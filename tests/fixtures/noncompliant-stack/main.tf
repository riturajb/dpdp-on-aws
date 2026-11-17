# A deliberately non-compliant change, used by test T13 to show that the plan check stops it.
# It is only ever planned, never applied: scripts/plan_check.sh is run without --apply.
#
# Each resource breaks one rule in policies/rego/prevent.rego:
#   export bucket   no DataClass tag (s.8(1)) and no public access block (Rule 6(1)(b))
#   leads table     personal, but named in no register entry (s.8(1)), no point-in-time
#                   recovery (Rule 6(1)(d))
#   debug log group kept for 7 days (Rule 6(1)(e))

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "export" {
  bucket = "dpdp-unreviewed-export-${data.aws_caller_identity.current.account_id}"
}

resource "aws_dynamodb_table" "leads" {
  name         = "dpdp-campaign-leads"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lead_id"

  attribute {
    name = "lead_id"
    type = "S"
  }

  tags = {
    DataClass     = "personal"
    RegisterStore = "campaign-leads"
  }
}

resource "aws_cloudwatch_log_group" "debug" {
  name              = "/fernleaf/campaign-debug"
  retention_in_days = 7
}
