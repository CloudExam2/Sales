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
                # -e NOTIFICATION_URL=$${this_is_now_ignored_by_terraform} \
                ${data.aws_caller_identity.current.account_id}.dkr.ecr.us-east-1.amazonaws.com/sales-service:latest
              EOF

  tags = {
    Name = "Sales-Service"
  }
}

# Automating the Secret Update
resource "github_actions_secret" "ec2_id" {
  repository       = "Exam2-Sales"
  secret_name      = "EC2_INSTANCE_ID"
  plaintext_value  = aws_instance.sales_service.id
}