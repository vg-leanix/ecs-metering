output "dynamodb_arn" {
  value = aws_dynamodb_table.task_states.arn
}