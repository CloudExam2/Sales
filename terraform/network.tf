resource "aws_security_group" "sales_sg" {
  name_prefix = "sales-service-ec2-"
  description = "HTTP and SSH for lab console connect and browser access"
  vpc_id      = data.terraform_remote_state.core.outputs.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sales-ec2-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "sales_rds" {
  name_prefix = "sales-service-rds-"
  description = "PostgreSQL for Sales - ingress only from Sales EC2 SG"
  vpc_id      = data.terraform_remote_state.core.outputs.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.sales_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sales-rds-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

 