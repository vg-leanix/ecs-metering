
resource "aws_lambda_function" "metering" {
  function_name = "ecs-meter"
  role          = var.exec_role
  filename      = "taskstatus.zip"
  handler       = "ecsTaskStatus.lambda_handler"
  runtime       = "python3.7"

}

