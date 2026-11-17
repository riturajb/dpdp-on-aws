# Input for the plan; test T13 sets it from config/local.env.

variable "aws_profile" {
  description = "AWS CLI profile used to make the plan."
  type        = string
  default     = "dpdp-workload-eng"
}
