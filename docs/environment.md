
These variables are required for the Terraform provider and the GitHub Actions runner to manage the global AWS environment.

| Variable | Description | Source |
| :--- | :--- | :--- |
| **AWS_ACCESS_KEY_ID** | IAM credentials for provisioning. | GitHub Secrets |
| **AWS_SECRET_ACCESS_KEY** | IAM credentials for provisioning. | GitHub Secrets |
| **AWS_SESSION_TOKEN** | Required for temporary/lab accounts. | GitHub Secrets |
| **AWS_REGION** | Default region (e.g., us-east-1). | Static Config |
| **GH_PAT** | Personal Access Token for GitHub API. | GitHub Secrets |
| **TF_STATE_BUCKET** | S3 bucket for remote terraform state. | providers.tf |
