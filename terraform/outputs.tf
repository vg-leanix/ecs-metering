output "lambda_metering_arn" {
  description = "Policy that allows the Lambda function to make the necessary API calls"
  value       = module.iam.lambda_iam_role_arn
}

output "task_states_db" {
  description = "ARN of DynamoDB to capture task states"
  value       = module.dynamodb.dynamodb_arn
}

output "cloudwatch_event_rule_arn" {
  description = "ARN of CloudWatch event rule"
  value       = module.cloudwatch.event_rule_arn
}
