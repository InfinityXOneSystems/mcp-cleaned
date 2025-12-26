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
