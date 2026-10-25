# Fernleaf Finance (fictional), the model company: its data stores in dpdp-workload, used for the weekly demonstrations.
#
# The stores themselves are defined once, in terraform/modules/model-company, so the
# workload and sandbox copies are always identical.

module "model_company" {
  source = "../../../modules/model-company"
}
