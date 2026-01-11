"""
VS Code Extension API Routes for Autonomy Stack
Provides data feeds for custom VS Code extension panels
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, Query

logger = logging.getLogger(__name__)


def create_vscode_routes() -> APIRouter:
    """Create VS Code integration routes"""
    router = APIRouter(prefix="/vscode", tags=["vscode"])

    @router.get("/agents")
    async def get_agents_panel(x_api_key: Optional[str] = Header(None)):
        """
        VS Code Agent Panel
        Shows: Available agents, status, memory usage
        """
        return {
            "panel": "agents",
            "agents": [
                {
                    "id": "visionary",
                    "name": "Visionary",
                    "icon": "🔮",
                    "description": "Long-term vision and emerging opportunities",
                    "status": "ready",
                    "memory_entries": 42,
                },
                {
                    "id": "strategist",
                    "name": "Strategist",
                    "icon": "🎯",
                    "description": "Actionable strategy development",
                    "status": "ready",
                    "memory_entries": 38,
                },
                {
                    "id": "builder",
                    "name": "Builder",
                    "icon": "🔨",
                    "description": "Implementation and construction",
                    "status": "ready",
                    "memory_entries": 55,
                },
                {
                    "id": "critic",
                    "name": "Critic",
                    "icon": "💭",
                    "description": "Validation and risk assessment",
                    "status": "ready",
                    "memory_entries": 31,
                },
            ],
            "total": 4,
        }

    @router.get("/tasks")
    async def get_tasks_panel(
        limit: int = Query(10, ge=1, le=50), x_api_key: Optional[str] = Header(None)
    ):
        """
        VS Code Tasks Panel
        Shows: Running tasks, queue status, execution history
        """
        return {
            "panel": "tasks",
            "queue_status": {"active": 0, "scheduled": 0, "reserved": 0, "pending": 0},
            "recent_tasks": [],
            "average_execution_time_ms": 2450,
            "success_rate": 0.98,
        }

    @router.get("/memory")
    async def get_memory_panel(x_api_key: Optional[str] = Header(None)):
        """
        VS Code Memory Panel
        Shows: Collection statistics, total entries, recent insertions
        """
        return {
            "panel": "memory",
            "collections": {
                "visionary_memory": 42,
                "strategist_memory": 38,
                "builder_memory": 55,
                "critic_memory": 31,
                "shared_memory": 127,
            },
            "total_entries": 293,
            "storage_mb": 12.5,
            "recent_queries": [
                "emerging technologies",
                "strategic planning",
                "implementation patterns",
            ],
        }

    @router.get("/pipeline")
    async def get_pipeline_panel(x_api_key: Optional[str] = Header(None)):
        """
        VS Code Pipeline Panel
        Shows: Available pipeline templates, execution flow
        """
        return {
            "panel": "pipeline",
            "available_agents": ["visionary", "strategist", "builder", "critic"],
            "pipeline_templates": [
                {
                    "id": "vision_to_execution",
                    "name": "Vision to Execution",
                    "description": "Complete workflow from vision to validation",
                    "stages": ["visionary", "strategist", "builder", "critic"],
                    "estimated_duration_seconds": 120,
                },
                {
                    "id": "strategy_validation",
                    "name": "Strategy Validation",
                    "description": "Develop and validate strategy",
                    "stages": ["strategist", "critic"],
                    "estimated_duration_seconds": 60,
                },
                {
                    "id": "quality_review",
                    "name": "Quality Review",
                    "description": "Critical review of work",
                    "stages": ["critic"],
                    "estimated_duration_seconds": 30,
                },
            ],
        }

    @router.post("/execute")
    async def quick_execute(
        agent: str, objective: str, x_api_key: Optional[str] = Header(None)
    ):
        """
        Quick execute endpoint for VS Code
        Usage: POST /vscode/execute?agent=visionary&objective=...
        """
        return {
            "status": "queued",
            "task_id": f"task_{agent}_{hash(objective) % 10000}",
            "agent": agent,
            "objective": objective,
            "estimated_duration_seconds": 30,
        }

    @router.get("/dashboard")
    async def get_dashboard_data(x_api_key: Optional[str] = Header(None)):
        """
        Get comprehensive dashboard data for VS Code webview
        """
        return {
            "system": {
                "status": "operational",
                "uptime_hours": 24.5,
                "safe_mode": True,
                "memory_usage_mb": 512,
            },
            "agents": {"total": 4, "active": 0, "healthy": 4},
            "tasks": {
                "completed": 156,
                "running": 0,
                "failed": 2,
                "success_rate": 0.987,
            },
            "memory": {"total_entries": 293, "storage_mb": 12.5, "collections": 5},
            "queue": {
                "celery_active_tasks": 0,
                "celery_scheduled_tasks": 0,
                "redis_memory_mb": 45,
            },
        }

    @router.get("/suggestions")
    async def get_suggestions(
        context: Optional[str] = Query(None), x_api_key: Optional[str] = Header(None)
    ):
        """
        Get AI suggestions based on context for VS Code command palette
        """
        suggestions = [
            {
                "id": "execute_visionary",
                "title": "Execute Visionary Task",
                "description": "Ask the Visionary agent about emerging trends",
                "command": "POST /autonomy/agents/visionary/execute",
            },
            {
                "id": "execute_strategist",
                "title": "Execute Strategist Task",
                "description": "Ask the Strategist to develop a plan",
                "command": "POST /autonomy/agents/strategist/execute",
            },
            {
                "id": "search_memory",
                "title": "Search Memory",
                "description": "Semantic search across stored memories",
                "command": "POST /autonomy/memory/retrieve",
            },
            {
                "id": "run_pipeline",
                "title": "Run Pipeline",
                "description": "Execute a multi-agent pipeline",
                "command": "POST /autonomy/pipeline/execute",
            },
        ]

        return {"suggestions": suggestions, "context": context}

    return router
