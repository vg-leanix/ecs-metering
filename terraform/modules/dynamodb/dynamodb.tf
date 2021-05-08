
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

resource "aws_dynamodb_table" "db_init" {
  name           = "initDB"
  hash_key       = "id"
  billing_mode   = "PROVISIONED"
  write_capacity = 10
  read_capacity  = 20

  attribute {
    name = "id"
    type = "S"
  }
}
