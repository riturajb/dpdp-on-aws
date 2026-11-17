# The role GitHub Actions assumes. Its ARN contains the account id: store it as a GitHub
# secret (Release 3 guide, Step 8), never in the repository.

output "plan_role_arn" {
  description = "Role for the plan job in GitHub Actions"
  value       = aws_iam_role.plan.arn
  sensitive   = true
}
