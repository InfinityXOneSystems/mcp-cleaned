param(
    [string]$remoteUrl
)
if (-not $remoteUrl) { Write-Host 'Usage: .\ops\init_results_repo.ps1 -remoteUrl <git-url>'; exit 1 }

$tmp = Join-Path $PSScriptRoot '..\results_tmp'
if(Test-Path $tmp){ Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
Push-Location $tmp
git init
Copy-Item -Path (Join-Path $PSScriptRoot '..\results\*') -Destination $tmp -Recurse
git add .
git commit -m 'Initial scaffold commit for results repo'
git remote add origin $remoteUrl
git branch -M main
git push -u origin main
Pop-Location
Remove-Item $tmp -Recurse -Force
Write-Host 'Initialized remote results repo.'
