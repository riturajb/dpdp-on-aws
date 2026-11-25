# Which Terraform and provider versions this stack accepts, and where its state is kept.
#
# State: an S3 bucket in the same account (created once by scripts/bootstrap_state_bucket.sh).
# The bucket name and sign-in profile come from backend.hcl, which is not committed because it
# contains the account number. use_lockfile stops two runs changing the same stack at once.
# The AWS provider is pinned to the 5.x series. archive packs the function's code on the laptop.

terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.100"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
  backend "s3" {
    key          = "workload/consent.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
