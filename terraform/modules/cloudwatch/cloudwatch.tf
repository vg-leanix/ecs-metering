
resource "aws_cloudwatch_event_rule" "ecs_event_rule" {
  name          = "ECSTaskStatusRule"
  description   = "Capture ECS task state change events"
  event_pattern = jsondecode(file("${path.module}/event_pattern.json"))
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  target_id = "1"
  rule      = aws_cloudwatch_event_rule.ecs_event_rule.name
  arn       = var.lambda_exec_role_arn
}
