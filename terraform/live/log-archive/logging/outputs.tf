# Bucket names, needed by the trail stack (cloudtrail_bucket_name) and by config/local.env.

output "cloudtrail_bucket_name" {
  value = module.trail_bucket.name
}

output "evidence_live_bucket_name" {
  value = module.evidence_live.name
}

output "evidence_sandbox_bucket_name" {
  value = module.evidence_sandbox.name
}
