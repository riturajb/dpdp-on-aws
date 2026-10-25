# Values other stacks need: the bucket name (for the trail and the tests) and its ARN.

output "name" {
  value = aws_s3_bucket.this.id
}

output "arn" {
  value = aws_s3_bucket.this.arn
}
