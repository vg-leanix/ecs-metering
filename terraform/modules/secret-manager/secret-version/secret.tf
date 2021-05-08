resource "aws_secretsmanager_secret" "leanixsecret" {
  name = "leanixsecret2"
  rotation_rules {
    automatically_after_days = 0
  }
}