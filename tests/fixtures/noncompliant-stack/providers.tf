# Sign-in for the plan. Test T13 sets TF_VAR_aws_profile to the target account's profile.

provider "aws" {
  region  = "ap-south-1"
  profile = var.aws_profile
}
