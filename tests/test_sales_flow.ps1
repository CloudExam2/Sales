$ErrorActionPreference = "Stop"

# 1. Create Client
$client = @{rfc="NEW_RFC_" + (Get-Date -Format "ssmm"); razon_social="Sales Test"; email="sales@test.com"} | ConvertTo-Json
$c_res = Invoke-RestMethod -Uri "http://localhost:8000/clients/" -Method Post -Body $client -ContentType "application/json"
$cid = $c_res.id
Write-Host "Client Created: $cid" -ForegroundColor Green

# 2. Create Product
$prod = @{name="Widget"; unit="pcs"; base_price=10.0; client_id=$cid} | ConvertTo-Json
$p_res = Invoke-RestMethod -Uri "http://localhost:8000/products/" -Method Post -Body $prod -ContentType "application/json"
$productId = $p_res.id
Write-Host "Product Created: $productId" -ForegroundColor Green

# 3. Create Sales Note
$note = @{
    folio = "F-" + (Get-Date -Format "ssmm")
    client_id = $cid
    fac_address_id = 1
    send_address_id = 1
    contents = @(@{product_id=$productId; unit_price=12.5; quantity=5})
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/sales/" -Method Post -Body $note -ContentType "application/json"