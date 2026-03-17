$baseUrl = "http://localhost:8000/api/v1/auth"

# Test 1: Register a new user
Write-Host "=== TEST 1: Register User ===" -ForegroundColor Green
$registerData = @{
    email = "test@weforeverdrip.com"
    first_name = "Tobe"
    last_name = "Drip"
    password = "Wfd2025!"
    confirm_password = "Wfd2025!"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/register/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $registerData
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    $body = $response.Content | ConvertFrom-Json
    Write-Host ($body | ConvertTo-Json -Depth 3)
    $access_token = $body.access
    $refresh_token = $body.refresh
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode
}

# Test 2: Login with the registered user
Write-Host "`n=== TEST 2: Login User ===" -ForegroundColor Green
$loginData = @{
    email = "test@weforeverdrip.com"
    password = "Wfd2025!"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/login/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $loginData
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    $body = $response.Content | ConvertFrom-Json
    Write-Host ($body | ConvertTo-Json -Depth 3)
    $access_token = $body.access
    $refresh_token = $body.refresh
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

# Test 3: Get User Profile
Write-Host "`n=== TEST 3: Get User Profile ===" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/profile/" -Method GET -Headers @{"Authorization"="Bearer $access_token"; "Content-Type"="application/json"}
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

# Test 4: Create an Address
Write-Host "`n=== TEST 4: Create Address ===" -ForegroundColor Green
$addressData = @{
    street = "12 Independence Layout"
    city = "Enugu"
    state = "Enugu State"
    country = "Nigeria"
    is_default = $true
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/addresses/" -Method POST -Headers @{"Authorization"="Bearer $access_token"; "Content-Type"="application/json"} -Body $addressData
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    $addressBody = $response.Content | ConvertFrom-Json
    Write-Host ($addressBody | ConvertTo-Json -Depth 3)
    $address_id = $addressBody.id
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

# Test 5: Get All Addresses
Write-Host "`n=== TEST 5: Get All Addresses ===" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/addresses/" -Method GET -Headers @{"Authorization"="Bearer $access_token"; "Content-Type"="application/json"}
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

# Test 6: Logout
Write-Host "`n=== TEST 6: Logout User ===" -ForegroundColor Green
$logoutData = @{
    refresh = $refresh_token
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/logout/" -Method POST -Headers @{"Authorization"="Bearer $access_token"; "Content-Type"="application/json"} -Body $logoutData
    Write-Host "Status: $($response.StatusCode) ✓" -ForegroundColor Green
    Write-Host ($response.Content | ConvertFrom-Json | ConvertTo-Json)
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
}

# Test 7: Try to use old refresh token (should fail)
Write-Host "`n=== TEST 7: Test Blacklisted Token ===" -ForegroundColor Green
$refreshData = @{
    refresh = $refresh_token
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/token/refresh/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $refreshData
    Write-Host "Error - Token should be blacklisted! Status: $($response.StatusCode)" -ForegroundColor Red
} catch {
    Write-Host "Status: Token blacklisted ✓" -ForegroundColor Green
    Write-Host "Error (expected): $($_.Exception.Message)" -ForegroundColor Green
}
