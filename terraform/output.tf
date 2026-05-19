output "ec2_sales_id" {
  description = "EC2 instance ID for SSM deploy and debugging"
  value       = aws_instance.sales_service.id
}

output "sales_public_ip" {
  description = "Stable public IPv4 (Elastic IP) for Sales"
  value       = aws_eip.sales.public_ip
}

output "sales_backend_url" {
  description = "Base URL written to Core SALES_BACKEND_URL"
  value       = "http://${aws_eip.sales.public_ip}:80"
}

output "catalog_service_url" {
  description = "URL Sales will use to call Catalog (from Catalog remote state)."
  value       = data.terraform_remote_state.catalog.outputs.catalog_backend_url
}

output "sales_log_group_name" {
  description = "CloudWatch Logs group for Sales (from Core remote state)"
  value       = data.terraform_remote_state.core.outputs.sales_log_group_name
}

output "sqs_queue_url" {
  description = "Core sales-ticket-queue URL for sale notifications"
  value       = try(data.terraform_remote_state.core.outputs.sqs_queue_url, "")
}