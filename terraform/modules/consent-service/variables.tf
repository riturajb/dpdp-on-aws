# Inputs for the consent service. The workload and sandbox stacks set them differently.

variable "lock_mode" {
  description = "Object Lock mode for notices and consent records: COMPLIANCE (workload) or GOVERNANCE (sandbox)."
  type        = string
  validation {
    condition     = contains(["GOVERNANCE", "COMPLIANCE"], var.lock_mode)
    error_message = "lock_mode must be GOVERNANCE or COMPLIANCE."
  }
}

variable "lock_days" {
  description = "Days each notice and consent record stays locked after it is written."
  type        = number
  default     = 365
}

variable "allow_removal" {
  description = "true only in the sandbox: the buckets can be emptied and the table deleted after the clean-room test."
  type        = bool
  default     = false
}
