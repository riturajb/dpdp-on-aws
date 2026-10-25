# Terraform linting (run locally and in GitHub Actions). The "recommended" rules catch unused
# variables, missing version constraints and similar mistakes.
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}
