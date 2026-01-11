"""
Autonomy Gateway - Main FastAPI application integrating all autonomy stack components
Serves as the central hub for AI-autonomy orchestration with VS Code integration
"""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Autonomy stack imports
from autonomy_stack.agent_factory import AgentFactory
from autonomy_stack.endpoints import create_routes
from autonomy_stack.memory_layer import MemoryLayer
from autonomy_stack.security import SecurityManager, get_security_manager
from autonomy_stack.task_queue import TaskQueue, celery_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ===== APPLICATION SETUP =====
app = FastAPI(
    title="Autonomy Stack Gateway",
    description="AI-autonomy orchestration platform with multi-agent reasoning",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DEPENDENCY INJECTION =====
_agent_factory: Optional[AgentFactory] = None
_task_queue: Optional[TaskQueue] = None
_memory_layer: Optional[MemoryLayer] = None
_security: Optional[SecurityManager] = None


def get_components():
    """Initialize and cache components"""
    global _agent_factory, _task_queue, _memory_layer, _security

    if _security is None:
        _security = get_security_manager()
        logger.info("✓ Security manager initialized")

    if _memory_layer is None:
        _memory_layer = MemoryLayer(persist_dir="./data/chroma")
        logger.info("✓ Memory layer initialized")

    if _agent_factory is None:
        _agent_factory = AgentFactory(memory=_memory_layer)
        logger.info("✓ Agent factory initialized")

    if _task_queue is None:
        _task_queue = TaskQueue(celery_app)
        logger.info("✓ Task queue initialized")

    return _agent_factory, _task_queue, _memory_layer, _security


# ===== ROOT ENDPOINTS =====
@app.get("/")
async def root():
    """Root endpoint - serves dashboard"""
    return HTMLResponse(get_dashboard_html())


@app.get("/health")
async def health():
    """Health check"""
    factory, queue, memory, security = get_components()
    return {
        "status": "healthy",
        "safe_mode": security.is_safe_mode(),
        "memory_stats": memory.get_memory_stats(),
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Autonomy Gateway starting...")
    try:
        factory, queue, memory, security = get_components()
        logger.info("✓ All components initialized")
        logger.info(f"✓ Safe mode: {security.is_safe_mode()}")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("💤 Autonomy Gateway shutting down...")


# ===== INCLUDE AUTONOMY ROUTES =====
factory, queue, memory, security = get_components()
routes = create_routes(factory, queue, memory)
app.include_router(routes)


# ===== VS CODE INTEGRATION ENDPOINTS =====
@app.get("/vscode/agents")
async def vscode_agents():
    """VS Code agent panel data"""
    factory, _, _, _ = get_components()
    stats = factory.get_agent_stats()
    return {
        "agents": stats["agents"],
        "total": stats["total_agents"],
        "memory": stats["memory_stats"],
    }


@app.get("/vscode/tasks")
async def vscode_tasks(limit: int = 10):
    """VS Code tasks panel data"""
    _, queue, _, _ = get_components()
    stats = queue.get_queue_stats()
    return {
        "active": stats.get("active", {}),
        "scheduled": stats.get("scheduled", {}),
        "reserved": stats.get("reserved", {}),
    }


@app.get("/vscode/memory")
async def vscode_memory():
    """VS Code memory panel data"""
    _, _, memory, _ = get_components()
    stats = memory.get_memory_stats()
    return {
        "collections": stats,
        "total": sum(stats.values()),
    }


@app.get("/vscode/pipeline")
async def vscode_pipeline():
    """VS Code pipeline visualization data"""
    return {
        "pipelines": [],
        "available_agents": ["visionary", "strategist", "builder", "critic"],
        "status": "ready",
    }


@app.post("/vscode/execute")
async def vscode_execute(agent: str, objective: str):
    """Quick execute from VS Code"""
    factory, _, _, _ = get_components()
    try:
        result = await factory.execute_task(agent, objective)
        return result.dict()
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# ===== DASHBOARD HTML =====
def get_dashboard_html() -> str:
    """Return dashboard HTML for browser"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Autonomy Stack Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: #fff;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .subtitle {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 12px;
                padding: 25px;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                background: rgba(255,255,255,0.15);
                border-color: rgba(255,255,255,0.4);
                transform: translateY(-5px);
            }
            
            .card h2 {
                font-size: 1.5em;
                margin-bottom: 15px;
                color: #4dd0e1;
            }
            
            .card-content {
                line-height: 1.6;
            }
            
            .status {
                display: inline-block;
                background: #4caf50;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 500;
            }
            
            .agents-list {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 15px;
            }
            
            .agent-badge {
                background: rgba(77, 208, 225, 0.2);
                border: 1px solid #4dd0e1;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
            }
            
            .endpoint-list {
                list-style: none;
                padding: 0;
            }
            
            .endpoint-list li {
                padding: 10px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }
            
            .endpoint-list li:last-child {
                border-bottom: none;
            }
            
            .endpoint-method {
                color: #4dd0e1;
                font-weight: bold;
                margin-right: 10px;
            }
            
            .endpoint-path {
                color: #fff;
            }
            
            button {
                background: linear-gradient(135deg, #4dd0e1 0%, #26a69a 100%);
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
                margin-top: 15px;
            }
            
            button:hover {
                transform: scale(1.05);
                box-shadow: 0 8px 16px rgba(77, 208, 225, 0.4);
            }
            
            .footer {
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid rgba(255,255,255,0.2);
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🤖 Autonomy Stack</h1>
                <p class="subtitle">Multi-agent AI orchestration platform</p>
            </header>
            
            <div class="grid">
                <div class="card">
                    <h2>📊 System Status</h2>
                    <div class="card-content">
                        <p>Status: <span class="status">OPERATIONAL</span></p>
                        <p>Mode: Safe (Local execution)</p>
                        <p>Memory: ChromaDB + Firestore</p>
                        <p>Queue: Celery + Redis</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🤖 Available Agents</h2>
                    <div class="card-content">
                        <p>Four role-based agents:</p>
                        <div class="agents-list">
                            <div class="agent-badge">🔮 Visionary</div>
                            <div class="agent-badge">🎯 Strategist</div>
                            <div class="agent-badge">🔨 Builder</div>
                            <div class="agent-badge">💭 Critic</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚙️ Core Services</h2>
                    <div class="card-content">
                        <ul class="endpoint-list">
                            <li><span class="endpoint-method">GET</span> <span class="endpoint-path">/autonomy/health</span></li>
                            <li><span class="endpoint-method">GET</span> <span class="endpoint-path">/autonomy/agents</span></li>
                            <li><span class="endpoint-method">POST</span> <span class="endpoint-path">/autonomy/tasks/submit</span></li>
                            <li><span class="endpoint-method">GET</span> <span class="endpoint-path">/autonomy/memory/stats</span></li>
                            <li><span class="endpoint-method">POST</span> <span class="endpoint-path">/autonomy/pipeline/execute</span></li>
                        </ul>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔧 Local Stacks</h2>
                    <div class="card-content">
                        <p>✓ FastAPI Gateway (8000)</p>
                        <p>✓ Celery Worker (async tasks)</p>
                        <p>✓ Redis (messaging)</p>
                        <p>✓ ChromaDB (vector memory)</p>
                        <p>✓ PostgreSQL (metadata)</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📚 Features</h2>
                    <div class="card-content">
                        <p>✓ Multi-agent reasoning</p>
                        <p>✓ Semantic memory search</p>
                        <p>✓ Pipeline orchestration</p>
                        <p>✓ PyTorch/TensorFlow support</p>
                        <p>✓ Secure API keys</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎯 Quick Start</h2>
                    <div class="card-content">
                        <p>1. Execute agent task</p>
                        <p>2. Submit to queue</p>
                        <p>3. Query memory</p>
                        <p>4. Run pipeline</p>
                        <button onclick="alert('See /docs for full API documentation')">📖 API Docs</button>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>Autonomy Stack v1.0 | Local AI-autonomy orchestration platform</p>
                <p>Visit <code>/docs</code> for interactive API documentation</p>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
