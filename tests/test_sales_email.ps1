$salesIp = "52.90.212.228"
$url = "http://$salesIp/sales" # Assuming your Python route is /sales

$payload = @{
    item  = "Industrial Robot Arm"
    price = "4500.00"
    user  = "Inaki Medina"
} | ConvertTo-Json

Write-Host "Sending request to Sales Service at $url..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $payload -ContentType "application/json"
    Write-Output "Status: Success"
    Write-Output ($response | ConvertTo-Json -Depth 5)
}
catch {
    Write-Error "Request failed. Check if EC2 is still initializing or if the /sales route is correct: $_"
}