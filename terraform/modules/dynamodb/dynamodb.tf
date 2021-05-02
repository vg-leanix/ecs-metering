
resource "aws_dynamodb_table" "task_states" {
  name           = "ECSTaskStatus"
  hash_key       = "taskArn"
  billing_mode   = "PROVISIONED"
  write_capacity = 10
  read_capacity  = 20

  attribute {
    name = "taskArn"
    type = "S"
  }
}
