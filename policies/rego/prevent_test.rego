# Unit tests for prevent.rego, run by test T12 (conftest verify).
#
# What:        Each test feeds a small plan to the rules and checks the result: a compliant plan
#              passes, and each kind of non-compliant change is denied with the right provision.
# Why:         A rule that has never been seen to fail could be broken without anyone noticing.
# Who runs it: Anyone, with no AWS access: conftest verify --policy policies/rego
# When:        Release 3, Step 1 and Step 7; after any change to prevent.rego. The API tests
#              were added in Release 4.
# Changes AWS: No.

package main

import rego.v1

register := [{"id": "customers-db"}, {"id": "bureau-reports"}]

provider_mumbai := {"aws": {"name": "aws", "expressions": {"region": {"constant_value": "ap-south-1"}}}}

rc(type, address, after) := {"address": address, "mode": "managed", "type": type, "change": {"actions": ["create"], "after": after}}

personal_bucket := rc("aws_s3_bucket", "aws_s3_bucket.reports", {"bucket": "dpdp-bureau-reports-1", "tags_all": {"DataClass": "personal", "RegisterStore": "bureau-reports"}})

blocked := rc("aws_s3_bucket_public_access_block", "aws_s3_bucket_public_access_block.reports", {"bucket": "dpdp-bureau-reports-1", "block_public_acls": true, "block_public_policy": true, "ignore_public_acls": true, "restrict_public_buckets": true})

versioned := rc("aws_s3_bucket_versioning", "aws_s3_bucket_versioning.reports", {"bucket": "dpdp-bureau-reports-1", "versioning_configuration": [{"status": "Enabled"}]})

personal_table := rc("aws_dynamodb_table", "aws_dynamodb_table.customers", {"name": "dpdp-customers", "tags_all": {"DataClass": "personal", "RegisterStore": "customers-db"}, "point_in_time_recovery": [{"enabled": true}]})

log_year := rc("aws_cloudwatch_log_group", "aws_cloudwatch_log_group.app", {"name": "/fernleaf/app", "retention_in_days": 365})

good_plan := {"configuration": {"provider_config": provider_mumbai}, "resource_changes": [personal_bucket, blocked, versioned, personal_table, log_year]}

denied_with(plan, prefix) if {
	some msg in deny with input as plan with data.stores as register
	startswith(msg, prefix)
}

test_compliant_plan_passes if {
	count(deny) == 0 with input as good_plan with data.stores as register
}

test_untagged_store_is_denied if {
	b := rc("aws_s3_bucket", "aws_s3_bucket.export", {"bucket": "dpdp-export-1", "tags_all": {}})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [b]}, "[s.8(1)]")
}

test_unregistered_store_is_denied if {
	t := rc("aws_dynamodb_table", "aws_dynamodb_table.leads", {"name": "leads", "tags_all": {"DataClass": "personal", "RegisterStore": "leads-db"}, "point_in_time_recovery": [{"enabled": true}]})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [t]}, "[s.8(1)]")
}

test_public_bucket_is_denied if {
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [personal_bucket, versioned]}, "[R.6(1)(b)]")
}

test_bucket_without_fixed_name_is_denied if {
	b := rc("aws_s3_bucket", "aws_s3_bucket.random", {"tags_all": {"DataClass": "none"}})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [b]}, "[R.6(1)(b)]")
}

test_unversioned_personal_bucket_is_denied if {
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [personal_bucket, blocked]}, "[R.6(1)(d)]")
}

test_table_without_pitr_is_denied if {
	t := rc("aws_dynamodb_table", "aws_dynamodb_table.customers", {"name": "dpdp-customers", "tags_all": {"DataClass": "personal", "RegisterStore": "customers-db"}, "point_in_time_recovery": [{"enabled": false}]})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [t]}, "[R.6(1)(d)]")
}

test_short_log_retention_is_denied if {
	l := rc("aws_cloudwatch_log_group", "aws_cloudwatch_log_group.debug", {"name": "/fernleaf/debug", "retention_in_days": 7})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [l]}, "[R.6(1)(e)]")
}

test_never_expiring_logs_pass if {
	l := rc("aws_cloudwatch_log_group", "aws_cloudwatch_log_group.app", {"name": "/fernleaf/app", "retention_in_days": 0})
	count(deny) == 0 with input as {"configuration": {"provider_config": provider_mumbai}, "resource_changes": [l]} with data.stores as register
}

test_other_region_is_denied if {
	p := {"aws": {"name": "aws", "expressions": {"region": {"constant_value": "ap-southeast-1"}}}}
	denied_with({"configuration": {"provider_config": p}, "resource_changes": []}, "[Mumbai only]")
}

test_region_from_variable_is_denied if {
	p := {"aws": {"name": "aws", "expressions": {"region": {"references": ["var.region"]}}}}
	denied_with({"configuration": {"provider_config": p}, "resource_changes": []}, "[Mumbai only]")
}

test_deleted_resources_are_not_checked if {
	gone := {"address": "aws_s3_bucket.old", "mode": "managed", "type": "aws_s3_bucket", "change": {"actions": ["delete"], "after": null}}
	count(deny) == 0 with input as {"configuration": {"provider_config": provider_mumbai}, "resource_changes": [gone]} with data.stores as register
}

test_open_api_route_is_denied if {
	r := rc("aws_apigatewayv2_route", "aws_apigatewayv2_route.open", {"route_key": "POST /consents", "authorization_type": "NONE"})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [r]}, "[R.6(1)(b)]")
}

test_signed_api_route_passes if {
	r := rc("aws_apigatewayv2_route", "aws_apigatewayv2_route.signed", {"route_key": "POST /consents", "authorization_type": "AWS_IAM"})
	count(deny) == 0 with input as {"configuration": {"provider_config": provider_mumbai}, "resource_changes": [r]} with data.stores as register
}

test_open_rest_method_is_denied if {
	m := rc("aws_api_gateway_method", "aws_api_gateway_method.open", {"http_method": "GET", "authorization": "NONE"})
	denied_with({"configuration": {"provider_config": provider_mumbai}, "resource_changes": [m]}, "[R.6(1)(b)]")
}
