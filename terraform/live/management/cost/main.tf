# Monthly budget for the whole organisation (all accounts share one bill).
#
# Emails at one third, two thirds and 100 percent of the limit (about INR 500, 1,000 and 1,500
# with the default USD 18), and when AWS forecasts that the month will exceed it.
# AWS Budgets works in US dollars. The guardrail "cost" blocks the most expensive services;
# this budget catches everything else.

resource "aws_budgets_budget" "monthly" {
  name         = "dpdp-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # One alert per threshold, based on actual spending.
  dynamic "notification" {
    for_each = [33, 67, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }

  # Early warning: the forecast for the month exceeds the budget.
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
