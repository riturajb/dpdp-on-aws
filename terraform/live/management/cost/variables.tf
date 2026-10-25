# Inputs for this stack. Values that identify you or your accounts go in terraform.tfvars,
# which Git ignores; terraform.tfvars.example shows the expected format.

variable "aws_profile" {
  description = "AWS CLI profile used for this stack."
  type        = string
  default     = "dpdp-mgmt-admin"
}

variable "environment" {
  description = "Value of the Environment tag."
  type        = string
  default     = "management"
}

variable "alert_email" {
  description = "Email address for budget alerts."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly budget for the whole organisation, in US dollars. 18 is about INR 1,500."
  type        = number
  default     = 18
}
