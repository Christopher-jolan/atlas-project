# Atlas Call Intelligence - Test Script
# Usage: .\run-test.ps1
# Requires: Docker running, n8n active, mailer on port 8765 (optional)

$ErrorActionPreference = "Stop"
$payloadPath = Join-Path $PSScriptRoot "test-payload.json"
$resultPath = Join-Path $PSScriptRoot "test-result.json"

Write-Host "Sending test call to n8n webhook..." -ForegroundColor Cyan
$payload = Get-Content $payloadPath -Raw -Encoding UTF8
$resp = Invoke-WebRequest `
    -Uri "http://localhost:5678/webhook/atlas/call-intelligence" `
    -Method POST `
    -ContentType "application/json; charset=utf-8" `
    -Body $payload `
    -TimeoutSec 300 `
    -UseBasicParsing

Write-Host "HTTP $($resp.StatusCode) - $($resp.Content.Length) bytes" -ForegroundColor Green
$resp.Content | Out-File $resultPath -Encoding UTF8

$json = $resp.Content | ConvertFrom-Json
Write-Host "success=$($json.success) department=$($json.department) email_sent=$($json.email_sent)"
if ($json.analysis.ticket.title) { Write-Host "ticket: $($json.analysis.ticket.title)" }

if (-not $json.email_sent -and $env:SMTP_PASS) {
    Write-Host "Retrying email via local mailer..." -ForegroundColor Yellow
    $mail = @{
        to      = "mohamad.j1380@yahoo.com"
        subject = $json.manager_notification.subject
        body    = $json.manager_notification.body
    } | ConvertTo-Json
    $mailResp = Invoke-RestMethod -Uri "http://localhost:8765/send" -Method POST -ContentType "application/json; charset=utf-8" -Body $mail
    Write-Host "Mailer: $($mailResp | ConvertTo-Json -Compress)"
}

Write-Host "Full result saved to: $resultPath"
