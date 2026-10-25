#!/usr/bin/env bash
# Creates the S3 bucket that holds Terraform's state for one AWS account. Run once per account,
# before the first "terraform init" of any stack in that account.
#
#   scripts/bootstrap_state_bucket.sh dpdp-mgmt-admin
#
# Terraform cannot create the bucket it stores its own state in, so this one step uses the AWS CLI.
# The bucket is versioned (earlier states can be recovered), encrypted, and closed to the public.
# Safe to run again: if the bucket exists, it only prints the backend.hcl lines.
set -euo pipefail
PROFILE="${1:?usage: $0 <aws-profile>}"
REGION="ap-south-1"
# The account id makes the bucket name unique.
ACCOUNT_ID=$(aws sts get-caller-identity --profile "$PROFILE" --query Account --output text)
BUCKET="dpdp-tfstate-${ACCOUNT_ID}"

if aws s3api head-bucket --bucket "$BUCKET" --profile "$PROFILE" 2>/dev/null; then
  echo "State bucket already exists: $BUCKET"
else
  # Create the bucket in Mumbai, then switch on versioning, encryption and the public access block.
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION" --profile "$PROFILE" >/dev/null
  aws s3api put-bucket-versioning --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled --profile "$PROFILE"
  aws s3api put-bucket-encryption --bucket "$BUCKET" --profile "$PROFILE" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  aws s3api put-public-access-block --bucket "$BUCKET" --profile "$PROFILE" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-tagging --bucket "$BUCKET" --profile "$PROFILE" \
    --tagging 'TagSet=[{Key=Project,Value=dpdp-in-practice},{Key=ManagedBy,Value=bootstrap-script}]'
  echo "Created state bucket: $BUCKET"
fi
# These two lines go into backend.hcl in each stack folder of this account (never committed).
echo
echo "Put these two lines in backend.hcl for the stacks of this account:"
echo "bucket  = \"$BUCKET\""
echo "profile = \"$PROFILE\""
