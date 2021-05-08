output "taskdb_arn" {
  value = aws_dynamodb_table.task_states.arn
}

output "initdb_state" {
  value = aws_dynamodb_table.db_init.arn
}