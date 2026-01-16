# Download Production Database Backup
# This script downloads the production database backup from EC2

$keyPath = "$env:USERPROFILE\Downloads\fitness-key.pem"
$remotePath = "ubuntu@your-ec2-instance.compute.amazonaws.com:~/online-fitness-store-M/backups/fitness_club_db_prod_2026-01-11_05-03-51.backup"
$localPath = ".\backups\"

# Check if key file exists
if (-not (Test-Path $keyPath)) {
    Write-Host "Error: Key file not found at $keyPath" -ForegroundColor Red
    exit 1
}

# Create local backups directory if it doesn't exist
if (-not (Test-Path $localPath)) {
    New-Item -ItemType Directory -Path $localPath -Force | Out-Null
    Write-Host "Created backups directory" -ForegroundColor Green
}

Write-Host "Downloading backup from EC2..." -ForegroundColor Yellow
Write-Host "Key file: $keyPath" -ForegroundColor Gray
Write-Host "Remote file: $remotePath" -ForegroundColor Gray
Write-Host "Local destination: $localPath" -ForegroundColor Gray
Write-Host ""

# Download the backup
scp -i $keyPath $remotePath $localPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Backup download complete!" -ForegroundColor Green
    Write-Host "Backup saved to: $localPath" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Download failed. Please check the error message above." -ForegroundColor Red
    exit 1
}
