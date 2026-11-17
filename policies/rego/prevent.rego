# Release 3, Prevent: the rules every infrastructure change must pass before it is applied.
#
# What:        Reads a Terraform plan (terraform show -json) and denies any change that would
#              leave a data store, a bucket or a log group outside the rules below.
# Why:         The DPDP Act and Rules require the safeguards to be in place, not repaired later.
#              Checking the plan stops a non-compliant change before it reaches AWS.
# Who runs it: scripts/plan_check.sh on the laptop, before every apply, and GitHub Actions on
#              every pull request (the "plan" job). Both call conftest, which runs these rules.
# When:        Release 3 onwards, for every stack.
# Reads:       The plan (input) and the personal data register (data.stores).
# Writes:      Nothing. Each denial is a message that names the rule and the resource.
# Changes AWS: No.
#
# Each message starts with the provision it serves, so a blocked change explains itself:
#   [s.8(1)]       every data store says whether it holds personal data, and personal stores
#                  are in the register
#   [R.6(1)(b)]    no bucket can be made public
#   [R.6(1)(d)]    personal stores can be recovered: versioning on buckets, point-in-time
#                  recovery on tables
#   [R.6(1)(e)]    log groups are kept for at least one year
#   [Mumbai only]  every stack runs in ap-south-1 (a design choice of this build; see the README)
#
# Encryption at rest is not checked here: S3 has encrypted every new object by default since
# January 2023, and DynamoDB tables are always encrypted. Release 3 guide, "What it does not do".

package main

import rego.v1

store_types := {"aws_s3_bucket", "aws_dynamodb_table"}

# Every resource the plan will leave in place: created, updated or unchanged. Resources being
# deleted are not checked; data sources are not resources.
resources contains r if {
	some r in input.resource_changes
	r.mode == "managed"
	r.change.actions != ["delete"]
}

after(r) := a if {
	a := r.change.after
	is_object(a)
} else := {}

# Tags as they will be: the resource's own tags merged over the provider's default tags.
tags(r) := object.union(tag_map(after(r), "tags_all"), tag_map(after(r), "tags"))

tag_map(a, key) := m if {
	m := a[key]
	is_object(m)
} else := {}

registered(id) if {
	some s in data.stores
	s.id == id
}

personal(r) if tags(r).DataClass == "personal"

# ---------------------------------------------------------------- Section 8(1)

deny contains msg if {
	some r in resources
	r.type in store_types
	not tags(r).DataClass
	msg := sprintf("[s.8(1)] %s has no DataClass tag. Every data store must say whether it holds personal data (personal or none).", [r.address])
}

deny contains msg if {
	some r in resources
	r.type in store_types
	personal(r)
	not tags(r).RegisterStore
	msg := sprintf("[s.8(1)] %s holds personal data but has no RegisterStore tag linking it to the register.", [r.address])
}

deny contains msg if {
	some r in resources
	r.type in store_types
	personal(r)
	id := tags(r).RegisterStore
	not registered(id)
	msg := sprintf("[s.8(1)] %s names RegisterStore '%s', which is not in register/personal-data-register.yaml.", [r.address, id])
}

# ---------------------------------------------------------------- Rule 6(1)(b)

# Every bucket name must be known at plan time, so that its settings can be matched to it.
deny contains msg if {
	some r in resources
	r.type == "aws_s3_bucket"
	not is_string(object.get(after(r), "bucket", null))
	msg := sprintf("[R.6(1)(b)] %s has no fixed name in the plan, so its access settings cannot be checked. Set the bucket name explicitly.", [r.address])
}

deny contains msg if {
	some r in resources
	r.type == "aws_s3_bucket"
	name := after(r).bucket
	is_string(name)
	not public_access_blocked(name)
	msg := sprintf("[R.6(1)(b)] %s (%s) has no public access block with all four settings on.", [r.address, name])
}

public_access_blocked(name) if {
	some p in resources
	p.type == "aws_s3_bucket_public_access_block"
	a := after(p)
	a.bucket == name
	a.block_public_acls == true
	a.block_public_policy == true
	a.ignore_public_acls == true
	a.restrict_public_buckets == true
}

# ---------------------------------------------------------------- Rule 6(1)(d)

deny contains msg if {
	some r in resources
	r.type == "aws_s3_bucket"
	personal(r)
	name := after(r).bucket
	is_string(name)
	not versioning_enabled(name)
	msg := sprintf("[R.6(1)(d)] %s (%s) holds personal data and has no versioning, so deleted or overwritten data cannot be recovered.", [r.address, name])
}

versioning_enabled(name) if {
	some v in resources
	v.type == "aws_s3_bucket_versioning"
	a := after(v)
	a.bucket == name
	some c in a.versioning_configuration
	c.status == "Enabled"
}

deny contains msg if {
	some r in resources
	r.type == "aws_dynamodb_table"
	personal(r)
	not pitr_enabled(r)
	msg := sprintf("[R.6(1)(d)] %s holds personal data and has no point-in-time recovery.", [r.address])
}

pitr_enabled(r) if {
	some p in after(r).point_in_time_recovery
	p.enabled == true
}

# ---------------------------------------------------------------- Rule 6(1)(e)

# retention_in_days 0 means "never expire", which keeps logs for at least a year.
deny contains msg if {
	some r in resources
	r.type == "aws_cloudwatch_log_group"
	days := object.get(after(r), "retention_in_days", 0)
	days != null
	days > 0
	days < 365
	msg := sprintf("[R.6(1)(e)] %s keeps logs for %d days. Rule 6(1)(e) requires at least one year (365 days).", [r.address, days])
}

# ---------------------------------------------------------------- Mumbai only

deny contains msg if {
	some key, p in input.configuration.provider_config
	p.name == "aws"
	region := p.expressions.region.constant_value
	region != "ap-south-1"
	msg := sprintf("[Mumbai only] Provider %s uses region %s. This build keeps every resource in ap-south-1.", [key, region])
}

deny contains msg if {
	some key, p in input.configuration.provider_config
	p.name == "aws"
	not is_string(object.get(p, ["expressions", "region", "constant_value"], null))
	msg := sprintf("[Mumbai only] Provider %s does not set the region as a fixed value. Write region = \"ap-south-1\" in the provider block.", [key])
}
