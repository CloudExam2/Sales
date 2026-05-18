resource "aws_instance" "sales_service" {
  ami                  = "ami-0440d3b780d96b29d" # Amazon Linux 2023
  instance_type        = "t2.micro"
    subnet_id              = data.terraform_remote_state.core.outputs.public_subnet_ids[0]
  iam_instance_profile = "LabInstanceProfile"
  vpc_security_group_ids = [aws_security_group.sales_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              set -e
              dnf update -y
              dnf install -y docker
              systemctl enable --now docker
              ACCOUNT_ID=${data.aws_caller_identity.current.account_id}
              aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.${var.aws_region}.amazonaws.com
              docker pull $ACCOUNT_ID.dkr.ecr.${var.aws_region}.amazonaws.com/sales-service:latest || true
              docker system prune -af || true
              docker image prune -af || true
              docker stop sales-app 2>/dev/null || true 
              docker rm sales-app 2>/dev/null || true
              docker run -d --name sales-app -p 80:8000 \
                $ACCOUNT_ID.dkr.ecr.${var.aws_region}.amazonaws.com/sales-service:latest
              EOF

  tags = {
    Name      = "Sales-Service"
    ManagedBy = "terraform-sales"
  }
}

resource "aws_eip" "sales" {
  domain = "vpc"
  tags = {
    Name      = "sales-service-eip"
    ManagedBy = "terraform-sales"
  }
}

resource "aws_eip_association" "sales" {
  instance_id   = aws_instance.sales_service.id
  allocation_id = aws_eip.sales.id
}

resource "github_actions_secret" "ec2_instance_id" {
  repository      = var.github_repo
  secret_name     = "EC2_SALES_ID"
  plaintext_value = aws_instance.sales_service.id
}

resource "github_actions_variable" "sales_url_for_core" {
  provider      = github.core
  repository    = "Core"
  variable_name = "SALES_BACKEND_URL"
  value         = "http://${aws_eip.sales.public_ip}:80"
}
