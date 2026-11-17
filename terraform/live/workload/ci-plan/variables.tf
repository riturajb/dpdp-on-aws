# Inputs for this stack. They go in terraform.tfvars, which Git ignores; the Release 3 guide
# writes it for you from the repository's address and GitHub's public API.

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

variable "github_owner_id" {
  description = "Numeric id of the repository owner on GitHub (owner.id in the GitHub API)."
  type        = string

  validation {
    condition     = can(regex("^[0-9]+$", var.github_owner_id))
    error_message = "Use the numeric owner id from https://api.github.com/repos/<owner>/<name>."
  }
}

variable "github_repository_id" {
  description = "Numeric id of the repository on GitHub (id in the GitHub API)."
  type        = string

  validation {
    condition     = can(regex("^[0-9]+$", var.github_repository_id))
    error_message = "Use the numeric repository id from https://api.github.com/repos/<owner>/<name>."
  }
}
