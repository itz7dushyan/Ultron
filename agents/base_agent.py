import json
import re
import logging
from typing import Dict, Any, Optional
from agents.llm_client import llm_client
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.BaseAgent")

class BaseAgent:
    """Base class for specialized Ultron agents."""

    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        self.llm = llm_client
        self.state = state_manager

    def parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Extracts and parses JSON object from LLM response cleanly."""
        cleaned = raw_text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: regex search for outer braces
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            logger.warning(f"[{self.name}] Failed to parse JSON: {raw_text[:100]}...")
            return {"raw_text": raw_text}

    def log(self, action: str, target: Optional[str] = None, details: Optional[Any] = None, status: str = "success"):
        """Convenience method to log an action into shared state."""
        self.state.record_action(self.name, action, target, details, status)
