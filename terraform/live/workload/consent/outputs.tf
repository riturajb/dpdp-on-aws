# Shown after "terraform apply". The tools find these names on their own; they are printed so
# that you can see what was created.

output "api_endpoint" {
  description = "Address of the consent API (signed requests only)"
  value       = module.consent_service.api_endpoint
}

output "notices_bucket" {
  description = "Locked bucket with the published notices"
  value       = module.consent_service.notices_bucket
}

output "records_bucket" {
  description = "Locked bucket with the copy of every consent record"
  value       = module.consent_service.records_bucket
}

output "ledger_table" {
  description = "Consent ledger"
  value       = module.consent_service.ledger_table
}
