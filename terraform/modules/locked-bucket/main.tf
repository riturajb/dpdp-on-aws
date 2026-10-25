# Locked bucket: an S3 bucket whose objects cannot be deleted or changed before a retention date.
#
# Used three times in the log archive account: for the CloudTrail logs and for the two
# evidence buckets. It supports Rule 6(1)(c) and 6(1)(e): access logs must exist, and must be
# kept for at least one year without anyone being able to erase them.
#
# Two lock modes (variable lock_mode):
#   GOVERNANCE  objects cannot be deleted early, except by someone with special permission,
#               which the "buckets" guardrail denies to everyone in the member accounts.
#   COMPLIANCE  nobody can delete objects early, not even the root user. Cannot be shortened later.
#
# Once the "buckets" guardrail is attached (setup guide, Part 9), this bucket's settings can no
# longer be changed from the member accounts. Plan any change before that, or follow the
# documented procedure to detach the guardrail temporarily.

# The bucket. Object Lock can only be switched on when a bucket is created.
# prevent_destroy makes Terraform refuse any plan that would delete it.
resource "aws_s3_bucket" "this" {
  bucket              = var.name
  object_lock_enabled = true

  lifecycle {
    prevent_destroy = true
  }
}

# Versioning is required by Object Lock: every change creates a new version instead of
# overwriting, so earlier versions remain available.
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Default retention applied to every new object: the mode and number of days set by the caller.
resource "aws_s3_bucket_object_lock_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    default_retention {
      mode = var.lock_mode
      days = var.lock_days
    }
  }

  depends_on = [aws_s3_bucket_versioning.this]
}

# Encryption at rest with keys managed by S3 (no extra cost). CloudTrail can write to it.
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# The bucket owner owns every object, including those written by other accounts.
# This also switches off access control lists, so access is decided only by policies.
resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# No public access, ever.
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Who may write to the bucket. The policy text is built by the calling stack, because it
# depends on which accounts and services write here.
resource "aws_s3_bucket_policy" "this" {
  bucket     = aws_s3_bucket.this.id
  policy     = var.policy_json
  depends_on = [aws_s3_bucket_public_access_block.this]
}
