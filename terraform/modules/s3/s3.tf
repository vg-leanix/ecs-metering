resource "aws_s3_bucket" "s3_ldif" {
  bucket = "ecsbucktforldif1"
  acl    = "private"
}

output "s3_arn" {
  value = aws_s3_bucket.s3_ldif.arn
  description = "ARN of the s3 role"
}