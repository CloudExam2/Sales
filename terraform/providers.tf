terraform {
  backend "s3" {
    bucket = "iteso-terraform-state-inaki-69"
    key    = "sales/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

provider "github" {
  alias = "core"
  token = var.github_token
  owner = "CloudExam2"
}
