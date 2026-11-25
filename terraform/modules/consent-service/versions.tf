# Versions this module is written for. The calling stack decides the exact provider versions.
# archive packs the function's code into a zip file on the laptop; it makes no AWS calls.

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
}
