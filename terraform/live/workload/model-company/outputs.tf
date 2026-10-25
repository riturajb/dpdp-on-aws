# Names of the model company's stores in the workload account. Shown after "terraform apply";
# they let you check the real names against the personal data register.

output "table_names" {
  description = "DynamoDB tables, by store name"
  value       = module.model_company.table_names
}

output "bucket_names" {
  description = "S3 buckets, by store name"
  value       = module.model_company.bucket_names
}
