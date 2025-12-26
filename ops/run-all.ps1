<#
Run API and crawlers in parallel (PowerShell helper).
Usage: from repo root run: .\ops\run-all.ps1
Ensure your virtualenv is activated or uncomment the activate line.
#>

# Uncomment to activate venv in script (optional)
# & .\.venv\Scripts\Activate.ps1

Write-Host "Starting MCP intelligence API and crawlers..."

$env:ADMIN_TOKEN = $env:ADMIN_TOKEN
$env:GOOGLE_APPLICATION_CREDENTIALS = $env:GOOGLE_APPLICATION_CREDENTIALS
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY

function Start-BackgroundProcess($args){
    $exe = $args[0]
    $arguments = $args[1]
    Start-Process -NoNewWindow -FilePath $exe -ArgumentList $arguments -WorkingDirectory (Get-Location)
}

# Start FastAPI / Omni Gateway
Start-BackgroundProcess @('.\.venv\Scripts\python.exe', '-m uvicorn omni_gateway:app --host 127.0.0.1 --port 8000')
Start-Sleep -Seconds 2

# Start business loans crawler
Start-BackgroundProcess @('.\.venv\Scripts\python.exe', 'crawler/run.py --seed crawler/seeds/business_loans.yaml')

# Start real estate crawler
Start-BackgroundProcess @('.\.venv\Scripts\python.exe', 'crawler/run.py --seed crawler/seeds/real_estate_distress.yaml')

Write-Host "Launched API and crawlers. Check crawler/output/raw and logs for output."
# Activate venv externally before running this script or uncomment the line below
# & .\.venv\Scripts\Activate.ps1

# Ensure deps and browsers installed (first run)
python -m pip install -r requirements.txt
playwright install

$env:ADMIN_TOKEN = $env:ADMIN_TOKEN
$env:GOOGLE_APPLICATION_CREDENTIALS = $env:GOOGLE_APPLICATION_CREDENTIALS
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY

# Start FastAPI (dashboard/API)
Start-Process -NoNewWindow -FilePath python -ArgumentList "-m uvicorn api.intelligence_api:app --host 0.0.0.0 --port 8000" -WorkingDirectory (Get-Location)

# Start crawler for business loans seed
Start-Process -NoNewWindow -FilePath python -ArgumentList "crawler/run.py --seed crawler/seeds/business_loans.yaml" -WorkingDirectory (Get-Location)

# Start crawler for real estate seed
Start-Process -NoNewWindow -FilePath python -ArgumentList "crawler/run.py --seed crawler/seeds/real_estate_distress.yaml" -WorkingDirectory (Get-Location)

# (Optional) Start a mock LLM adapter server or tests
Start-Process -NoNewWindow -FilePath python -ArgumentList "-m pytest tests -q" -WorkingDirectory (Get-Location)

Write-Host "Launched API, crawlers, and tests as background processes. Check logs and crawler/output/ for snapshots."
