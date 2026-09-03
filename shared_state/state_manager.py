import threading
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from shared_state.database import (
    log_event,
    get_recent_events,
    create_task,
    update_task_status,
    get_active_tasks,
    set_memory,
    get_memory,
    get_all_memory,
    init_db
)

logger = logging.getLogger("Ultron.StateManager")

class StateManager:
    """
    Central State Coordinator for all Ultron agents.
    Maintains active task state, audit events, and thread-safe notifications.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []
        init_db()

    def record_action(self, agent_name: str, action: str, target: Optional[str] = None, details: Optional[Any] = None, status: str = "success") -> int:
        """
        Record an action in the central event log and notify active listeners.
        """
        with self._lock:
            event_id = log_event(agent_name, action, target, details, status)
            event_payload = {
                "id": event_id,
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "action": action,
                "target": target,
                "details": details,
                "status": status
            }
            self._notify_subscribers(event_payload)
            return event_id

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to real-time events published by any agent."""
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Unsubscribe from event stream."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def _notify_subscribers(self, event: Dict[str, Any]):
        for callback in list(self._subscribers):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber {callback}: {e}")

    # Task Management
    def add_task(self, title: str, description: str = "", assigned_agent: str = "Manager") -> int:
        with self._lock:
            task_id = create_task(title, description, assigned_agent)
            self.record_action(
                agent_name="StateManager",
                action="TASK_CREATED",
                target=f"Task #{task_id}",
                details={"title": title, "assigned_to": assigned_agent}
            )
            return task_id

    def complete_task(self, task_id: int, result: str = "Completed successfully"):
        with self._lock:
            update_task_status(task_id, "completed", result)
            self.record_action(
                agent_name="StateManager",
                action="TASK_COMPLETED",
                target=f"Task #{task_id}",
                details={"result": result}
            )

    def fail_task(self, task_id: int, error_message: str):
        with self._lock:
            update_task_status(task_id, "failed", error_message)
            self.record_action(
                agent_name="StateManager",
                action="TASK_FAILED",
                target=f"Task #{task_id}",
                details={"error": error_message},
                status="failed"
            )

    def list_active_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return get_active_tasks()

    def get_history(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._lock:
            return get_recent_events(limit)

    # Shared Memory K/V
    def remember(self, key: str, value: Any, category: str = "general"):
        with self._lock:
            set_memory(key, value, category)
            self.record_action(
                agent_name="StateManager",
                action="MEMORY_UPDATED",
                target=key,
                details={"category": category}
            )

    def recall(self, key: str) -> Optional[Any]:
        with self._lock:
            return get_memory(key)

    def dump_context(self) -> Dict[str, Any]:
        """Provides a complete snapshot of current state for agents to analyze."""
        with self._lock:
            return {
                "active_tasks": self.list_active_tasks(),
                "recent_events": self.get_history(10),
                "memory": get_all_memory()
            }

state_manager = StateManager()
