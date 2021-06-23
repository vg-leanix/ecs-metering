data "aws_region" "current" {}

resource "aws_s3_bucket" "s3_ldif" {
  bucket = "ecsbucktforldif-${data.aws_region.current.name}"
  acl    = "private"
  force_destroy = true
}