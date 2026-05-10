output "sales_instance_id" {
  value = aws_instance.sales_service.id
}

output "sales_public_ip" {
  value = aws_instance.sales_service.public_ip
}