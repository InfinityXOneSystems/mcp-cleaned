# 🤖 Autonomy Stack - Local AI-Autonomy Platform

> **Production-Ready Multi-Agent AI Orchestration Framework**  
> Fully containerized, secure, and designed for autonomous task execution within your local environment.

---

## 🎯 Overview

The **Autonomy Stack** is a comprehensive platform for building and orchestrating multi-agent AI systems. It combines:

- **FastAPI Gateway** - RESTful API for agent management and task orchestration
- **4 Role-Based Agents** - Visionary, Strategist, Builder, Critic
- **Celery + Redis** - Async task queuing and distributed execution
- **ChromaDB** - Vector memory for semantic context persistence
- **PyTorch + TensorFlow** - Model experimentation framework
- **Playwright** - Headless browser automation (local/authorized domains only)
- **Docker Compose** - Complete local stack with 10 services
- **VS Code Integration** - Custom panels and quick commands

All automation **stays local** - no external system control, no mouse/keyboard manipulation.

---

## ⚡ Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- 8GB RAM minimum
- 50GB disk space
```

### 2. Setup
```bash
cd c:\AI\repos\mcp
cp .env.template .env
# Edit .env with your API keys
docker-compose up -d
```

### 3. Verify
```bash
# Health check
curl http://localhost:8000/health

# List agents
curl -H "X-API-Key: INVESTORS-DEMO-KEY-2025" http://localhost:8000/autonomy/agents

# Dashboard
open http://localhost:8000
```

### 4. Execute First Task
```bash
curl -X POST http://localhost:8000/autonomy/agents/visionary/execute \
  -H "X-API-Key: INVESTORS-DEMO-KEY-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "What will disrupt technology in 5 years?"
  }'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Gateway (8000)               │
