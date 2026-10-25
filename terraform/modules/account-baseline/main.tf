# Account baseline: three settings every member account gets before anything else is deployed.
#
# They are account-wide switches, so they also protect resources created later by hand.
# Supports Rule 6(1)(a) (data secured at rest) and Rule 6(1)(b) (control of access).

# Block public access to every S3 bucket in the account, including buckets created in future.
resource "aws_s3_account_public_access_block" "this" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Encrypt every new disk (EBS volume) in this region automatically.
resource "aws_ebs_encryption_by_default" "this" {
  enabled = true
}

# IAM Access Analyzer reports any resource that can be reached from outside the account,
# such as a bucket or role shared with another account. The account-level analyzer is free.
resource "aws_accessanalyzer_analyzer" "this" {
  analyzer_name = "dpdp-account-analyzer"
  type          = "ACCOUNT"
}
