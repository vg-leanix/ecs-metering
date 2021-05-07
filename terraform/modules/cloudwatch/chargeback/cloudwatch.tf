resource "aws_cloudwatch_event_rule" "run_daily" {
    name = "ComputeECSCostDaily"
    description = "Compute ECS Services daily and export to LeanIX CI workspace"
    schedule_expression = "cron(7 00 * * ? *)"
}

resource "aws_cloudwatch_event_target" "ecs-chargeback_every_day" {
    rule      = aws_cloudwatch_event_rule.run_daily.name
    arn       = var.lambda_exec_role_arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_ecs-chargeback" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = var.lambda_function_name
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.run_daily.arn}"
}