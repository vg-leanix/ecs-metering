
resource "aws_cloudwatch_event_rule" "ecs_event_rule" {
  name          = "ECSTaskStatusRule"
  description   = "Capture ECS task state change events"
  event_pattern = jsonencode({ "source" : ["aws.ecs"], "detail-type" : ["ECS Task State Change"], "detail" : { "lastStatus" : ["RUNNING", "STOPPED"] } })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  target_id = "1"
  rule      = aws_cloudwatch_event_rule.ecs_event_rule.name
  arn       = var.lambda_exec_role_arn
}

resource "aws_lambda_permission" "lambda_event_permissiom" {
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ecs_event_rule.arn
}
