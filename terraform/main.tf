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

resource "aws_security_group" "sales_sg" {
  name        = "sales-service-sg"
  description = "Allow HTTP inbound"

  ingress { 
	from_port   = 22
	to_port     = 22
	protocol    = "tcp"
	cidr_blocks = ["189.163.24.169/32"]
	}

	# Authorize HTTP access for the test script
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["189.163.24.169/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "sales_service" {
  ami                  = "ami-0440d3b780d96b29d" # Amazon Linux 2023
  instance_type        = "t2.micro"
  iam_instance_profile = "LabInstanceProfile"
  vpc_security_group_ids = [aws_security_group.sales_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y docker
              systemctl enable --now docker
              
              # Authenticate using dynamic Account ID
              aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com
              
              # Pull and Run using dynamic Account ID and Lambda URL
              docker pull ${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com/sales-service:latest
              docker run -d -p 80:8080 \
                -e NOTIFICATION_URL=${data.aws_lambda_function_url.notification_url.function_url} \
                ${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com/sales-service:latest
              EOF

  tags = {
    Name = "Sales-Service"
  }
}