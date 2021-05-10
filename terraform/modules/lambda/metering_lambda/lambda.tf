provider "archive" {}

data "archive_file" "zip" {
  type        = "zip"
  source_file = "${path.module}/ecsTaskStatus.py"
  output_path = "${path.module}/ecs_task_status.zip"
  
}


resource "aws_lambda_function" "metering" {
  function_name = "ecs-meter"
  role          = var.exec_role
  filename      = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256
  handler       = "ecsTaskStatus.lambda_handler"
  runtime       = "python3.7"
  timeout          = 30
}

