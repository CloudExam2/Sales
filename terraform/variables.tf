variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
}
variable "github_repo" {
  description = "The GitHub repository"
  type        = string
}

variable "tickets_bucket_name" {
  description = "Name of the S3 bucket created by Core for ticket payloads"
  type        = string
}