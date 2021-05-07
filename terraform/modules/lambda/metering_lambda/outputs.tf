output "lambda_arn" {
  value = aws_lambda_function.metering.arn
  description = "ARN of metering lambda function"
}

output "lambda_function_name" {
  value = aws_lambda_function.metering.function_name
  description = "name of lambda function"
}