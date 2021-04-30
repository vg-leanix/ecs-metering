output "taskStatusPolicy" {
  description = "Policy that allows the Lambda function to make the necessary API calls"
  value       = module.vpc.public_subnets
}