# Account baseline for dpdp-sandbox.
#
# Applies the settings every member account gets before anything else is deployed:
# no public S3 buckets, encrypted disks by default, and a check for resources shared
# outside the account. The settings themselves are in terraform/modules/account-baseline.

module "baseline" {
  source = "../../../modules/account-baseline"
}
