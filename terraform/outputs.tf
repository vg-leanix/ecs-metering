output "lambda_metering_arn" {
  description = "Policy that allows the Lambda function to make the necessary API calls"
  value       = module.metering_lambda.lambda_arn
}

output "lambda_chargeback_arn" {
  description = "Policy that allows the Lambda function to make the necessary API calls"
  value       = module.chargeback_lambda.lambda_arn
}

output "task_states_db" {
  description = "ARN of DynamoDB to capture task states"
  value       = module.dynamodb.taskdb_arn
}

output "cloudwatch_event_rule_arn" {
  description = "ARN of CloudWatch event rule"
  value       = module.cloudwatch_metering.event_rule_arn
}

output "cloudwatch_event_rule_run_daily" {
  description = "ARN of CloudWatch event rule"
  value       = module.cloudwatch_chargeback.event_rule_arn
}

output "exec_iam_role_lambda" {
  description = "ARN of IAM execution role for lambda function"
  value       = module.iam.lambda_iam_role_arn
}

output "s3_lidf_arn" {
  description = "ARN of S3 for LDIF storage"
  value       = module.s3_ldif.s3_arn
}

output "aws_secretsmanager_secret_id" {
  value       = module.aws_secretsmanager_secret.secret_version_id
}