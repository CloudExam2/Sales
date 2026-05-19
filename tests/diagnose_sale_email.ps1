# Exam2: CloudWatch logs + SNS email checklist (sale + CPU alerts)
# Run from Sales folder with AWS lab credentials:
#   .\tests\diagnose_sale_email.ps1

$region = "us-east-1"
$email = "inaki.medina@gmail.com"
$queueName = "sales-ticket-queue"
$lambdaName = "SalesNotificationHandler"

function Show-SnsEmailStatus {
    param([string]$Label, [string]$TopicNamePattern)
    $topics = aws sns list-topics --region $region --output json | ConvertFrom-Json
    $topicArn = ($topics.Topics | Where-Object { $_.TopicArn -like "*$TopicNamePattern*" }).TopicArn
    if (-not $topicArn) {
        Write-Host "  $Label : topic *$TopicNamePattern* NOT FOUND" -ForegroundColor Yellow
        return
    }
    $subs = aws sns list-subscriptions-by-topic --topic-arn $topicArn --region $region --output json | ConvertFrom-Json
    $mine = $subs.Subscriptions | Where-Object { $_.Endpoint -eq $email -and $_.Protocol -eq "email" }
    if (-not $mine) {
        Write-Host "  $Label : NO email subscription for $email" -ForegroundColor Red
        Write-Host "    Topic: $topicArn"
        return
    }
    if ($mine.SubscriptionArn -eq "PendingConfirmation") {
        Write-Host "  $Label : PENDING — open Gmail, search 'AWS Notifications', confirm subscription" -ForegroundColor Red
        Write-Host "    Topic: $topicArn"
    } else {
        Write-Host "  $Label : OK (confirmed)" -ForegroundColor Green
    }
}

Write-Host "`n=== CloudWatch log groups (region $region) ===" -ForegroundColor Cyan
Write-Host "Console: CloudWatch -> Logs -> Log groups -> search 'exam2'"
Write-Host "Names are /exam2/sales and /exam2/catalog (digit 2, not 'exam/sales').`n"

foreach ($name in @("/exam2/sales", "/exam2/catalog")) {
    $lg = aws logs describe-log-groups --log-group-name-prefix $name --region $region --output json 2>$null | ConvertFrom-Json
    $g = $lg.logGroups | Where-Object { $_.logGroupName -eq $name } | Select-Object -First 1
    if (-not $g) {
        Write-Host "  $name : MISSING — run Core CI (terraform logs.tf)" -ForegroundColor Red
        continue
    }
    $streams = aws logs describe-log-streams --log-group-name $name --order-by LastEventTime --descending --limit 3 --region $region --output json 2>$null | ConvertFrom-Json
    $streamNames = ($streams.logStreams | ForEach-Object { $_.logStreamName }) -join ", "
    if (-not $streamNames) {
        Write-Host "  $name : exists but NO streams — redeploy Catalog/Sales (Docker awslogs)" -ForegroundColor Yellow
    } else {
        Write-Host "  $name : OK — streams: $streamNames" -ForegroundColor Green
    }
}

Write-Host "`n=== Dashboard & CPU alarms ===" -ForegroundColor Cyan
Write-Host "Dashboard: Exam2-EC2-Overview"
Write-Host "Alarms:    exam2-sales-cpu-high, exam2-catalog-cpu-high"
$alarms = aws cloudwatch describe-alarms --alarm-name-prefix "exam2-" --region $region --output json 2>$null | ConvertFrom-Json
foreach ($a in $alarms.MetricAlarms) {
    Write-Host "  $($a.AlarmName) state=$($a.StateValue)"
}

Write-Host "`n=== SNS email subscriptions (alarms without email = usually Pending) ===" -ForegroundColor Cyan
Show-SnsEmailStatus -Label "CPU alerts" -TopicNamePattern "exam2-cpu-alerts"
Show-SnsEmailStatus -Label "Sale emails" -TopicNamePattern "Exam2-Sales-Notifications"

Write-Host "`n=== SQS + Lambda (sale path) ===" -ForegroundColor Cyan
$q = aws sqs get-queue-url --queue-name $queueName --region $region --output json 2>$null | ConvertFrom-Json
if (-not $q.QueueUrl) {
    Write-Host "FAIL: queue $queueName not found. Run Core CI." -ForegroundColor Red
} else {
    $url = $q.QueueUrl
    Write-Host "Queue: $url"
    $maps = aws lambda list-event-source-mappings --function-name $lambdaName --region $region --output json | ConvertFrom-Json
    $sqsMap = $maps.EventSourceMappings | Where-Object { $_.EventSourceArn -like "*$queueName*" }
    if ($sqsMap) { Write-Host "Lambda SQS mapping: $($sqsMap.State) enabled=$($sqsMap.Enabled)" }
    else { Write-Host "FAIL: Lambda has no SQS trigger. Run Notifications CI." -ForegroundColor Red }

    $testBody = '{"event":"sale_created","sale_id":0,"folio":"DIAG-TEST","client_id":1,"total":"9.99","contents":[]}'
    aws sqs send-message --queue-url $url --message-body $testBody --region $region | Out-Null
    Write-Host "Sent DIAG-TEST to queue — if sale email topic is confirmed, check inbox in 1-2 min."
}

Write-Host "`n=== Lambda logs ===" -ForegroundColor Cyan
Write-Host "CloudWatch -> Log groups -> /aws/lambda/$lambdaName"
Write-Host "`n=== Sales app logs (after a sale) ===" -ForegroundColor Cyan
Write-Host "Log group /exam2/sales -> stream sales-app -> filter 'sales.sqs'"
Write-Host "If you see 'SQS_QUEUE_URL not set', redeploy Sales CI so container gets the queue URL."
Write-Host ""
