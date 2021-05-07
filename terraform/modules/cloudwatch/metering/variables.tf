variable "lambda_exec_role_arn" {
  description = "ARN of lambda to use as target for event bus"
  type        = string
}

variable "lambda_function_name" {
  description = "function name of lambda to use as target for event bus"
  type        = string
}
