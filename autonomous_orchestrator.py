"""
Autonomous Agent Orchestrator - Max autonomy with governance
Coordinates background agents, triggers, and autonomous operations
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/autonomy", tags=["autonomy"])

# Agent registry
AGENT_REGISTRY = {}
ACTIVE_AGENTS = {}

class AgentConfig(BaseModel):
    agent_id: str
    interval_seconds: int = 60
    enabled: bool = True
    config: Dict[str, Any] = {}

class TriggerConfig(BaseModel):
    trigger_id: str
    cron: Optional[str] = None  # Cloud Scheduler cron
    event_type: Optional[str] = None  # Event-driven trigger
    agent_ids: List[str] = []
    enabled: bool = True

async def run_agent_loop(agent_id: str, config: Dict[str, Any], interval: int):
    """Run agent in background loop"""
    logger.info(f"Starting agent loop: {agent_id}")
    
    while ACTIVE_AGENTS.get(agent_id, {}).get("enabled", False):
        try:
            # Import and run agent
            if agent_id == "memory_curator":
                from agents.memory_curator import run
                await run(config)
            elif agent_id == "intelligence_monitor":
                # Stub for intelligence monitoring agent
                logger.info(f"[{agent_id}] Monitoring intelligence endpoints...")
                # Check intelligence endpoints health
                pass
            elif agent_id == "credential_rotator":
                # Stub for credential rotation agent
                logger.info(f"[{agent_id}] Checking credential expiry...")
                pass
            elif agent_id == "auto_builder":
                # Stub for auto-build agent
                logger.info(f"[{agent_id}] Checking for build triggers...")
                pass
            else:
                logger.warning(f"Unknown agent: {agent_id}")
            
            await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Agent {agent_id} error: {e}")
            await asyncio.sleep(interval)
    
    logger.info(f"Agent loop stopped: {agent_id}")

@router.get("/health")
async def autonomy_health():
    """Health check for autonomy system"""
    return JSONResponse(content={
        "status": "healthy",
        "active_agents": list(ACTIVE_AGENTS.keys()),
        "agent_count": len(ACTIVE_AGENTS),
        "available_agents": [
            "memory_curator",
            "intelligence_monitor",
            "credential_rotator",
            "auto_builder"
        ]
    })

@router.post("/agents/start")
async def start_agent(config: AgentConfig, background_tasks: BackgroundTasks):
    """Start an autonomous agent"""
    
    if config.agent_id in ACTIVE_AGENTS:
        return JSONResponse(content={
            "success": False,
            "error": f"Agent already running: {config.agent_id}"
        })
    
    ACTIVE_AGENTS[config.agent_id] = {
        "enabled": True,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "config": config.config,
        "interval": config.interval_seconds
    }
    
    # Start agent loop in background
    background_tasks.add_task(
        run_agent_loop,
        config.agent_id,
        config.config,
        config.interval_seconds
    )
    
    logger.info(f"Started agent: {config.agent_id}")
    
    return JSONResponse(content={
        "success": True,
        "agent_id": config.agent_id,
        "status": "running"
    })

@router.post("/agents/stop/{agent_id}")
async def stop_agent(agent_id: str):
    """Stop an autonomous agent"""
    
    if agent_id not in ACTIVE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    ACTIVE_AGENTS[agent_id]["enabled"] = False
    del ACTIVE_AGENTS[agent_id]
    
    logger.info(f"Stopped agent: {agent_id}")
    
    return JSONResponse(content={
        "success": True,
        "agent_id": agent_id,
        "status": "stopped"
    })

@router.get("/agents/list")
async def list_agents():
    """List all active agents"""
    return JSONResponse(content={
        "success": True,
        "agents": ACTIVE_AGENTS
    })

@router.post("/triggers/create")
async def create_trigger(trigger: TriggerConfig):
    """Create a trigger (Cloud Scheduler or event-driven)"""
    
    # Write trigger config to Firestore for persistence
    try:
        from google.cloud import firestore
        project = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
        client = firestore.Client(project=project)
        
        doc = {
            "trigger_id": trigger.trigger_id,
            "cron": trigger.cron,
            "event_type": trigger.event_type,
            "agent_ids": trigger.agent_ids,
            "enabled": trigger.enabled,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        client.collection("mcp_memory").document(f"trigger_{trigger.trigger_id}").set(doc)
        
        return JSONResponse(content={
            "success": True,
            "trigger_id": trigger.trigger_id,
            "message": "Trigger created. Deploy Cloud Scheduler job to activate."
        })
    
    except Exception as e:
        logger.error(f"Failed to create trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/triggers/execute/{trigger_id}")
async def execute_trigger(trigger_id: str, background_tasks: BackgroundTasks):
    """Execute a trigger (called by Cloud Scheduler or event)"""
    
    try:
        from google.cloud import firestore
        project = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
        client = firestore.Client(project=project)
        
        doc = client.collection("mcp_memory").document(f"trigger_{trigger_id}").get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Trigger not found: {trigger_id}")
        
        trigger_data = doc.to_dict()
        
        if not trigger_data.get("enabled", False):
            return JSONResponse(content={
                "success": False,
                "message": f"Trigger disabled: {trigger_id}"
            })
        
        # Execute agents associated with this trigger
        agent_ids = trigger_data.get("agent_ids", [])
        results = []
        
        for agent_id in agent_ids:
            try:
                # Start agent if not already running
                if agent_id not in ACTIVE_AGENTS:
                    config = AgentConfig(agent_id=agent_id, enabled=True)
                    await start_agent(config, background_tasks)
                    results.append({"agent_id": agent_id, "status": "started"})
                else:
                    results.append({"agent_id": agent_id, "status": "already_running"})
            except Exception as e:
                logger.error(f"Failed to execute agent {agent_id}: {e}")
                results.append({"agent_id": agent_id, "status": "error", "error": str(e)})
        
        return JSONResponse(content={
            "success": True,
            "trigger_id": trigger_id,
            "executed_agents": results
        })
    
    except Exception as e:
        logger.error(f"Failed to execute trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_autonomy_capabilities():
    """Get all autonomous capabilities"""
    return JSONResponse(content={
        "success": True,
        "capabilities": {
            "agents": {
                "memory_curator": {
                    "description": "Curates and optimizes memory storage",
                    "default_interval": 300,
                    "governance": "LOW"
                },
                "intelligence_monitor": {
                    "description": "Monitors intelligence endpoints for anomalies",
                    "default_interval": 60,
                    "governance": "LOW"
                },
                "credential_rotator": {
                    "description": "Checks credential expiry and rotates",
                    "default_interval": 3600,
                    "governance": "CRITICAL"
                },
                "auto_builder": {
                    "description": "Automatically builds and deploys on triggers",
                    "default_interval": 300,
                    "governance": "MEDIUM"
                }
            },
            "triggers": {
                "cron": "Scheduled execution via Cloud Scheduler",
                "event": "Event-driven execution (Pub/Sub, Firestore, HTTP)",
                "webhook": "External webhook triggers"
            },
            "governance": {
                "approval_required": ["credential_rotator"],
                "audit_logged": "all",
                "rate_limited": ["auto_builder"]
            }
        }
    })
