$sqsUrl = "https://sqs.us-east-1.amazonaws.com/008611926542/sales-ticket-queue"
$payload = @{
    order_id = "INTEGRATION-TEST-001"
    customer_email = "your-verified-email@example.com"
    total = 125.50
} | ConvertTo-Json -Compress

aws sqs send-message --queue-url $sqsUrl --message-body $payload --region us-east-1