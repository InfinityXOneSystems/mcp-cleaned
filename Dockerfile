FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Default to running the Omni Gateway (59 MCP tools + Cockpit)
ENV SERVICE_MODE=single
ENV GATEWAY_PORT=8000
CMD ["python", "omni_gateway.py"]
