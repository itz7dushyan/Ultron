import time
import json
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("Ultron.SwarmHarness")

@dataclass
class SwarmEvent:
    event_id: str
    source_brain: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SwarmBlackboard:
    """
    Shared Thread-Safe Blackboard and Real-Time Event Bus.
    All specialized LLM brains publish and read real-time situational awareness here.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "active_goal": None,
            "browser_state": {"current_url": None, "profile": "Default", "active_tab": None},
            "os_state": {"active_window": None, "volume": None},
            "telephony_state": {"active_call": False, "call_summary": None},
            "big_task_state": {"meta_prompt": None, "seo_package": None, "wireframe": None},
            "critic_state": {"last_score": None, "approved": True, "notes": None}
        }
        self._event_history: List[SwarmEvent] = []
        self._subscribers: List[Callable[[SwarmEvent], None]] = []

    def set(self, key: str, value: Any, source_brain: str = "System"):
        with self._lock:
            self._state[key] = value
            ev = SwarmEvent(
                event_id=f"ev_{int(time.time()*1000)}",
                source_brain=source_brain,
                event_type=f"STATE_UPDATE_{key.upper()}",
                payload={"key": key, "value": value}
            )
            self._event_history.append(ev)
            self._notify_subscribers(ev)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def get_full_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def subscribe(self, callback: Callable[[SwarmEvent], None]):
        with self._lock:
            self._subscribers.append(callback)

    def _notify_subscribers(self, event: SwarmEvent):
        for cb in self._subscribers:
            try:
                cb(event)
            except Exception as e:
                logger.debug(f"Subscriber callback error: {e}")

class SwarmHarness:
    """
    Actor-pattern Swarm Harness coordinating specialized LLM brains.
    """

    def __init__(self):
        self.blackboard = SwarmBlackboard()
        self._brains: Dict[str, Any] = {}

    def register_brain(self, name: str, brain_instance: Any):
        self._brains[name] = brain_instance
        logger.info(f"Swarm Brain registered: {name}")

    def get_brain(self, name: str) -> Optional[Any]:
        return self._brains.get(name)

    def execute_swarm_task(self, brain_name: str, task_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a task directly to a specialized brain."""
        brain = self.get_brain(brain_name)
        if not brain:
            return {
                "success": False,
                "error": f"Swarm Brain '{brain_name}' is not registered."
            }
        try:
            res = brain.execute(task_name, parameters, self.blackboard)
            self.blackboard.set(f"last_result_{brain_name}", res, source_brain=brain_name)
            return res
        except Exception as e:
            logger.error(f"Swarm Brain '{brain_name}' execution failure on '{task_name}': {e}")
            return {"success": False, "error": str(e)}

swarm_harness = SwarmHarness()
