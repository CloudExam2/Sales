# Find current AWS Account ID
data "aws_caller_identity" "current" {}

# Find the existing Lambda Function URL by its name
data "aws_lambda_function_url" "notification_url" {
  function_name = "SalesNotificationHandler"
}

# Find the existing SQS Queue ARN
data "aws_s3_bucket" "tickets" {
  bucket = "iteso-tickets-377871695195"
}

# Find the existing ECR Repository URL
data "aws_ecr_repository" "sales" {
  name = "sales-service"
}