# Autonomy Stack - Complete Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git
- 8GB RAM minimum (16GB recommended)
- 50GB disk space

### Local Development Setup

#### 1. Clone and Configure
```bash
cd c:\AI\repos\mcp
cp .env.template .env
# Edit .env with your API keys
```

#### 2. Install Local Dependencies (Optional for development)
```bash
pip install -r requirements_autonomy_stack.txt
```

#### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api_gateway

# Check status
docker-compose ps
```

#### 4. Verify Services
```bash
# Health check
curl http://localhost:8000/health

# Agent list
curl -H "X-API-Key: INVESTORS-DEMO-KEY-2025" http://localhost:8000/autonomy/agents

# Dashboard
open http://localhost:8000
```

---

## 📦 Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Main FastAPI endpoint |
| Flower (Celery UI) | 5555 | Task monitoring |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Metrics dashboard |
| Redis | 6379 | Message broker |
| PostgreSQL | 5432 | Metadata store |
| ChromaDB | 8001 | Vector database |

---

## 🤖 Agent System

### Four Role-Based Agents

#### 1. **Visionary** 🔮
- **Role**: Long-term vision and emerging opportunities
- **Endpoint**: `POST /autonomy/agents/visionary/execute`
- **Input**: Strategic question or objective
- **Output**: Vision, opportunities, timeframes

#### 2. **Strategist** 🎯
- **Role**: Develops actionable strategies
- **Endpoint**: `POST /autonomy/agents/strategist/execute`
- **Input**: Vision or goal
- **Output**: Phased plans, resources, risks

#### 3. **Builder** 🔨
- **Role**: Implements and builds solutions
- **Endpoint**: `POST /autonomy/agents/builder/execute`
- **Input**: Strategy or spec
- **Output**: Implementation, components, deployment plan

#### 4. **Critic** 💭
- **Role**: Validates, challenges, identifies risks
- **Endpoint**: `POST /autonomy/agents/critic/execute`
- **Input**: Proposal or implementation
- **Output**: Assessment, strengths, weaknesses, recommendations

---

## 📡 REST API Endpoints

### Agent Management
```
GET  /autonomy/agents              # List available agents
POST /autonomy/agents/{role}/execute  # Execute agent task
GET  /autonomy/agents/stats        # Agent statistics
```

### Task Queue
```
POST   /autonomy/tasks/submit              # Submit async task
GET    /autonomy/tasks/{task_id}/status    # Check task status
DELETE /autonomy/tasks/{task_id}           # Cancel task
GET    /autonomy/tasks/queue/stats         # Queue statistics
```

### Memory Management
```
POST /autonomy/memory/store        # Store memory entry
POST /autonomy/memory/retrieve     # Semantic search
GET  /autonomy/memory/stats        # Memory statistics
DELETE /autonomy/memory/{collection} # Clear collection
```

### Pipeline Execution
```
POST /autonomy/pipeline/execute    # Execute multi-agent pipeline
```

### Models
```
POST /autonomy/models/experiment   # Create model experiment
GET  /autonomy/models/experiments  # List experiments
```

---

## 🔐 Security

### API Key Management
```bash
# Set in .env
MCP_API_KEY=your-secure-key

# Use in requests
curl -H "X-API-Key: your-secure-key" http://localhost:8000/autonomy/agents
```

### Safe Mode
- Enabled by default: `SAFE_MODE=true`
- No external OS control (mouse, keyboard)
- Only authorized domains for browser automation
- Firestore audit logging

### Environment Variables
```env
# API Keys
OPENAI_API_KEY=sk-...
MCP_API_KEY=INVESTORS-DEMO-KEY-2025

# Services
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/db

# Security
SAFE_MODE=true
GOVERNANCE_LEVEL=MEDIUM
```

---

## 💾 Memory System

### Vector Storage (ChromaDB)
```python
# Store memory
POST /autonomy/memory/store
{
    "content": "Key insight about system",
    "metadata": {"type": "insight", "source": "visionary"},
    "agent_role": "visionary"
}

# Retrieve by similarity
POST /autonomy/memory/retrieve
{
    "query": "What are emerging technologies?",
    "collection": "shared",
    "n_results": 5
}
```

### Collections
- `visionary_memory` - Visionary agent context
- `strategist_memory` - Strategist context
- `builder_memory` - Builder context
- `critic_memory` - Critic context
- `shared_memory` - Global context

---

## ⚙️ Task Queue (Celery)

### Submit Task
```bash
curl -X POST http://localhost:8000/autonomy/tasks/submit \
  -H "X-API-Key: INVESTORS-DEMO-KEY-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analysis",
    "agent_role": "visionary",
    "objective": "What will disrupt tech in 5 years?",
    "priority": 7,
    "timeout_seconds": 300
  }'
```

### Check Status
```bash
curl http://localhost:8000/autonomy/tasks/{task_id}/status \
  -H "X-API-Key: INVESTORS-DEMO-KEY-2025"
```

### Monitor Queue
```bash
# Flower UI
open http://localhost:5555
```

---

## 🔄 Pipeline Orchestration

### Execute Multi-Agent Pipeline
```bash
curl -X POST http://localhost:8000/autonomy/pipeline/execute \
  -H "X-API-Key: INVESTORS-DEMO-KEY-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "strategy_development",
    "agents": ["visionary", "strategist", "builder", "critic"],
    "objectives": [
      "What emerging AI trends matter?",
      "How should we adapt?",
      "What should we build?",
      "Is this realistic?"
    ]
  }'
