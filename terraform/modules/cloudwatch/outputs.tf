output "event_rule_arn" {
  value = aws_cloudwatch_event_rule.ecs_event_rule.arn
}