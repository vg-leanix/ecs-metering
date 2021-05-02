terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

module "lambda" {
  source = "./modules/lambda"

  exec_role = module.iam.lambda_exec_role_arn

}

module "db" {
  source     = "./modules/dynamodb"
  table_name = "taskStatus"

}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  lambda_exec_role_arn = module.lambda.lambda_arn

}

module "iam" {
  source = "./modules/iam"
}
