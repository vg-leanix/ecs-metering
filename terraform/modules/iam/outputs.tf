output "iam_policy_arn" {
  value = aws_iam_policy.lambda_ecs_status.arn
  description = "ARN of the ECSStatus Policy"
}

output "lambda_iam_role_arn" {
  value = aws_iam_role.lambda_task_role.arn
  description = "ARN of the lambda role"
}