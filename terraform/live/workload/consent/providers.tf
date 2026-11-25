# Sign-in and tags for every resource in this stack.
#
# profile: BreakGlassAdmin in dpdp-workload (dpdp-workload-admin), because the stack creates an
# IAM role, which PlatformEngineer cannot do. In GitHub Actions (the "plan" job of Release 3)
# aws_profile is set to "" and the job's read-only role is used instead.
# default_tags: added to every resource, so costs and ownership can be traced.

provider "aws" {
  region  = "ap-south-1"
  profile = var.aws_profile == "" ? null : var.aws_profile

  default_tags {
    tags = {
      Project     = "dpdp-in-practice"
      Release     = "4"
      Environment = "workload"
      DataOrigin  = "synthetic"
      ManagedBy   = "terraform"
    }
  }
}
