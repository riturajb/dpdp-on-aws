# Detective controls for dpdp-workload: AWS Config records the data stores and log groups and
# checks them continuously against the Release 3 rules.
#
# The controls are defined once, in terraform/modules/detective-controls, so the workload and
# sandbox copies are always identical. Apply with scripts/plan_check.sh, like every other stack.

module "detective_controls" {
  source = "../../../modules/detective-controls"
}
