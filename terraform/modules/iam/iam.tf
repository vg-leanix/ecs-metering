data "aws_region" "current" {}

resource "aws_iam_policy" "lambda_ecs_status" {
  name        = "LambdaECSTaskStatusPolicy-${data.aws_region.current.name}"
  description = "allows the Lambda function to make API calls"
  policy      = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "dynamodb:GetRecords",
            "Resource": "arn:aws:dynamodb:*:*:table/* "
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "pricing:DescribeServices",
                "logs:CreateLogStream",
                "pricing:GetAttributeValues",
                "ecs:*",
                "logs:PutLogEvents",
                "logs:CreateLogGroup",
                "pricing:GetProducts"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor2",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObjectAcl",
                "dynamodb:BatchGetItem",
                "logs:CreateLogStream",
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "s3:CreateBucket",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
                "logs:CreateLogGroup",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:s3:::*",
                "arn:aws:logs:*:*:*",
                "arn:aws:dynamodb:*:*:table/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetResourcePolicy",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
                "secretsmanager:ListSecretVersionIds",
                "kms:GenerateDataKey",
                "kms:Encrypt",
                "kms:Decrypt"

            ],
            "Resource": [
                "*"
            ]
        }
    ]
})

}


resource "aws_iam_role" "lambda_task_role" {
  name = "LambdaECSTaskStatusRole-${data.aws_region.current.name}"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : {
      "Effect" : "Allow",
      "Principal" : {
        "Service" : "lambda.amazonaws.com"
      },
      "Action" : "sts:AssumeRole"
    }
  })

}

resource "aws_iam_role_policy_attachment" "lambda_task_role_attachment" {
  role       = aws_iam_role.lambda_task_role.name
  policy_arn = aws_iam_policy.lambda_ecs_status.arn
}

