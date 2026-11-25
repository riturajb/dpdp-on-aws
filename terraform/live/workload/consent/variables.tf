# Inputs for this stack.

variable "aws_profile" {
  description = "AWS CLI profile used for this stack: BreakGlassAdmin, because it creates an IAM role."
  type        = string
  default     = "dpdp-workload-admin"
}
