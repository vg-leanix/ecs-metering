data "aws_region" "current" {}

resource "aws_secretsmanager_secret" "leanixsecret" {
  name = "leanixdatasecret-${data.aws_region.current.name}"
  recovery_window_in_days = 0
  rotation_rules {
    automatically_after_days = 7
  }
}