```

---

## 📊 Monitoring

### Prometheus Metrics
```
http://localhost:9090
```

### Grafana Dashboard
```
http://localhost:3000
- Username: admin
- Password: [see .env GRAFANA_PASSWORD]
```

### Celery Monitoring
```
http://localhost:5555
```

---

## 🧠 VS Code Integration

### Agent Panel
```
GET /vscode/agents
```
Lists all agents, statistics, and memory usage

### Tasks Panel
```
GET /vscode/tasks
```
Shows active, scheduled, and reserved tasks

### Memory Panel
```
GET /vscode/memory
```
Displays memory collection statistics

### Quick Execute
```
POST /vscode/execute?agent=visionary&objective=...
```
Execute directly from VS Code

### Pipeline Visualization
```
GET /vscode/pipeline
```
Pipeline structure and available agents

---

## 🐍 Model Experimentation

### PyTorch Support
```python
from autonomy_stack.models import ModelExperimentConfig

config = ModelExperimentConfig(
    name="sentiment_classifier",
    model_type="pytorch",
    task="classification",
    parameters={"layers": 3, "dropout": 0.2},
    datasets=["train.csv", "test.csv"],
    metrics=["accuracy", "f1", "precision"],
    batch_size=32,
    epochs=10
)
```

### TensorFlow Support
```python
config = ModelExperimentConfig(
    name="nlp_model",
    model_type="tensorflow",
    task="sequence_labeling",
    parameters={"units": 256, "dropout": 0.3},
    datasets=["tagged_data.json"],
    metrics=["loss", "accuracy"],
    batch_size=64,
    epochs=20
)
```

---

## 🌐 Browser Automation (Playwright)

### Constraints
- Headless mode only
- Local/authorized domains only
- Configurable timeout (5 minutes default)
- No system-level mouse/keyboard control

### Configuration
```env
HEADLESS_BROWSER=true
ALLOWED_DOMAINS=localhost,127.0.0.1,example.com
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=false
```

---

## 📝 Logging

### Log Locations
```
./logs/gateway.log        # API Gateway logs
./logs/celery_worker.log  # Worker logs
./logs/celery_beat.log    # Scheduler logs
```

### Log Level
```env
LOG_LEVEL=info  # debug, info, warning, error, critical
```

---

## 🧹 Maintenance

### Clean Up Docker
```bash
# Stop all services
docker-compose down

# Remove volumes (data loss!)
docker-compose down -v

# View logs
docker-compose logs --tail=100 -f api_gateway
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U autonomy_user -d autonomy_db

# View Redis data
docker-compose exec redis redis-cli
```

### Memory Cleanup
```bash
# Clear ChromaDB collection
POST /autonomy/memory/shared

# Export memory
GET /autonomy/memory/shared/export
```

---

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
docker-compose --env-file .env -e GATEWAY_PORT=8001 up
```

### Redis Connection Failed
```bash
# Check Redis status
docker-compose ps redis

# Restart Redis
docker-compose restart redis
```

### Memory Issues
```bash
# Monitor Docker resources
docker stats

# Increase memory limits in docker-compose.yml
services:
  api_gateway:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Celery Workers Not Processing
```bash
# Check worker status
docker-compose logs celery_worker

# Restart workers
docker-compose restart celery_worker celery_beat
```

---

## 📚 Example Workflows

### Workflow 1: Vision → Strategy → Implementation
```python
import requests

api_key = "INVESTORS-DEMO-KEY-2025"
base_url = "http://localhost:8000"

# Step 1: Visionary generates vision
vision = requests.post(
    f"{base_url}/autonomy/agents/visionary/execute",
    json={"objective": "What's next for AI?"},
    headers={"X-API-Key": api_key}
).json()

# Step 2: Strategist develops strategy
strategy = requests.post(
    f"{base_url}/autonomy/agents/strategist/execute",
    json={"objective": vision["result"]["vision"]},
    headers={"X-API-Key": api_key}
).json()

# Step 3: Builder implements
implementation = requests.post(
    f"{base_url}/autonomy/agents/builder/execute",
    json={"objective": strategy["result"]["phases"][0]["name"]},
    headers={"X-API-Key": api_key}
).json()

# Step 4: Critic validates
critique = requests.post(
    f"{base_url}/autonomy/agents/critic/execute",
    json={"objective": "Review the implementation"},
    headers={"X-API-Key": api_key}
).json()
```

### Workflow 2: Semantic Memory Search
```python
# Store insights
requests.post(
    f"{base_url}/autonomy/memory/store",
    json={
        "content": "AI will reshape knowledge work",
        "metadata": {"category": "emerging_tech"},
        "agent_role": "visionary"
    },
    headers={"X-API-Key": api_key}
)

# Search similar
results = requests.post(
    f"{base_url}/autonomy/memory/retrieve",
    json={"query": "future of AI"},
    headers={"X-API-Key": api_key}
).json()
```

---

## 📞 Support

### Documentation
- API Docs: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Debugging
- Enable debug mode: `DEBUG=true` in .env
- Check logs: `docker-compose logs -f`
- Monitor Flower: `http://localhost:5555`

---

## 🎯 Next Steps

1. **Customize Agents**: Edit `agent_factory.py` to add LangChain integration
2. **Add Memory**: Configure embeddings model for ChromaDB
3. **Extend Pipeline**: Create complex multi-agent workflows
4. **Monitor**: Set up Grafana dashboards
5. **Deploy**: Push to Cloud Run or Kubernetes

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Status**: Production Ready ✓
