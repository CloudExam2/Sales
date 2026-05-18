output "ec2_sales_id" {
  description = "EC2 instance ID for SSM deploy and debugging"
  value       = aws_instance.sales_service.id
}

output "sales_public_ip" {
  description = "Stable public IPv4 (Elastic IP) for Sales"
  value       = aws_eip.sales.public_ip
}