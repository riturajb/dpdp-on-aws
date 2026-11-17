# Names used by tools/drift_drill.py and the tests.

output "recorder_name" {
  description = "AWS Config configuration recorder"
  value       = aws_config_configuration_recorder.this.name
}

output "rule_names" {
  description = "AWS Config rules, one per safeguard"
  value       = sort(keys(aws_config_config_rule.this))
}

output "history_bucket" {
  description = "Bucket that holds the recorded configuration history"
  value       = aws_s3_bucket.history.bucket
}
