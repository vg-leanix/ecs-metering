output "lambda_arn" {
  value = aws_lambda_function.metering.arn
  description = "ARN of metering lambda function"
}