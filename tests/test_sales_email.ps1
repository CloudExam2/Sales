# Create one sale on live Sales → SQS → Lambda → email.
# Run in PowerShell (NOT python):
#   cd Sales
#   .\tests\test_sales_email.ps1
#
# Or use Python (reads .env):
#   python tests/test_sale_sqs_notification.py

param(
    [string]$SalesUrl = $env:SALES_BASE_URL,
    [string]$CatalogUrl = $env:CATALOG_BASE_URL
)

if (-not $SalesUrl -or -not $CatalogUrl) {
    Write-Error "Set SALES_BASE_URL and CATALOG_BASE_URL in Sales/.env or pass -SalesUrl / -CatalogUrl"
    exit 1
}

$SalesUrl = $SalesUrl.TrimEnd("/")
$CatalogUrl = $CatalogUrl.TrimEnd("/")

Write-Host "Catalog: $CatalogUrl" -ForegroundColor DarkGray
Write-Host "Sales:   $SalesUrl" -ForegroundColor DarkGray

# Minimal Catalog seed: one client, two addresses, one product
$runTag = [int][double]::Parse((Get-Date -UFormat %s)) % 10000
$rfc = "PS{0:D6}{1:D4}" -f (Get-Random -Maximum 999999), $runTag

Write-Host "Seeding Catalog..." -ForegroundColor Cyan
$client = Invoke-RestMethod -Uri "$CatalogUrl/clients/" -Method Post -ContentType "application/json" -Body (@{
    rfc = $rfc; razon_social = "PS Email Test"; email = "ps@test.local"
} | ConvertTo-Json)

$fac = Invoke-RestMethod -Uri "$CatalogUrl/addresses/" -Method Post -ContentType "application/json" -Body (@{
    domicilio = "Fac 1"; address_type = "FACTURACIÓN"
} | ConvertTo-Json)

$env = Invoke-RestMethod -Uri "$CatalogUrl/addresses/" -Method Post -ContentType "application/json" -Body (@{
    domicilio = "Env 1"; address_type = "ENVÍO"
} | ConvertTo-Json)

$product = Invoke-RestMethod -Uri "$CatalogUrl/products/" -Method Post -ContentType "application/json" -Body (@{
    name = "Email Test Product"; unit = "unit"; base_price = 15.00
} | ConvertTo-Json)

$saleBody = @{
    folio            = "F-PS-EMAIL-$runTag"
    client_id        = $client.id
    fac_address_id   = $fac.id
    send_address_id  = $env.id
    contents         = @(@{
        product_id = $product.id
        quantity   = 1
    })
} | ConvertTo-Json -Depth 5

Write-Host "Creating sale (triggers SQS if Sales EC2 has SQS_QUEUE_URL)..." -ForegroundColor Cyan
try {
    $sale = Invoke-RestMethod -Uri "$SalesUrl/sales/" -Method Post -Body $saleBody -ContentType "application/json"
    Write-Host "Sale created: id=$($sale.id) folio=$($sale.folio) total=$($sale.total)" -ForegroundColor Green
    Write-Host "Check inaki.medina@gmail.com in 1-3 min. Sales logs: filter 'sales.sqs' in CloudWatch." -ForegroundColor Yellow
}
catch {
    Write-Error "POST /sales/ failed: $_"
    exit 1
}
