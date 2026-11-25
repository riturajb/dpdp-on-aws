# Names the guides, tools and tests use. The tools find them on their own from the account id
# and the API's name, so nothing here has to be copied into config/local.env.

output "api_endpoint" {
  description = "Address of the consent API. Every request must be signed (IAM authorisation)."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "notices_bucket" {
  description = "Locked bucket with every published notice version"
  value       = aws_s3_bucket.this["notices"].bucket
}

output "records_bucket" {
  description = "Locked bucket with the copy of every consent record"
  value       = aws_s3_bucket.this["records"].bucket
}

output "ledger_table" {
  description = "DynamoDB table with one row per record"
  value       = aws_dynamodb_table.ledger.name
}
