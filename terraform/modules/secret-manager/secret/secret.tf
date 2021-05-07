resource "aws_secretsmanager_secret_version" "secret" {
  secret_id     = var.id
  secret_string = jsonencode(var.credentials)
}