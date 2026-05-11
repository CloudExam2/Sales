terraform {
  backend "s3" {
    bucket         = "iteso-terraform-state-inaki-99" # Must be globally unique
    key            = "notifications/terraform.tfstate"
    region         = "us-east-1"
  }
}

terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

# Configure the GitHub Provider
provider "github" {
  token = var.github_token # Requires a Personal Access Token (PAT)
  owner = var.github_owner # GitHub username or organization
}
