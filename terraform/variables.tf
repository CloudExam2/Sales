variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "The GitHub repository in 'username/repo' format"
  type        = string
}