# The consent service of Fernleaf Finance (fictional): the notice, the consent API and the proof.
#
# What:        Two buckets with Object Lock (the published notices; the locked copy of every
#              consent record), one DynamoDB table (the consent ledger, an index of the records),
#              one Lambda function (services/consent) and one API Gateway HTTP API in front of it.
#              Every route of the API needs a request signed with AWS credentials (IAM
#              authorisation): there is no anonymous access from the internet.
# Why:         DPDP Act, Section 5(1) and Rule 3 (a notice with every request for consent),
#              Section 6(1) (consent checked before it is recorded), Section 6(10) (the company
#              must prove the notice and the consent). Rule 6(1)(b) (access control: signed
#              requests only, a function that can add records but never change or delete them),
#              Rule 6(1)(c) and (e) (an access log of every request, kept for one year), Rule
#              6(1)(d) (the ledger can be restored to any second of the last 35 days).
# Who runs it: The author or reader, as BreakGlassAdmin: this module creates an IAM role for the
#              function, which PlatformEngineer cannot do, by design (Release 4, Step 3).
# When:        Release 4 onwards.
# Changes AWS: Yes. Two buckets, one table, one function with its role, one HTTP API and two log
#              groups. All are charged by use; at this project's size, a few cents a month.
#
# Lock modes (variables lock_mode and lock_days), as for the evidence buckets of Release 1:
#   COMPLIANCE  (workload) nobody can change or delete a locked record before its retention date,
#               not even the root user. The bucket cannot be removed while it holds one.
#   GOVERNANCE  (sandbox) the same, except for someone with the special permission to bypass it,
#               so the clean-room copy can be removed after the test.
#
# The plan-check rules of Release 3 apply to every resource here: each bucket and the table say
# whether they hold personal data; the personal ones name their register entry and can be
# recovered; both buckets block public access; both log groups keep logs for a year; and every
# API route needs authorisation (a rule added in Release 4).

data "aws_caller_identity" "current" {}

locals {
  account  = data.aws_caller_identity.current.account_id
  name     = "dpdp-consent-api"
  table    = "dpdp-consent-ledger"
  log_days = 365

  # The notices hold no personal data: the same text is shown to everyone. The records do:
  # each names a customer by her internal customer number.
  buckets = {
    "notices" = {
      name = "dpdp-notices-${local.account}"
      tags = { DataClass = "none" }
    }
    "records" = {
      name = "dpdp-consent-records-${local.account}"
      tags = { DataClass = "personal", RegisterStore = "consent-records" }
    }
  }
}

# ---------------------------------------------------------------- the two locked buckets

# Object Lock can only be switched on when a bucket is created. force_destroy lets Terraform
# empty the sandbox copy (governance mode); in compliance mode no object can be removed early,
# whatever this setting says.
resource "aws_s3_bucket" "this" {
  for_each            = local.buckets
  bucket              = each.value.name
  object_lock_enabled = true
  force_destroy       = var.allow_removal
  tags                = each.value.tags
}

# Versioning is required by Object Lock. A new copy of an object becomes a new version; the
# earlier version stays, locked. Each ledger row names the exact version it relies on.
resource "aws_s3_bucket_versioning" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.bucket
  versioning_configuration {
    status = "Enabled"
  }
}

# Every new object is locked on arrival, for lock_days days, in lock_mode.
resource "aws_s3_bucket_object_lock_configuration" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.bucket
  rule {
    default_retention {
      mode = var.lock_mode
      days = var.lock_days
    }
  }
  depends_on = [aws_s3_bucket_versioning.this]
}

