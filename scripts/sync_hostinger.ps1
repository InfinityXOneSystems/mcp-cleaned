Param(
  [string]$ftpHost = "ftp.your-hostinger.com",
  [string]$ftpUser = "username",
  [string]$ftpPass = "password",
  [string]$localDir = "landing_pages",
  [string]$remoteDir = "/public_html"
)

Write-Host "Syncing $localDir -> $ftpHost:$remoteDir"

if (-not (Test-Path $localDir)) {
  Write-Error "Local directory $localDir does not exist"
  exit 1
}

Add-Type -AssemblyName System.Net
$client = New-Object System.Net.WebClient
$client.Credentials = New-Object System.Net.NetworkCredential($ftpUser,$ftpPass)

Get-ChildItem -Path $localDir -Recurse -File | ForEach-Object {
  $rel = $_.FullName.Substring((Get-Item $localDir).FullName.Length).TrimStart('\') -replace '\\','/' 
  $target = "ftp://$ftpHost$remoteDir/$rel"
  Write-Host "Uploading $rel -> $target"
  try {
    $uri = New-Object System.Uri($target)
    $client.UploadFile($uri, $_.FullName)
  } catch {
    Write-Warning "Failed to upload $rel: $_"
  }
}

Write-Host "Sync complete"
