# The consent service of Fernleaf Finance (fictional) in dpdp-sandbox: the notices, the consent
# API and the locked records (Release 4, Notice and consent).
#
# The service is defined once, in terraform/modules/consent-service, so the workload and
# sandbox copies are identical except for the two settings below.
#
# Apply with scripts/plan_check.sh, like every other stack. This stack creates an IAM role for
# the function, so it signs in as BreakGlassAdmin (backend.hcl and variables.tf).

module "consent_service" {
  source = "../../../modules/consent-service"

  # The clean-room copy must be removable after the test: governance mode, which an
  # administrator may bypass, and buckets and table that Terraform may delete.
  lock_mode     = "GOVERNANCE"
  allow_removal = true
}
