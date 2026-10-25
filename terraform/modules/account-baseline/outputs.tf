# The analyzer's ARN, for reference in later releases.

output "analyzer_arn" {
  value = aws_accessanalyzer_analyzer.this.arn
}
