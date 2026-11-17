# A read-only role that GitHub Actions uses to make a Terraform plan on every pull request, so
# the plan can be checked against policies/rego before anything is merged (Release 3, Prevent).
#
# What:        GitHub's OpenID Connect identity provider, and one role that only a pull request
#              of the named repository can assume. The role can read resource settings, but not
#              the content of the data stores or logs.
# Why:         Rule 6(1)(b): no stored keys. GitHub receives short-lived credentials for each run
#              instead of an access key kept in its settings. Least privilege: reading settings
#              is enough to plan; reading personal data is not needed, so it is denied.
# Who runs it: The author, once, as BreakGlassAdmin (dpdp-workload-admin).
# When:        Release 3, Step 8.
# Changes AWS: Yes. One identity provider and one role in dpdp-workload. Free of charge.

data "aws_caller_identity" "current" {}

locals {
  state_bucket = "dpdp-tfstate-${data.aws_caller_identity.current.account_id}"

  # GitHub names the sender of each token in its "sub" claim. Repositories created after
  # 15 July 2026, and older ones that opt in, use immutable ids next to the names
  # (owner@id/name@id), so a deleted name taken over by someone else cannot match.
  # https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens
  owner   = split("/", var.github_repository)[0]
  repo    = split("/", var.github_repository)[1]
  subject = "repo:${local.owner}@${var.github_owner_id}/${local.repo}@${var.github_repository_id}:pull_request"
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Only pull requests of this repository, identified by its immutable ids, can assume the role.
# GitHub does not give these credentials to pull requests opened from forks.
resource "aws_iam_role" "plan" {
  name                 = "dpdp-github-plan"
  description          = "Read-only Terraform plan for pull requests (Release 3)"
  max_session_duration = 3600

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = local.subject
        }
      }
    }]
  })
}

# Read access to resource settings, which "terraform plan" needs.
resource "aws_iam_role_policy_attachment" "read_only" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# ReadOnlyAccess would also let the role read the data itself. Planning does not need it, so it
# is denied: object contents in every bucket except the Terraform state, table items, and log
# events.
resource "aws_iam_role_policy" "no_data_reads" {
  name = "deny-reading-personal-data"
  role = aws_iam_role.plan.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid         = "NoObjectReadsExceptState"
        Effect      = "Deny"
        Action      = ["s3:GetObject", "s3:GetObjectVersion"]
        NotResource = "arn:aws:s3:::${local.state_bucket}/*"
      },
      {
        Sid      = "NoTableOrLogReads"
        Effect   = "Deny"
        Resource = "*"
        Action = [
          "dynamodb:GetItem", "dynamodb:BatchGetItem", "dynamodb:Query", "dynamodb:Scan",
          "dynamodb:GetRecords", "logs:GetLogEvents", "logs:FilterLogEvents", "logs:StartQuery",
          "logs:GetQueryResults",
        ]
      },
    ]
  })
}