├─────────────────────────────────────────────────────────┤
│  /autonomy/agents      /autonomy/tasks                  │
│  /autonomy/memory      /autonomy/pipeline               │
│  /autonomy/models      /vscode/*                        │
└────────┬─────────────────────────────┬──────────────────┘
         │                             │
    ┌────▼────────────────┐    ┌──────▼──────────────┐
    │  Agent Factory      │    │  Task Queue        │
    │  ├─ Visionary 🔮    │    │  (Celery + Redis)  │
    │  ├─ Strategist 🎯   │    │  ├─ Workers        │
    │  ├─ Builder 🔨      │    │  ├─ Scheduler      │
    │  └─ Critic 💭       │    │  └─ Monitoring     │
    └────┬────────────────┘    └──────┬──────────────┘
         │                            │
    ┌────▼────────────────────────────▼──────┐
    │       Memory Layer (ChromaDB)          │
    │  ├─ Visionary Memory                   │
    │  ├─ Strategist Memory                  │
    │  ├─ Builder Memory                     │
    │  ├─ Critic Memory                      │
    │  └─ Shared Memory                      │
    └───────────────────────────────────────┘
```

---

## 🚀 Services

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| API Gateway | 8000 | FastAPI endpoints | ✓ |
| Flower | 5555 | Task monitoring | ✓ |
| Prometheus | 9090 | Metrics collection | ✓ |
| Grafana | 3000 | Dashboards | ✓ |
| Redis | 6379 | Message broker | ✓ |
| PostgreSQL | 5432 | Metadata store | ✓ |
| ChromaDB | 8001 | Vector DB | ✓ |

---

## 🤖 Agents

### Visionary 🔮
**Long-term vision and emerging opportunities**
```bash
POST /autonomy/agents/visionary/execute
{
  "objective": "What will disrupt the industry?"
}
```
- Identifies emerging trends
- Speculates on futures
- Generates opportunities
- Confidence: 0.82

### Strategist 🎯
**Actionable strategy development**
```bash
POST /autonomy/agents/strategist/execute
{
  "objective": "How do we capitalize on emerging trends?"
}
```
- Creates phased plans
- Allocates resources
- Identifies risks
- Confidence: 0.78

### Builder 🔨
**Implementation and construction**
```bash
POST /autonomy/agents/builder/execute
{
  "objective": "Build the first phase of the plan"
}
```
- Implements strategies
- Creates artifacts
- Deploys solutions
- Confidence: 0.88

### Critic 💭
**Validation and risk assessment**
```bash
POST /autonomy/agents/critic/execute
{
  "objective": "Validate the implementation"
}
```
- Identifies weaknesses
- Assesses risks
- Validates claims
- Confidence: 0.85

---

## 📡 REST API

### Agent Management
```
GET    /autonomy/agents              # List agents
POST   /autonomy/agents/{role}/execute
GET    /autonomy/agents/stats        # Statistics
```

### Task Queue
```
POST   /autonomy/tasks/submit        # Submit task
GET    /autonomy/tasks/{id}/status   # Check status
DELETE /autonomy/tasks/{id}          # Cancel
GET    /autonomy/tasks/queue/stats   # Queue stats
```

### Memory
```
POST   /autonomy/memory/store        # Store entry
POST   /autonomy/memory/retrieve     # Search
GET    /autonomy/memory/stats        # Statistics
DELETE /autonomy/memory/{collection} # Clear
```

### Pipeline
```
POST   /autonomy/pipeline/execute    # Run multi-agent pipeline
```

### Models
```
POST   /autonomy/models/experiment   # Create experiment
GET    /autonomy/models/experiments  # List experiments
```

### VS Code
```
GET    /vscode/agents                # Agent panel
GET    /vscode/tasks                 # Tasks panel
GET    /vscode/memory                # Memory panel
GET    /vscode/pipeline              # Pipeline viz
POST   /vscode/execute               # Quick execute
GET    /vscode/dashboard             # Full dashboard
GET    /vscode/suggestions           # AI suggestions
```

---

## 💾 Memory System

### Vector Storage
```python
# Store insight
POST /autonomy/memory/store
{
  "content": "AI will reshape knowledge work",
  "metadata": {"category": "insights"},
  "agent_role": "visionary"
}

# Search similar
POST /autonomy/memory/retrieve
{
  "query": "future of AI",
  "n_results": 5
}
```

### Collections
- `visionary_memory` - Strategic insights
- `strategist_memory` - Plans and strategies
- `builder_memory` - Implementation artifacts
- `critic_memory` - Validations and reviews
- `shared_memory` - Global context

---

## ⚙️ Configuration

### .env Template
```env
# Security
OPENAI_API_KEY=sk-...
MCP_API_KEY=INVESTORS-DEMO-KEY-2025
JWT_SECRET_KEY=...

# Services
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
DATABASE_URL=postgresql://user:pass@postgres/db

# Safety
SAFE_MODE=true
GOVERNANCE_LEVEL=MEDIUM
HEADLESS_BROWSER=true
ALLOWED_DOMAINS=localhost,127.0.0.1
```

---

## 🔐 Security

✅ **Enabled by Default**
- Safe mode (no external system control)
- API key validation (timing-safe comparison)
- Domain whitelist for browser automation
- Secure .env management
- Firestore audit logging
- JWT authentication ready

✅ **Constraints**
- No mouse/keyboard OS-level control
- No access to external accounts
- Headless browser only
- Local domain access only

---

## 📊 Monitoring

### Celery Flower UI
```
http://localhost:5555
```
- Task monitoring
- Worker status
- Queue statistics

### Prometheus Metrics
```
http://localhost:9090
```
- Application metrics
- Service health
- Performance tracking

### Grafana Dashboards
```
http://localhost:3000
```
- Real-time monitoring
- Custom dashboards
- Alert setup

---

## 🧪 Testing

```bash
# Run tests
pytest tests/test_autonomy_stack.py -v

# With coverage
pytest tests/test_autonomy_stack.py --cov=autonomy_stack

# Specific test
pytest tests/test_autonomy_stack.py::TestAgentFactory -v
```

---

## 🎮 Development

### CLI Commands
```bash
# Execute agent
python autonomy_cli.py execute-agent visionary "What's next?"

# Run pipeline
python autonomy_cli.py run-pipeline visionary strategist \
  --objectives "What's next?" "How to get there?"

# Manage memory
python autonomy_cli.py store-memory "Key insight" --agent visionary
python autonomy_cli.py search-memory "emerging technologies"
python autonomy_cli.py memory-stats

# Check status
python autonomy_cli.py agent-stats
python autonomy_cli.py security-check
```

---

## 📚 Workflows

### Vision → Execution Pipeline
```python
import requests

api_key = "INVESTORS-DEMO-KEY-2025"

# 1. Vision
vision = requests.post(
    "http://localhost:8000/autonomy/agents/visionary/execute",
    json={"objective": "What's next for AI?"},
    headers={"X-API-Key": api_key}
).json()

# 2. Strategy
strategy = requests.post(
    "http://localhost:8000/autonomy/agents/strategist/execute",
    json={"objective": vision["result"]["vision"]},
    headers={"X-API-Key": api_key}
).json()

# 3. Implementation
impl = requests.post(
    "http://localhost:8000/autonomy/agents/builder/execute",
    json={"objective": strategy["result"]["phases"][0]},
    headers={"X-API-Key": api_key}
).json()

# 4. Validation
critique = requests.post(
    "http://localhost:8000/autonomy/agents/critic/execute",
    json={"objective": "Review implementation"},
    headers={"X-API-Key": api_key}
).json()
```

### Memory + Intelligence Loop
```python
# Store insights
requests.post(
    "http://localhost:8000/autonomy/memory/store",
    json={
        "content": "Learned pattern: X leads to Y",
        "metadata": {"learning": True},
        "agent_role": "visionary"
    },
    headers={"X-API-Key": api_key}
)

# Retrieve for context
results = requests.post(
    "http://localhost:8000/autonomy/memory/retrieve",
    json={"query": "patterns in growth strategies"},
    headers={"X-API-Key": api_key}
).json()

# Use in future tasks
context = {"learned_patterns": results["results"]}
```

---

## 🧹 Maintenance

### Docker Operations
```bash
# Stop all services
docker-compose down

# View logs
docker-compose logs -f api_gateway
docker-compose logs --tail=100 celery_worker

# Rebuild
docker-compose build
docker-compose up -d

# Cleanup
docker-compose down -v  # Removes volumes!
```

### Database Management
```bash
# PostgreSQL CLI
docker-compose exec postgres psql -U autonomy_user -d autonomy_db

# Redis CLI
docker-compose exec redis redis-cli
```

### Memory Cleanup
```bash
# Clear memory collection
DELETE /autonomy/memory/shared

# Export before clearing
GET /autonomy/memory/shared
```

---

## 🐛 Troubleshooting

### Port Conflicts
```bash
# Find process on port 8000
lsof -ti:8000 | xargs kill -9

# Use different port
docker-compose --env-file .env -e GATEWAY_PORT=8001 up
```

### Redis Connection Failed
```bash
# Check Redis status
docker-compose ps redis

# Restart
docker-compose restart redis
```

### Memory Issues
```bash
# Monitor resources
docker stats

# Increase limits in docker-compose.yml
services:
  api_gateway:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Workers Not Processing
```bash
# Check worker logs
docker-compose logs celery_worker

# Restart
docker-compose restart celery_worker celery_beat
```

---

## 📖 Documentation

- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`
- **Deployment Guide**: `AUTONOMY_STACK_GUIDE.md`
- **Architecture**: See diagram above

---

## 🎯 Next Steps

1. **Customize Agents**
   - Integrate LangChain for LLM calls
   - Add domain-specific prompts
   - Implement memory retrieval in thinking

2. **Extend Memory**
   - Configure embedding models
   - Add semantic search weights
   - Implement memory eviction policies

3. **Build Pipelines**
   - Create domain-specific workflows
   - Add approval gates
   - Implement human feedback loops

4. **Monitor & Alert**
   - Set up Grafana dashboards
   - Create Prometheus alerts
   - Configure log aggregation

5. **Scale & Deploy**
   - Push to Kubernetes
   - Set up monitoring stack
   - Implement governance tiers

---

## 📦 Project Structure

```
autonomy_stack/
├── __init__.py
├── agent_factory.py      # Role-based agent implementations
├── memory_layer.py       # ChromaDB vector storage
├── task_queue.py         # Celery task orchestration
├── security.py           # API keys and encryption
├── models.py             # Pydantic data models
├── endpoints.py          # REST API routes
└── vscode_integration.py # VS Code panel data

docker-compose.yml        # Complete local stack
Dockerfile               # API Gateway image
Dockerfile.celery        # Celery worker image
requirements_autonomy_stack.txt

autonomy_gateway.py      # Main FastAPI application
autonomy_cli.py          # Development CLI
tests/                   # Test suite
```

---

## 📝 License

**Infinity X One Systems** - Internal Use

---

## 🤝 Support

- **Issues**: Check logs in `./logs/`
- **Monitoring**: Flower UI at `http://localhost:5555`
- **Metrics**: Prometheus at `http://localhost:9090`
- **API Docs**: `http://localhost:8000/docs`

---

**Version**: 1.0.0  
**Status**: Production Ready ✓  
**Last Updated**: December 2025