# Encryption at rest with keys managed by S3 (Rule 6(1)(a)).
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.bucket
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# The account owns every object; access control lists are switched off.
resource "aws_s3_bucket_ownership_controls" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.bucket
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# No public access, ever (Rule 6(1)(b)).
resource "aws_s3_bucket_public_access_block" "this" {
  for_each                = aws_s3_bucket.this
  bucket                  = each.value.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Requests without encryption in transit are refused (Rule 6(1)(a)).
resource "aws_s3_bucket_policy" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.bucket
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "EncryptedConnectionsOnly"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [each.value.arn, "${each.value.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.this]
}

# ---------------------------------------------------------------- the ledger

# One row per record, found by customer number, in time order. The ledger is the index; the
# locked copy in the records bucket is the proof. On-demand billing costs nothing while idle.
resource "aws_dynamodb_table" "ledger" {
  name         = local.table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "customer_id"
  range_key    = "record_key"

  attribute {
    name = "customer_id"
    type = "S"
  }

  attribute {
    name = "record_key"
    type = "S"
  }

  # Restore to any second of the last 35 days (Rule 6(1)(d)).
  point_in_time_recovery {
    enabled = true
  }

  # In the workload account the table cannot be deleted by accident.
  deletion_protection_enabled = !var.allow_removal

  tags = {
    DataClass     = "personal"
    RegisterStore = "consent-ledger"
  }
}

# ---------------------------------------------------------------- the function

# The code: the two files of services/consent, packed into a zip at plan time. Listing the
# files one by one keeps anything else (such as Python's cache folders) out of the package.
data "archive_file" "code" {
  type        = "zip"
  output_path = "${path.root}/.terraform/consent-service.zip"

  source {
    filename = "handler.py"
    content  = file("${path.module}/../../../services/consent/handler.py")
  }

  source {
    filename = "consent_rules.py"
    content  = file("${path.module}/../../../services/consent/consent_rules.py")
  }
}

# The function's own log, kept for a year (Rule 6(1)(e)). Created before the function, so that
# Lambda does not create it without a retention period.
resource "aws_cloudwatch_log_group" "function" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = local.log_days
}

# The role the function runs as.
resource "aws_iam_role" "function" {
  name        = local.name
  description = "Consent service (Release 4): reads notices, adds consent records"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Least privilege (Rule 6(1)(b)): read the notices; add a locked copy and a ledger row. The role
# has no permission to change or delete either, so the service itself can never alter a record.
resource "aws_iam_role_policy" "function" {
  name = "read-notices-add-records"
  role = aws_iam_role.function.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadNotices"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.this["notices"].arn}/notices/*"
      },
      {
        Sid      = "AddLockedRecords"
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.this["records"].arn}/*"
      },
      {
        Sid      = "AddLedgerRows"
        Effect   = "Allow"
        Action   = "dynamodb:PutItem"
        Resource = aws_dynamodb_table.ledger.arn
      },
      {
        Sid      = "WriteOwnLog"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.function.arn}:*"
      },
    ]
  })
}

resource "aws_lambda_function" "this" {
  function_name    = local.name
  description      = "Consent service (Release 4): notice, consent checks and records"
  role             = aws_iam_role.function.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.code.output_path
  source_code_hash = data.archive_file.code.output_base64sha256
  memory_size      = 256
  timeout          = 10

  environment {
    variables = {
      NOTICES_BUCKET = aws_s3_bucket.this["notices"].bucket
      RECORDS_BUCKET = aws_s3_bucket.this["records"].bucket
      LEDGER_TABLE   = aws_dynamodb_table.ledger.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.function, aws_iam_role_policy.function]
}

# ---------------------------------------------------------------- the API

# The API Gateway access log: one line per request, kept for a year (Rule 6(1)(c) and (e)). It
# records who called (the signed-in role and session), from where, which route, the result,
# and the request reference that the function copies into every record it makes. It holds no
# request body, so no customer data.
resource "aws_cloudwatch_log_group" "access" {
  name              = "/aws/apigateway/${local.name}"
  retention_in_days = local.log_days
}

resource "aws_apigatewayv2_api" "this" {
  name          = local.name
  description   = "Consent service of Fernleaf Finance (fictional), Release 4"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "function" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  payload_format_version = "2.0"
}

# Every route requires a request signed with AWS credentials (AWS_IAM). An unsigned request is
# refused by API Gateway before it reaches the function.
resource "aws_apigatewayv2_route" "this" {
  for_each           = toset(["GET /notice", "POST /consents", "POST /notice-deliveries"])
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = each.value
  authorization_type = "AWS_IAM"
  target             = "integrations/${aws_apigatewayv2_integration.function.id}"
}

# One stage, deployed automatically. Throttling limits how fast any caller can send requests,
# which also limits the damage a misused credential can do.
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access.arn
    format = jsonencode({
      requestId    = "$context.requestId"
      requestTime  = "$context.requestTime"
      routeKey     = "$context.routeKey"
      status       = "$context.status"
      caller       = "$context.identity.userArn"
      sourceIp     = "$context.identity.sourceIp"
      responseSize = "$context.responseLength"
      error        = "$context.integrationErrorMessage"
    })
  }
}

# API Gateway may call the function, for this API only.
resource "aws_lambda_permission" "api" {
  statement_id  = "AllowConsentApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
