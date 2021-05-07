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

module "metering_lambda" {
  source = "./modules/lambda/metering_lambda"

  exec_role = module.iam.lambda_iam_role_arn

}

module "chargeback_lambda" {
  source = "./modules/lambda/chargeback_lambda"

  exec_role = module.iam.lambda_iam_role_arn

}

module "dynamodb" {
  source = "./modules/dynamodb"

}

module "cloudwatch_metering" {
  source = "./modules/cloudwatch/metering"

  lambda_exec_role_arn = module.metering_lambda.lambda_arn
  lambda_function_name = module.metering_lambda.lambda_function_name

}

module "cloudwatch_chargeback" {
  source = "./modules/cloudwatch/chargeback"

  lambda_exec_role_arn = module.chargeback_lambda.lambda_arn
  lambda_function_name = module.chargeback_lambda.lambda_function_name

}

module "iam" {
  source = "./modules/iam"
}
