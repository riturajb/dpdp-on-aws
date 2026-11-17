# Sign-in and tags for every resource in this stack.
#
# profile: the AWS CLI profile from ~/.aws/config (see config/aws-config.example).
# default_tags: added to every resource, so costs and ownership can be traced. DataOrigin says
# the data is synthetic.

provider "aws" {
  region  = "ap-south-1"
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = "dpdp-in-practice"
      Release     = "3"
      Environment = var.environment
      DataOrigin  = "synthetic"
      ManagedBy   = "terraform"
    }
  }
}
