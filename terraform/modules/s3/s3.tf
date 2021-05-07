resource "aws_s3_bucket" "s3_ldif" {
  bucket = "ecsbucktforldif"
  acl    = "private"
}