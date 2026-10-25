# Fernleaf Finance (fictional), the model lending and wallet company: where its personal data is
# stored. All data is synthetic. Folder and resource names stay generic, so the name can change
# without touching any infrastructure.
#
# Four DynamoDB tables and two S3 buckets. Every store carries two tags, which the register
# check (tools/register_check.py --live) and test T2 rely on:
#   DataClass     = "personal"   this store holds personal data
#   RegisterStore = <id>         the store's id in register/personal-data-register.yaml
# A store with personal data and no matching register entry is reported under Section 8(1).
#
# When adding a store: add it here with both tags, add it to the register, then run the check.

# The account id makes the bucket names unique across AWS.
data "aws_caller_identity" "current" {}

# Every table is keyed by customer_id, so all records of one customer can be read in one query
# (used by the customer summary, and later by access, correction and erasure requests).
locals {
  suffix = data.aws_caller_identity.current.account_id

  tables = {
    "customers-db" = { name = "dpdp-customers", hash_key = "customer_id", range_key = null }
    "loans-db"     = { name = "dpdp-loans", hash_key = "customer_id", range_key = "loan_id" }
    "wallet-db"    = { name = "dpdp-wallet-transactions", hash_key = "customer_id", range_key = "txn_id" }
    "tickets-db"   = { name = "dpdp-support-tickets", hash_key = "customer_id", range_key = "ticket_id" }
  }

  buckets = {
    "bureau-reports" = "dpdp-bureau-reports-${local.suffix}"
    "app-events"     = "dpdp-app-events-${local.suffix}"
  }
}

# The four tables. On-demand billing costs nothing while idle.
resource "aws_dynamodb_table" "store" {
  for_each = local.tables

  name         = each.value.name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = each.value.hash_key
  range_key    = each.value.range_key

  attribute {
    name = each.value.hash_key
    type = "S"
  }

  # Only tables with a second key (one row per loan, transaction or ticket) declare it.
  dynamic "attribute" {
    for_each = each.value.range_key == null ? [] : [each.value.range_key]
    content {
      name = attribute.value
      type = "S"
    }
  }

  # Encryption at rest with an AWS owned key is always on for DynamoDB.
  tags = {
    DataClass     = "personal"
    RegisterStore = each.key
  }
}

# The two buckets: credit bureau reports (one file per customer) and app activity
# (one file of events per customer). force_destroy lets the sandbox copy be removed after the
# clean-room test; acceptable here because the data is synthetic.
resource "aws_s3_bucket" "store" {
  for_each      = local.buckets
  bucket        = each.value
  force_destroy = true

  tags = {
    DataClass     = "personal"
    RegisterStore = each.key
  }
}

# Encryption at rest with keys managed by S3 (Rule 6(1)(a)).
resource "aws_s3_bucket_server_side_encryption_configuration" "store" {
  for_each = aws_s3_bucket.store
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# The account owns every object; access control lists are switched off.
resource "aws_s3_bucket_ownership_controls" "store" {
  for_each = aws_s3_bucket.store
  bucket   = each.value.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# No public access.
resource "aws_s3_bucket_public_access_block" "store" {
  for_each                = aws_s3_bucket.store
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
