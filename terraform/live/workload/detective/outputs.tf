# Names of the detective controls, shown after "terraform apply".

output "recorder_name" {
  description = "AWS Config configuration recorder"
  value       = module.detective_controls.recorder_name
}

output "rule_names" {
  description = "AWS Config rules, one per safeguard"
  value       = module.detective_controls.rule_names
}

output "history_bucket" {
  description = "Bucket that holds the recorded configuration history"
  value       = module.detective_controls.history_bucket
}
