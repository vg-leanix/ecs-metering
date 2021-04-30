terraform {
  required_providers {
    aws = {
        source  = "hashicorp/aws"
    }
  }
}

module "lambda" {
  source = "./modules/lambda"
  depends_on = [db, cloudwatch]

}

module "db" {
  source = "./modules/dynamodb"

}

module "cloudwatch" {
  source = "./modules/cloudwatch"

}