# Inputs for this stack. github_repository goes in terraform.tfvars, which Git ignores;
# the Release 3 guide writes it for you from the repository's own address.

variable "aws_profile" {
  description = "AWS CLI profile used for this stack."
  type        = string
  default     = "dpdp-workload-admin"
}

variable "github_repository" {
  description = "The GitHub repository allowed to use the plan role, as owner/name."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$", var.github_repository))
    error_message = "Use the form owner/name, for example riturajb/dpdp-on-aws."
  }
}
