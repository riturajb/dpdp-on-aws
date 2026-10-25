# Inputs for this stack. Values that identify you or your accounts go in terraform.tfvars,
# which Git ignores; terraform.tfvars.example shows the expected format.

variable "aws_profile" {
  description = "AWS CLI profile used for this stack."
  type        = string
  default     = "dpdp-workload-eng"
}

variable "environment" {
  description = "Value of the Environment tag."
  type        = string
  default     = "workload"
}
