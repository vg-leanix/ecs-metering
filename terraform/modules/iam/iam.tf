resource "aws_iam_policy" "lambda_ecs_status" {
  name        = "LambdaECSTaskStatusPolicy"
  description = "allows the Lambda function to make API calls"
  policy      = jsondecode(file("${path.module}/iam_ecs_status.json"))

}


resource "aws_iam_role" "lambda_task_role" {
  name = "LambdaECSTaskStatusRole"
  assume_role_policy = jsondecode({
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
  role       = aws_iam_role.lambda_task_role.arn
  policy_arn = aws_iam_policy.lambda_ecs_status.name
}

