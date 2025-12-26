FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Default to running the Omni Gateway (59 MCP tools + Cockpit + Credential Gateway + Autonomy)
ENV SERVICE_MODE=single
ENV GATEWAY_PORT=8000
ENV FIRESTORE_PROJECT=infinity-x-one-systems
ENV FIRESTORE_COLLECTION=mcp_memory
ENV SAFE_MODE=true
# Uvicorn for production
CMD ["python", "-m", "uvicorn", "omni_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
