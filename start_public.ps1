# Start the Attire Checker on this PC and publish it through a Cloudflare quick tunnel.
# Usage (PowerShell):  .\start_public.ps1
# The public https://...trycloudflare.com address is printed below; it changes on every start.
# Keep this window open; press Ctrl+C to stop both.
$ErrorActionPreference = "Stop"
$project = $PSScriptRoot
$cloudflared = Join-Path $env:USERPROFILE "cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflared)) { throw "cloudflared.exe not found at $cloudflared" }

# Free port 5000 if an earlier server is still running.
Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

$server = Start-Process -FilePath (Join-Path $project ".venv\Scripts\python.exe") -ArgumentList "serve.py" `
    -WorkingDirectory $project -PassThru -NoNewWindow
try {
    Write-Host "Starting server (models load in the background)..."
    Start-Sleep -Seconds 5
    Write-Host "Opening tunnel - look for the https://*.trycloudflare.com line below." -ForegroundColor Green
    & $cloudflared tunnel --no-autoupdate --url http://127.0.0.1:5000
} finally {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
}
