# Inputs for a locked bucket.

variable "name" {
  description = "Bucket name. Must be unique across all of AWS, so the account id is part of it."
  type        = string
}

variable "lock_mode" {
  description = "GOVERNANCE or COMPLIANCE. Compliance mode cannot be shortened or removed by anyone, including the root user."
  type        = string
  validation {
    condition     = contains(["GOVERNANCE", "COMPLIANCE"], var.lock_mode)
    error_message = "lock_mode must be GOVERNANCE or COMPLIANCE."
  }
}

variable "lock_days" {
  description = "Default retention in days for every new object. In compliance mode, start short: it can be extended later but never reduced."
  type        = number
}

variable "policy_json" {
  description = "Bucket policy document, built by the calling stack."
  type        = string
}
