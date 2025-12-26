FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Default to running the gateway (can be overridden with Cloud Run args)
ENV SERVICE_MODE=single
ENV GATEWAY_PORT=8000
CMD ["python", "api_gateway.py"]
