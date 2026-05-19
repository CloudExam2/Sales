# EC2 + EIP + GitHub wiring (scripts live in ./compute/)

resource "aws_instance" "sales_service" {
  ami                    = "ami-0440d3b780d96b29d" # Amazon Linux 2023 (us-east-1)
  instance_type          = "t2.micro"
  subnet_id              = data.terraform_remote_state.core.outputs.public_subnet_ids[0]
  iam_instance_profile   = "LabInstanceProfile"
  vpc_security_group_ids = [aws_security_group.sales_sg.id]

  user_data_replace_on_change = true

  user_data = base64encode(templatefile("${path.module}/compute/user_data.sh.tpl", {
    docker_script = indent(2, templatefile("${path.module}/compute/docker.sh.tpl", {
      aws_region = var.aws_region
      account_id = data.aws_caller_identity.current.account_id
      ecr_repo   = "sales-service"
      app_name   = "sales-app"
    }))
  }))

  tags = {
    Name      = "Sales-Service"
    ManagedBy = "terraform-sales"
  }

  lifecycle {
    create_before_destroy = true
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
