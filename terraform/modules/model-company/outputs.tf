# Real names of the stores in this account, for checking and for the guides.

output "table_names" {
  description = "DynamoDB tables, by store name"
  value       = { for k, t in aws_dynamodb_table.store : k => t.name }
}

output "bucket_names" {
  description = "S3 buckets, by store name"
  value       = { for k, b in aws_s3_bucket.store : k => b.id }
}
