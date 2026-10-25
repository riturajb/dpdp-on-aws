# The trail's ARN, used by test T5f (config/local.env, DPDP_TRAIL_ARN).

output "trail_arn" {
  value = aws_cloudtrail.organization.arn
}
