resource "aws_secretsmanager_secret" "leanixsecret" {
  name = "leanixdata"
  rotation_rules {
    automatically_after_days = 0
  }
}