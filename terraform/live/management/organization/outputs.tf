# Account and unit ids, needed for the CLI profiles and other stacks, and the list of
# guardrails currently attached (for the checkpoint in the setup guide, Part 10.2).

output "organization_id" {
  value = aws_organizations_organization.this.id
}

output "account_ids" {
  value = { for k, a in aws_organizations_account.member : k => a.id }
}

output "ou_ids" {
  value = { for k, o in aws_organizations_organizational_unit.ou : k => o.id }
}

output "attached_guardrails" {
  value = keys(local.attachments)
}
