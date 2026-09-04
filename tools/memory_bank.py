import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from shared_state.database import set_memory, get_memory, get_all_memory
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.MemoryBank")

class MemoryBank:
    """
    Persistent Long-Term Memory Engine for Ultron.
    Retains user preferences, personal profiles, identity facts, and instructions
    across restarts and sessions.
    """

    def __init__(self):
        self._init_defaults()

    def _init_defaults(self):
        """Auto-detects Chrome profiles and seeds default personal profile if not set."""
        try:
            if not get_memory("personal_chrome_profile"):
                profiles = self.get_available_chrome_profiles()
                # If Default profile exists (Your Chrome - itzdushyan@gmail.com), set as default
                if "Default" in profiles:
                    set_memory(
                        "personal_chrome_profile",
                        "Default",
                        category="browser_profiles"
                    )
                    set_memory(
                        "user_email",
                        profiles["Default"].get("email", ""),
                        category="identity"
                    )
                    set_memory(
                        "user_name",
                        profiles["Default"].get("name", "Boss"),
                        category="identity"
                    )
                    logger.info("Initialized personal Chrome profile memory: Default (itzdushyan@gmail.com)")
        except Exception as e:
            logger.debug(f"MemoryBank default init note: {e}")

    def get_available_chrome_profiles(self) -> Dict[str, Dict[str, str]]:
        """Scans Windows Chrome User Data directory and returns map of profile directories to user accounts."""
        results = {}
        try:
            chrome_user_data = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
            local_state_path = chrome_user_data / "Local State"
            if local_state_path.exists():
                with open(local_state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    info_cache = data.get("profile", {}).get("info_cache", {})
                    for p_dir, p_info in info_cache.items():
                        results[p_dir] = {
                            "name": p_info.get("name", ""),
                            "email": p_info.get("user_name", ""),
                            "dir": p_dir
                        }
        except Exception as e:
            logger.debug(f"Chrome profile scan note: {e}")
        return results

    def remember(self, key: str, value: Any, category: str = "user_preference") -> Dict[str, Any]:
        """Permanently stores a fact or preference in SQLite database."""
        set_memory(key, value, category=category)
        state_manager.record_action("MemoryBank", "REMEMBER", key, details={"value": value, "category": category})
        logger.info(f"Committed to long-term memory: {key} = {value}")
        return {"success": True, "key": key, "value": value}

    def recall(self, key: str) -> Optional[Any]:
        """Retrieves a memory by key."""
        return get_memory(key)

    def list_all(self) -> Dict[str, Any]:
        """Returns all persistent memories formatted for LLM context."""
        return get_all_memory()

    def get_agency_knowledge(self) -> str:
        """Loads institutional knowledge for Risala Digital Marketing and headless CMS workflows."""
        from config import DATA_DIR
        doc_path = DATA_DIR / "knowledge" / "agency_workflow.md"
        if doc_path.exists():
            try:
                return doc_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.debug(f"Knowledge read note: {e}")
        return ""

    def set_personal_chrome_profile(self, profile_name_or_email: str) -> Dict[str, Any]:
        """Finds and saves the specified Chrome profile directory as the user's personal profile."""
        profiles = self.get_available_chrome_profiles()
        target_dir = None
        target_info = None

        query = profile_name_or_email.lower().strip()
        for p_dir, info in profiles.items():
            if query in p_dir.lower() or query in info.get("name", "").lower() or query in info.get("email", "").lower():
                target_dir = p_dir
                target_info = info
                break

        if not target_dir:
            # Fallback to direct directory name or Default
            target_dir = "Default"
            target_info = profiles.get("Default", {"name": "Default", "email": ""})

        self.remember("personal_chrome_profile", target_dir, category="browser_profiles")
        if target_info:
            self.remember("personal_profile_name", target_info.get("name", ""), category="browser_profiles")
            self.remember("personal_profile_email", target_info.get("email", ""), category="browser_profiles")

        return {
            "success": True,
            "profile_dir": target_dir,
            "profile_info": target_info,
            "message": f"Saved Chrome profile '{target_dir}' ({target_info.get('email', '')}) as personal profile."
        }

memory_bank = MemoryBank()
