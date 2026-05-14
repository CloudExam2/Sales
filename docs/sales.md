📄 README.md (Sales Service)

## AWS student lab constraint

**Outbound internet from workloads:** Student lab accounts often **do not allow** application instances to reach the **public internet** for arbitrary traffic (generic HTTP/HTTPS egress, public package indexes, Docker Hub at runtime, etc.). Treat the lab as **private-by-default**: use **VPC endpoints** (or other AWS-documented private integration) for **ECR, SSM, S3, SQS**, and similar, unless your instructor explicitly permits open egress.

**Internet Gateway (optional in Core):** Core may ship with the **IGW commented out** and **VPC interface endpoints** for AWS APIs; see **Core** `docs/core.md`. **Browser `http://` to a public EC2 IP** usually needs an IGW (or another edge design). Use **SSM port forwarding** or **API Gateway** for access without public internet routing.

---

This repository contains the Sales Service, an independent microservice responsible for generating sales notes and managing their specific line-item contents. Following the 12-factor app methodology, this service maintains its own isolated environment and infrastructure.🏗️ Architecture & 12-Factor ComplianceCodebase (Factor I): One repository for the Sales business logic.Config (Factor III): Configuration is strictly injected via environment variables.Backing Services (Factor IV): Dedicated RDS and SQS are treated as attached resources.Statelessness (Factor VI): The application is stateless; all transactional data is persisted in the dedicated RDS instance.Logs (Factor XI): No internal logging or metric logic is included in this repository. The application streams to stdout for the Core infrastructure to aggregate.🛠️ Infrastructure (Terraform)This service manages its own dedicated resources via Terraform to ensure isolation:Networking: Private subnets and security groups specifically configured for Sales traffic.Database (RDS): A private PostgreSQL instance dedicated solely to sales notes and item contents.Compute (EC2): A dedicated instance to host the Dockerized application process.🚀 CI/CD & DockerContainerization: The service is packaged into an immutable Docker image.Pipeline (GitHub Actions):Build: Triggers on push to main.Publish: Automatically pushes the image to Amazon ECR.Deploy: Uses AWS SSM to pull the latest image and restart the container on the target EC2.📂 Project StructurePlaintext.
├── .github/workflows/  # CI/CD Pipelines (Github Actions)
├── terraform/          # Dedicated Infrastructure (EC2, RDS, Network)
├── src/
│   ├── crud/           # SQL Logic for Notes & Contents
│   ├── schemas/        # Pydantic models for API & SQS payloads
│   └── main.py         # FastAPI Entrypoint
├── Dockerfile          # Container Definition
└── requirements.txt    # Python Dependencies
📄 environment.md (Sales Service)This document defines the variables required for the Sales Service to function. These must be provided via the CI/CD pipeline or a local .env file.VariableDescriptionExample / FormatDATABASE_URLConnection string for the Sales RDS.postgresql://user:pass@host:5432/dbSQS_NOTIFY_URLURL of the SQS queue for notifications.[https://sqs.us-east-1.amazonaws.com/](https://sqs.us-east-1.amazonaws.com/)...AWS_REGIONTarget region for AWS clients.us-east-1PORTInternal application port.8000Required Secrets (GitHub Secrets)The following credentials must be added to the repository secrets for the pipeline to succeed:DB_PASSWORD: Master password for the service RDS.AWS_ACCESS_KEY_ID: Credentials with ECR and SQS permissions.AWS_SECRET_ACCESS_KEY: Credentials with ECR and SQS permissions.AWS_SESSION_TOKEN: Required if using temporary lab credentials.