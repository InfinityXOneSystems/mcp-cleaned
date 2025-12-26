"""
Scheduler — Vision Cortex Operational Schedule Manager
Governed by: /mcp/contracts/OPERATIONAL_SCHEDULE.json

Manages scheduled events and task execution for Vision Cortex agents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import json


class Frequency(Enum):
    """Event frequency types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledEvent:
    """A scheduled calendar event."""
    event_id: str
    name: str
    description: str
    frequency: Frequency
    time: str  # UTC time string
    duration_minutes: int
    responsible_agent: str
    pipeline: List[str] = field(default_factory=list)
    governance_level: str = "MEDIUM"
    requires_human_approval: bool = False
    day: Optional[str] = None  # For weekly/monthly
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "frequency": self.frequency.value,
            "time": self.time,
            "duration_minutes": self.duration_minutes,
            "responsible_agent": self.responsible_agent,
            "pipeline": self.pipeline,
            "governance_level": self.governance_level,
            "requires_human_approval": self.requires_human_approval,
            "day": self.day,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None
        }


@dataclass
class Task:
    """A task item."""
    task_id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.name.lower(),
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes
        }


@dataclass
class TaskList:
    """A collection of related tasks."""
    list_id: str
    name: str
    owner: str
    tasks: List[Task] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "list_id": self.list_id,
            "name": self.name,
            "owner": self.owner,
            "tasks": [t.to_dict() for t in self.tasks]
        }
    
    def get_pending(self) -> List[Task]:
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]
    
    def get_completed(self) -> List[Task]:
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]


class Scheduler:
    """
    Manages Vision Cortex operational schedule.
    
    Responsibilities:
    - Load schedule from OPERATIONAL_SCHEDULE.json
    - Track next run times for events
    - Manage task lists and status
    - Trigger agent pipelines on schedule
    """
    
    def __init__(self, config_path: str = "/mcp/contracts/OPERATIONAL_SCHEDULE.json"):
        self.config_path = Path(config_path)
        self._events: Dict[str, ScheduledEvent] = {}
        self._task_lists: Dict[str, TaskList] = {}
        self._event_handlers: Dict[str, Callable] = {}
    
    def load_config(self) -> bool:
        """Load schedule configuration from JSON."""
        if not self.config_path.exists():
            return False
        
        with open(self.config_path, "r") as f:
            config = json.load(f)
        
        # Load events
        for event_data in config.get("scheduling", {}).get("calendar_events", []):
            event = ScheduledEvent(
                event_id=event_data["event_id"],
                name=event_data["name"],
                description=event_data["description"],
                frequency=Frequency(event_data["frequency"]),
                time=event_data["time"],
                duration_minutes=event_data["duration_minutes"],
                responsible_agent=event_data["responsible_agent"],
                pipeline=event_data.get("pipeline", []),
                governance_level=event_data.get("governance_level", "MEDIUM"),
                requires_human_approval=event_data.get("requires_human_approval", False),
                day=event_data.get("day")
            )
            self._events[event.event_id] = event
        
        # Load task lists
        for list_data in config.get("tasks", {}).get("google_task_lists", []):
            tasks = []
            for task_data in list_data.get("tasks", []):
                task = Task(
                    task_id=task_data["task_id"],
                    title=task_data["title"],
                    status=TaskStatus(task_data.get("status", "pending")),
                    priority=TaskPriority[task_data.get("priority", "medium").upper()]
                )
                tasks.append(task)
            
            task_list = TaskList(
                list_id=list_data["list_id"],
                name=list_data["name"],
                owner=list_data["owner"],
                tasks=tasks
            )
            self._task_lists[task_list.list_id] = task_list
        
        return True
    
    def get_due_events(self, now: Optional[datetime] = None) -> List[ScheduledEvent]:
        """Get events that are due to run."""
        if now is None:
            now = datetime.utcnow()
        
        due = []
        for event in self._events.values():
            if self._is_event_due(event, now):
                due.append(event)
        
        return due
    
    def _is_event_due(self, event: ScheduledEvent, now: datetime) -> bool:
        """Check if an event is due to run."""
        # Parse event time
        hour, minute = map(int, event.time.replace(" UTC", "").split(":"))
        
        # Check frequency
        if event.frequency == Frequency.DAILY:
            if now.hour == hour and now.minute == minute:
                if event.last_run is None or (now - event.last_run) > timedelta(hours=23):
                    return True
        
        elif event.frequency == Frequency.WEEKLY:
            day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                      "Friday": 4, "Saturday": 5, "Sunday": 6}
            if event.day and now.weekday() == day_map.get(event.day, -1):
                if now.hour == hour and now.minute == minute:
                    if event.last_run is None or (now - event.last_run) > timedelta(days=6):
                        return True
        
        elif event.frequency == Frequency.MONTHLY:
            if event.day and now.day == int(event.day):
                if now.hour == hour and now.minute == minute:
                    if event.last_run is None or (now - event.last_run) > timedelta(days=27):
                        return True
        
        return False
    
    def mark_event_run(self, event_id: str) -> None:
        """Mark an event as having run."""
        if event_id in self._events:
            self._events[event_id].last_run = datetime.utcnow()
    
    def register_handler(self, event_id: str, handler: Callable) -> None:
        """Register a handler function for an event."""
        self._event_handlers[event_id] = handler
    
    async def trigger_event(self, event_id: str) -> Dict[str, Any]:
        """Trigger an event manually."""
        event = self._events.get(event_id)
        if not event:
            return {"success": False, "error": f"Event {event_id} not found"}
        
        handler = self._event_handlers.get(event_id)
        if handler:
            result = await handler(event)
            self.mark_event_run(event_id)
            return {"success": True, "result": result}
        
        return {"success": False, "error": "No handler registered"}
    
    def get_task_list(self, list_id: str) -> Optional[TaskList]:
        """Get a task list by ID."""
        return self._task_lists.get(list_id)
    
    def update_task_status(
        self,
        list_id: str,
        task_id: str,
        status: TaskStatus
    ) -> bool:
        """Update task status."""
        task_list = self._task_lists.get(list_id)
        if not task_list:
            return False
        
        for task in task_list.tasks:
            if task.task_id == task_id:
                task.status = status
                if status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                return True
        
        return False
    
    def get_all_pending_tasks(self) -> List[Task]:
        """Get all pending tasks across all lists."""
        pending = []
        for task_list in self._task_lists.values():
            pending.extend(task_list.get_pending())
        return pending
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        total_tasks = sum(len(tl.tasks) for tl in self._task_lists.values())
        completed_tasks = sum(len(tl.get_completed()) for tl in self._task_lists.values())
        
        return {
            "events_count": len(self._events),
            "task_lists_count": len(self._task_lists),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "handlers_registered": len(self._event_handlers)
        }
    
    def export_schedule(self) -> Dict[str, Any]:
        """Export current schedule state."""
        return {
            "events": [e.to_dict() for e in self._events.values()],
            "task_lists": [tl.to_dict() for tl in self._task_lists.values()],
            "status": self.get_status()
        }
