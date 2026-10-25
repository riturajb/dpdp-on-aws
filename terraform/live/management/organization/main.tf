# The AWS Organization: organisational units, member accounts and guardrail policies.
#
# This is the stack with the largest blast radius: a mistake here affects every account.
# It is applied only from a laptop with dpdp-mgmt-admin, after reading the plan line by line,
# and never by a pipeline. Accounts and the organisation are protected by prevent_destroy.
#
# Guardrails (service control policies) set limits that nobody in a member account can exceed,
# including administrators. They are attached in stages through var.scp_attachments
# (setup guide, Part 9). They never apply to the management account itself, which is why a
# faulty guardrail can always be detached from there.

# The organisation was created in the console (setup guide, Part 3). This block brings it under
# Terraform's control on the first apply, without recreating it.
import {
  to = aws_organizations_organization.this
  id = var.organization_id
}

# What is already switched on in the organisation. An organisation created through AWS's newer
# sign-up flow arrives with resource control policies and several AWS services already enabled.
# Terraform must keep all of them: switching them off could break access that AWS set up.
data "aws_organizations_organization" "current" {}

locals {
  # AWS services this build needs to work across all accounts: account settings, the
  # organisation trail, central management of root credentials, and IAM Identity Center sign-in.
  required_service_principals = [
    "account.amazonaws.com",
    "cloudtrail.amazonaws.com",
    "iam.amazonaws.com",
    "sso.amazonaws.com",
  ]

  # Policy types this build needs: guardrails (service control policies).
  required_policy_types = ["SERVICE_CONTROL_POLICY"]
}

resource "aws_organizations_organization" "this" {
  feature_set = "ALL"

  # Everything already enabled, plus what this build needs. Terraform only adds; it never
  # switches off a service or a policy type that is already on.
  aws_service_access_principals = setunion(
    data.aws_organizations_organization.current.aws_service_access_principals,
    local.required_service_principals,
  )

  enabled_policy_types = setunion(
    data.aws_organizations_organization.current.enabled_policy_types,
    local.required_policy_types,
  )

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  # The top of the organisation tree; the three units sit directly under it.
  root_id = aws_organizations_organization.this.roots[0].id

  ous = {
    security  = "Security"
    workloads = "Workloads"
    sandbox   = "Sandbox"
  }

  # Account name (without the dpdp- prefix) and the unit it belongs to.
  accounts = {
    "log-archive" = "security"
    "audit"       = "security"
    "workload"    = "workloads"
    "sandbox"     = "sandbox"
  }

  # Short name used in var.scp_attachments, and the policy file in policies/scp/.
  scp_files = {
    region   = "deny-regions-outside-mumbai"
    baseline = "baseline-protections"
    buckets  = "protect-log-and-evidence-buckets"
    cost     = "deny-costly-services"
  }

  # Turns {sandbox = ["region", "cost"]} into one entry per policy and unit, so that each
  # attachment is a separate resource and can be added or removed on its own.
  attachments = {
    for pair in flatten([
      for ou, names in var.scp_attachments : [
        for name in names : { key = "${ou}-${name}", ou = ou, name = name }
      ]
    ]) : pair.key => pair
  }
}

# The three organisational units: Security (log archive, audit), Workloads, Sandbox.
resource "aws_organizations_organizational_unit" "ou" {
  for_each  = local.ous
  name      = each.value
  parent_id = local.root_id
}

# The four member accounts. Each needs its own email address (var.account_emails).
# close_on_deletion = false: removing an account from this file never closes the real account.
# role_name: the administrator role AWS creates in each new account; ignored after creation.
resource "aws_organizations_account" "member" {
  for_each = local.accounts

  name              = "dpdp-${each.key}"
  email             = var.account_emails[each.key]
  parent_id         = aws_organizations_organizational_unit.ou[each.value].id
  role_name         = "OrganizationAccountAccessRole"
  close_on_deletion = false

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [role_name]
  }
}

# The four guardrail policies, read from policies/scp/. Creating a policy does not apply it;
# only an attachment below does. Each statement is explained in policies/scp/README.md.
resource "aws_organizations_policy" "scp" {
  for_each    = local.scp_files
  name        = "dpdp-${each.value}"
  description = "DPDP in Practice guardrail: ${each.value}"
  type        = "SERVICE_CONTROL_POLICY"
  content     = file("${path.root}/../../../../policies/scp/${each.value}.json")
}

# Attaches a guardrail to an organisational unit, as listed in var.scp_attachments.
# Every account in that unit is then bound by it.
resource "aws_organizations_policy_attachment" "scp" {
  for_each  = local.attachments
  policy_id = aws_organizations_policy.scp[each.value.name].id
  target_id = aws_organizations_organizational_unit.ou[each.value.ou].id
}
