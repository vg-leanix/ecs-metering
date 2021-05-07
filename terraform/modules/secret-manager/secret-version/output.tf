output "secret_version_id" {
  value = aws_secretsmanager_secret.leanixsecret.id
  description = "Amazon Resource Name (ARN) of the secret."
}