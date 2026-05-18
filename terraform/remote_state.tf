# Core must be applied first so this state exists (same S3 bucket, key core/terraform.tfstate).
data "terraform_remote_state" "core" {
  backend = "s3"

  config = {
    bucket = "iteso-terraform-state-inaki-69"
    key    = "core/terraform.tfstate"
    region = var.aws_region
  }
}
