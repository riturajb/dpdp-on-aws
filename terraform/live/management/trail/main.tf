# The organisation trail: one CloudTrail trail that records every management action
# (who changed what, when, from where) in every account of the organisation.
#
# Supports Rule 6(1)(c): visibility of access through logs. The logs go to the locked bucket in
# the log archive account, where they are kept for 365 days (Rule 6(1)(e)).
# Created in the management account because only it can create an organisation trail.
# The first copy of management events is free.

resource "aws_cloudtrail" "organization" {
  name                  = "dpdp-organization-trail"
  s3_bucket_name        = var.cloudtrail_bucket_name
  is_organization_trail = true
  # Records activity in every region, so an attempt to work outside Mumbai is also logged.
  is_multi_region_trail         = true
  include_global_service_events = true
  # Writes signed digest files every hour, so anyone can later prove a log file was not altered.
  enable_log_file_validation = true

  lifecycle {
    prevent_destroy = true
  }
}
