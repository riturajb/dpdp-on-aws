# Which Terraform and AWS provider versions this stack accepts, and where its state is kept.
#
# State: an S3 bucket in the same account (created once by scripts/bootstrap_state_bucket.sh).
# The bucket name and sign-in profile come from backend.hcl, which is not committed because it
# contains the account number. use_lockfile stops two runs changing the same stack at once.
# The provider is pinned to the 5.x series; move to a new major version only as a planned change.

terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.100"
    }
  }
  backend "s3" {
    key          = "workload/model-company.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
