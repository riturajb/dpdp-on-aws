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

variable "organization_id" {
  description = "Id of the AWS Organization created in the console (o-xxxxxxxxxx). Used once, to import it."
  type        = string
}

variable "account_emails" {
  description = "Email address for each member account. Kept in terraform.tfvars, which Git ignores."
  type        = map(string)
}

variable "scp_attachments" {
  description = "Which guardrail policies are attached to which organisational unit. Changed one stage at a time."
  type        = map(list(string))
  default = {
    sandbox   = []
    workloads = []
    security  = []
  }
  validation {
    condition = alltrue(flatten([
      for ou, names in var.scp_attachments : [
        for n in names : contains(["region", "baseline", "buckets", "cost"], n)
      ]
    ]))
    error_message = "Policy names must be region, baseline, buckets or cost."
  }
}
