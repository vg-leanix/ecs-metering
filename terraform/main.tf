terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

module "lambda" {
  source = "./modules/lambda"

  exec_role = module.iam.lambda_iam_role_arn

}

module "dynamodb" {
  source = "./modules/dynamodb"

}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  lambda_exec_role_arn = module.lambda.lambda_arn
  lambda_function_name = module.lambda.lambda_function_name

}

module "iam" {
  source = "./modules/iam"
}
