
resource "aws_lambda_function" "metering" {
  function_name = "ecs-meter"
  role= aws_iam_role.lambdaIAM.arn

}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"
  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }
}
EOF
}
