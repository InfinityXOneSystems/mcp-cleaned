# Quick secret scan: looks for private keys and API key patterns
$patterns = @(
  '-----BEGIN PRIVATE KEY-----',
  'BEGIN RSA PRIVATE KEY',
  'AIza[0-9A-Za-z-_]{35}',
  'AKIA[0-9A-Z]{16}',
  '-----BEGIN CERTIFICATE-----'
)

$root = Get-Location
Write-Host "Scanning repository for potential secrets..."

Get-ChildItem -Path $root -Recurse -File -Include *.py,*.yaml,*.yml,*.json,*.env,*.txt,*.md | ForEach-Object {
  $content = Get-Content -Raw $_.FullName -ErrorAction SilentlyContinue
  foreach ($p in $patterns) {
    if ($content -match $p) {
      Write-Host "[POTENTIAL SECRET] $($_.FullName) matches pattern: $p"
    }
  }
}

Write-Host "Scan complete. Review results and remove secrets from repo if any found."
