# Detective controls: AWS Config records the data stores and log groups of one account and
# checks them, continuously, against the same rules that scripts/plan_check.sh applies before a
# change. A change made outside the process (in the console, or by a script) is flagged within
# minutes as NON_COMPLIANT, with the time and the resource.
#
# What:        A configuration recorder for S3 buckets, DynamoDB tables and CloudWatch log groups,
#              a bucket for its history, and six AWS managed rules.
# Why:         Prevention covers changes made through Terraform. Rule 6(1)(g) asks for measures
#              that ensure the safeguards are actually observed; this shows when the
#              infrastructure around personal data drifts from them, whoever made the change.
# Who runs it: Applied by the engineer (PlatformEngineer) with scripts/plan_check.sh --apply.
#              Once the "buckets" guardrail is updated (Release 3 guide), nobody in the workload
#              account can stop or delete the recorder or the rules.
# When:        Release 3, Step 4 (workload); in the sandbox only for the clean-room test.
# Reads:       Nothing.   Writes: AWS resources only.
# Changes AWS: Yes. Recorder, delivery channel, bucket and six rules. The Config
#              service-linked role is created beforehand with the AWS CLI. Cost: a few cents a
#              month for this account (charged per item recorded and per rule evaluation).

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  bucket     = "dpdp-config-history-${local.account_id}"
}

# The role AWS Config uses to read resource settings. AWS creates its permissions. It is
# created once per account with the AWS CLI (Release 3 guide, Step 4), not here: Terraform
# would also tag it, and PlatformEngineer may create service-linked roles but not tag roles.
data "aws_iam_role" "config" {
  name = "AWSServiceRoleForConfig"
}

# ---------------------------------------------------------------- history bucket

# Config writes snapshots of the recorded settings here. It holds no personal data
# (DataClass = none), and meets the same bucket rules as every other bucket.
resource "aws_s3_bucket" "history" {
  bucket        = local.bucket
  force_destroy = true

  tags = {
    DataClass = "none"
  }
}

resource "aws_s3_bucket_public_access_block" "history" {
  bucket                  = aws_s3_bucket.history.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "history" {
  bucket = aws_s3_bucket.history.bucket
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "history" {
  bucket = aws_s3_bucket.history.bucket
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Only AWS Config, acting for this account, may write here.
resource "aws_s3_bucket_policy" "history" {
  bucket = aws_s3_bucket.history.bucket
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ConfigReadsBucketSettings"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = ["s3:GetBucketAcl", "s3:ListBucket"]
        Resource  = "arn:${data.aws_partition.current.partition}:s3:::${local.bucket}"
        Condition = { StringEquals = { "aws:SourceAccount" = local.account_id } }
      },
      {
        Sid       = "ConfigWritesSnapshots"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "arn:${data.aws_partition.current.partition}:s3:::${local.bucket}/AWSLogs/${local.account_id}/Config/*"
        Condition = { StringEquals = { "aws:SourceAccount" = local.account_id, "s3:x-amz-acl" = "bucket-owner-full-control" } }
      },
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.history]
}

# ---------------------------------------------------------------- recorder

# Records only the three resource types the rules check, which keeps the cost to cents.
resource "aws_config_configuration_recorder" "this" {
  name     = "dpdp-recorder"
  role_arn = data.aws_iam_role.config.arn

  recording_group {
    all_supported  = false
    resource_types = ["AWS::S3::Bucket", "AWS::DynamoDB::Table", "AWS::Logs::LogGroup"]
  }
}

resource "aws_config_delivery_channel" "this" {
  name           = "dpdp-delivery"
  s3_bucket_name = aws_s3_bucket.history.bucket
  depends_on     = [aws_config_configuration_recorder.this, aws_s3_bucket_policy.history]
}

resource "aws_config_configuration_recorder_status" "this" {
  name       = aws_config_configuration_recorder.this.name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.this]
}

# ---------------------------------------------------------------- rules

# The same rules as policies/rego/prevent.rego, as AWS managed rules. The rule names are used
# by tools/drift_drill.py and tests T14 and T15.
locals {
  personal_scope = { tag_key = "DataClass", tag_value = "personal" }

  rules = {
    # Section 8(1): every bucket and table says whether it holds personal data.
    "dpdp-store-has-dataclass" = {
      source   = "REQUIRED_TAGS"
      params   = jsonencode({ tag1Key = "DataClass" })
      types    = ["AWS::S3::Bucket", "AWS::DynamoDB::Table"]
      tag      = null
      periodic = false
    }
    # Section 8(1): a store with personal data is linked to the register.
    "dpdp-personal-store-registered" = {
      source   = "REQUIRED_TAGS"
      params   = jsonencode({ tag1Key = "RegisterStore" })
      types    = null
      tag      = local.personal_scope
      periodic = false
    }
    # Rule 6(1)(b): no public buckets.
    "dpdp-bucket-not-public" = {
      source   = "S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED"
      params   = null
      types    = ["AWS::S3::Bucket"]
      tag      = null
      periodic = false
    }
    # Rule 6(1)(d): personal buckets keep earlier versions.
    "dpdp-personal-bucket-versioned" = {
      source   = "S3_BUCKET_VERSIONING_ENABLED"
      params   = null
      types    = null
      tag      = local.personal_scope
      periodic = false
    }
    # Rule 6(1)(d): personal tables can be restored to a point in time.
    "dpdp-personal-table-recoverable" = {
      source   = "DYNAMODB_PITR_ENABLED"
      params   = null
      types    = null
      tag      = local.personal_scope
      periodic = false
    }
    # Rule 6(1)(e): log groups are kept for at least one year. AWS runs this rule periodically;
    # tools/drift_drill.py asks for an immediate evaluation.
    "dpdp-logs-kept-one-year" = {
      source   = "CW_LOGGROUP_RETENTION_PERIOD_CHECK"
      params   = jsonencode({ MinRetentionTime = "365" })
      types    = null
      tag      = null
      periodic = true
    }
  }
}

resource "aws_config_config_rule" "this" {
  for_each = local.rules

  name                        = each.key
  input_parameters            = each.value.params
  maximum_execution_frequency = each.value.periodic ? "TwentyFour_Hours" : null

  source {
    owner             = "AWS"
    source_identifier = each.value.source
  }

  dynamic "scope" {
    for_each = each.value.types != null ? [1] : []
    content {
      compliance_resource_types = each.value.types
    }
  }

  dynamic "scope" {
    for_each = each.value.tag != null ? [1] : []
    content {
      tag_key   = each.value.tag.tag_key
      tag_value = each.value.tag.tag_value
    }
  }

  depends_on = [aws_config_configuration_recorder.this]
}
