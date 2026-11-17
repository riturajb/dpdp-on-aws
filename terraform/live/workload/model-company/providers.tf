# Sign-in and tags for every resource in this stack.
#
# profile: the AWS CLI profile from ~/.aws/config (see config/aws-config.example). In GitHub
# Actions (Release 3, the "plan" job) aws_profile is set to "" and the job's temporary role is
# used instead.
# default_tags: added to every resource, so costs and ownership can be traced. DataOrigin says
# the data is synthetic; stores holding personal data also get DataClass = "personal" in the module.

provider "aws" {
  region  = "ap-south-1"
  profile = var.aws_profile == "" ? null : var.aws_profile

  default_tags {
    tags = {
      Project     = "dpdp-in-practice"
      Release     = "1"
      Environment = var.environment
      DataOrigin  = "synthetic"
      ManagedBy   = "terraform"
    }
  }
}
