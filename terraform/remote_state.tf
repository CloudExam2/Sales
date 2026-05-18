# Core must be applied first so this state exists (same S3 bucket, key core/terraform.tfstate).
data "terraform_remote_state" "core" {
  backend = "s3"

  config = {
    bucket = "iteso-terraform-state-inaki-69"
    key    = "core/terraform.tfstate"
    region = var.aws_region
  }
}

# Catalog must be applied first so Sales knows where to call it.
# If it does not exist yet, `defaults` keeps Terraform from crashing.
data "terraform_remote_state" "catalog" {
  backend = "s3"

  config = {
    bucket = "iteso-terraform-state-inaki-69"
    key    = "catalog/terraform.tfstate"
    region = var.aws_region
  }

  defaults = {
    catalog_backend_url = ""
  }
}
