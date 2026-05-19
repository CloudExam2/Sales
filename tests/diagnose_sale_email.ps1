# Quick checklist: Sale -> SQS -> Lambda -> SNS email
# Run: .\tests\diagnose_sale_email.ps1
# Needs AWS CLI + lab credentials.

$region = "us-east-1"
$queueName = "sales-ticket-queue"
$lambdaName = "SalesNotificationHandler"
$email = "inaki.medina@gmail.com"

Write-Host "`n=== 1) SQS queue ===" -ForegroundColor Cyan
$q = aws sqs get-queue-url --queue-name $queueName --region $region --output json 2>$null | ConvertFrom-Json
if (-not $q.QueueUrl) { Write-Host "FAIL: queue $queueName not found. Run Core CI." -ForegroundColor Red; exit 1 }
$url = $q.QueueUrl
Write-Host "Queue URL: $url"

$attrs = aws sqs get-queue-attributes --queue-url $url --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible --region $region --output json | ConvertFrom-Json
Write-Host "Messages waiting: $($attrs.Attributes.ApproximateNumberOfMessages)"
Write-Host "In flight: $($attrs.Attributes.ApproximateNumberOfMessagesNotVisible)"

Write-Host "`n=== 2) Lambda SQS trigger ===" -ForegroundColor Cyan
$maps = aws lambda list-event-source-mappings --function-name $lambdaName --region $region --output json | ConvertFrom-Json
$sqsMap = $maps.EventSourceMappings | Where-Object { $_.EventSourceArn -like "*$queueName*" }
if (-not $sqsMap) {
    Write-Host "FAIL: No SQS event source on $lambdaName. Run Notifications CI with enable_sqs_trigger=true." -ForegroundColor Red
} else {
    Write-Host "Mapping state: $($sqsMap.State) enabled=$($sqsMap.Enabled)"
}

Write-Host "`n=== 3) SNS subscription ===" -ForegroundColor Cyan
$topics = aws sns list-topics --region $region --output json | ConvertFrom-Json
$topicArn = ($topics.Topics | Where-Object { $_.TopicArn -like "*Exam2-Sales-Notifications*" }).TopicArn
if (-not $topicArn) { Write-Host "WARN: topic Exam2-Sales-Notifications not found" -ForegroundColor Yellow }
else {
    $subs = aws sns list-subscriptions-by-topic --topic-arn $topicArn --region $region --output json | ConvertFrom-Json
    $mine = $subs.Subscriptions | Where-Object { $_.Endpoint -eq $email }
    if ($mine.SubscriptionArn -like "PendingConfirmation*") {
        Write-Host "FAIL: Email subscription PENDING — click link in inbox for $email" -ForegroundColor Red
    } elseif ($mine.SubscriptionArn -eq "PendingConfirmation") {
        Write-Host "FAIL: No subscription for $email on $topicArn" -ForegroundColor Red
    } else {
        Write-Host "OK: Subscription $($mine.SubscriptionArn)"
    }
}

Write-Host "`n=== 4) Test message (bypasses Sales) ===" -ForegroundColor Cyan
$testBody = '{"event":"sale_created","sale_id":0,"folio":"DIAG-TEST","client_id":1,"total":"9.99","contents":[]}'
aws sqs send-message --queue-url $url --message-body $testBody --region $region | Out-Null
Write-Host "Sent test sale JSON to queue. Check $email in 1-2 min + Lambda CloudWatch logs."

Write-Host "`n=== 5) Sales EC2 (manual) ===" -ForegroundColor Cyan
Write-Host "SSM: docker exec sales-app printenv SQS_QUEUE_URL"
Write-Host "Logs: CloudWatch /exam2/sales filter sales.sqs"
Write-Host ""
