resource "aws_iam_policy" "lambda_ecs_status" {
  name        = "LambdaECSTaskStatusPolicy"
  description = "allows the Lambda function to make API calls"
  policy      = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "ecs:DescribeContainerInstances",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
})

}


resource "aws_iam_role" "lambda_task_role" {
  name = "LambdaECSTaskStatusRole"
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

