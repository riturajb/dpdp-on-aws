# Sign-in and tags for every resource in this stack.
#
# profile: BreakGlassAdmin in dpdp-workload. PlatformEngineer cannot create IAM roles, by design.

provider "aws" {
  region  = "ap-south-1"
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = "dpdp-in-practice"
      Release     = "3"
      Environment = "workload"
      DataOrigin  = "synthetic"
      ManagedBy   = "terraform"
    }
  }
}
