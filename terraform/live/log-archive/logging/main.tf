# Logs and evidence, in the log archive account: three locked buckets.
#
#   dpdp-cloudtrail-logs-<id>     the organisation trail; governance mode, 365 days (Rule 6(1)(e))
#   dpdp-evidence-live-<id>       test results from the workload account; compliance mode
#   dpdp-evidence-sandbox-<id>    test results from clean-room runs; governance mode, 1 day
#
# Why a separate account: the people who run the system cannot alter the evidence about it.
# The workload and sandbox accounts can only ADD files, each to its own folder.
#
# Apply this stack BEFORE attaching the "buckets" guardrail to the Security unit (setup guide,
# Part 9, stage C). After that, these buckets cannot be deleted or their settings weakened.

# This account's id, used to make the bucket names unique.
data "aws_caller_identity" "current" {}

locals {
  id             = data.aws_caller_identity.current.account_id
  trail_bucket   = "dpdp-cloudtrail-logs-${local.id}"
  live_bucket    = "dpdp-evidence-live-${local.id}"
  sandbox_bucket = "dpdp-evidence-sandbox-${local.id}"
  # Only the organisation trail may write to the log bucket (checked through aws:SourceArn).
  trail_arn = "arn:aws:cloudtrail:ap-south-1:${var.management_account_id}:trail/dpdp-organization-trail"
}

# Log bucket policy: the standard permissions CloudTrail needs for an organisation trail.
# Logs arrive under AWSLogs/<management id>/ and AWSLogs/<organisation id>/.
data "aws_iam_policy_document" "trail" {
  statement {
    sid       = "CloudTrailAclCheck"
    actions   = ["s3:GetBucketAcl"]
    resources = ["arn:aws:s3:::${local.trail_bucket}"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }

  statement {
    sid     = "CloudTrailWrite"
    actions = ["s3:PutObject"]
    resources = [
      "arn:aws:s3:::${local.trail_bucket}/AWSLogs/${var.management_account_id}/*",
      "arn:aws:s3:::${local.trail_bucket}/AWSLogs/${var.organization_id}/*",
    ]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = ["arn:aws:s3:::${local.trail_bucket}", "arn:aws:s3:::${local.trail_bucket}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# Live evidence: only the workload account may add files, and only under dpdp-workload/.
# Read access for auditors comes from their Auditor role in this account.
data "aws_iam_policy_document" "evidence_live" {
  statement {
    sid       = "WorkloadAddsEvidenceToItsOwnFolder"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${local.live_bucket}/dpdp-workload/*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.workload_account_id}:root"]
    }
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = ["arn:aws:s3:::${local.live_bucket}", "arn:aws:s3:::${local.live_bucket}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# Sandbox evidence: only the sandbox account may add files, and only under dpdp-sandbox/.
data "aws_iam_policy_document" "evidence_sandbox" {
  statement {
    sid       = "SandboxAddsEvidenceToItsOwnFolder"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${local.sandbox_bucket}/dpdp-sandbox/*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.sandbox_account_id}:root"]
    }
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = ["arn:aws:s3:::${local.sandbox_bucket}", "arn:aws:s3:::${local.sandbox_bucket}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# Each policy above also refuses any request not sent over an encrypted connection.

module "trail_bucket" {
  source      = "../../../modules/locked-bucket"
  name        = local.trail_bucket
  lock_mode   = "GOVERNANCE"
  lock_days   = 365
  policy_json = data.aws_iam_policy_document.trail.json
}

# Compliance mode: nobody can delete a live evidence record for 30 days, not even the root user.
module "evidence_live" {
  source      = "../../../modules/locked-bucket"
  name        = local.live_bucket
  lock_mode   = "COMPLIANCE"
  lock_days   = var.live_evidence_retention_days
  policy_json = data.aws_iam_policy_document.evidence_live.json
}

# Governance mode, one day: clean-room results expire quickly and never mix with live evidence.
module "evidence_sandbox" {
  source      = "../../../modules/locked-bucket"
  name        = local.sandbox_bucket
  lock_mode   = "GOVERNANCE"
  lock_days   = 1
  policy_json = data.aws_iam_policy_document.evidence_sandbox.json
}
