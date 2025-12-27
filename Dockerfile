FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "omni_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pipenv || true
RUN pip install --no-cache-dir fastapi uvicorn playwright pyyaml aiofiles httpx pydantic
# Install playwright browsers (non-interactive)
RUN playwright install --with-deps
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "api.intelligence_api:app", "--host", "0.0.0.0", "--port", "8080"]
