output "sales_instance_id" {
  value = aws_instance.sales_service.id
}

output "sales_public_ip" {
  value = aws_instance.sales_service.public_ip
}

output "ec2_instance_id" {
  description = "The ID of the EC2 instance for the Sales Service"
  value       = aws_instance.sales_service.id
}