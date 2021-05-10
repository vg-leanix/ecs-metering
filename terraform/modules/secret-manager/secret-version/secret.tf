resource "aws_secretsmanager_secret" "leanixsecret" {
  name = "leanixdatasecret"
  recovery_window_in_days = 0
  rotation_rules {
    automatically_after_days = 7
  }
}