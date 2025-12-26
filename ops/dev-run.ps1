# Activate venv then run dev server and ensure browsers are installed
python -m pip install -r requirements.txt
playwright install
$env:PYTHONPATH = "."
uvicorn api.intelligence_api:app --reload --host 0.0.0.0 --port 8000
