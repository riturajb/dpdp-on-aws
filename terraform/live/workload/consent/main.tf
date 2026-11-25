# The consent service of Fernleaf Finance (fictional) in dpdp-workload: the notices, the consent
# API and the locked records (Release 4, Notice and consent).
#
# The service is defined once, in terraform/modules/consent-service, so the workload and
# sandbox copies are identical except for the two settings below.
#
# Apply with scripts/plan_check.sh, like every other stack. This stack creates an IAM role for
# the function, so it signs in as BreakGlassAdmin (backend.hcl and variables.tf).

module "consent_service" {
  source = "../../../modules/consent-service"

  # Nobody can change or delete a notice or a consent record for 365 days after it is written,
  # not even the root user (Section 6(10): proof that holds). The table cannot be deleted.
  lock_mode     = "COMPLIANCE"
  allow_removal = false
}
