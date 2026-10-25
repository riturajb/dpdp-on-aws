# Inputs for this stack. Values that identify you or your accounts go in terraform.tfvars,
# which Git ignores; terraform.tfvars.example shows the expected format.

variable "aws_profile" {
  description = "AWS CLI profile used for this stack."
  type        = string
  default     = "dpdp-logarchive-admin"
}

variable "environment" {
  description = "Value of the Environment tag."
  type        = string
  default     = "log-archive"
}

variable "management_account_id" {
  description = "Account id of dpdp-management, where the organisation trail is created."
  type        = string
}

variable "organization_id" {
  description = "Id of the AWS Organization (o-xxxxxxxxxx)."
  type        = string
}

variable "workload_account_id" {
  description = "Account id of dpdp-workload."
  type        = string
}

variable "sandbox_account_id" {
  description = "Account id of dpdp-sandbox."
  type        = string
}

variable "live_evidence_retention_days" {
  description = "Compliance-mode retention for live evidence. Can be extended later, never shortened."
  type        = number
  default     = 30
}
