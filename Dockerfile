FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT 8080
EXPOSE 8080
CMD ["python", "http_adapter.py"]
FROM alpine:latest
LABEL Name=mcp Version=0.0.1
RUN apk add --no-cache fortune
ENTRYPOINT ["sh", "-c", "fortune -a | cat"]
