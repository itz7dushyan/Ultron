import json
import logging
from typing import Dict, Any, Optional
from agents.llm_client import llm_client
from tools.browser_control import browser_tools
from tools.vision_control import vision_control
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Brain.Browser")

class BrowserBrain:
    """
    Specialized Swarm Brain for ANY BROWSER TASK.
    Powered by Frontier LLM reasoning for web navigation, multi-profile routing,
    DOM/visual grounding, Hostinger hPanel, WordPress WP-Admin, and Google Workspace.
    """

    def __init__(self):
        self.name = "browser"

    def plan_and_execute(self, user_prompt: str, blackboard_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses specialized LLM reasoning to decompose any browser-related request
        into precise browser commands and executes them.
        """
        system_prompt = (
            "You are Ultron's Specialized Browser Navigator Brain.\n"
            "Your sole mission is to execute ANY browser or web task with 100% precision.\n"
            "You know all web services, URLs, and Chrome Profile routing rules:\n"
            "- Agency / SEO / Hostinger / WordPress tasks -> 'Profile 1' (Risala Digital Marketing: risaladigitalmarketing@gmail.com)\n"
            "- Personal tasks -> 'Default' (itzdushyant: itzdushyan@gmail.com)\n"
            "- Google Workspace URLs: Drive (https://drive.google.com), Docs (https://docs.google.com), Sheets (https://sheets.google.com), Gmail (https://mail.google.com)\n"
            "- Agency URLs: Hostinger (https://hpanel.hostinger.com), WordPress (https://risaladigitalmarketing.com/wp-admin), Risala Site (https://risaladigitalmarketing.com)\n"
            "- Common URLs: YouTube (https://www.youtube.com), ChatGPT (https://chatgpt.com), GitHub (https://github.com), WhatsApp Web (https://web.whatsapp.com)\n\n"
            "Available Actions:\n"
            "- open_url: {\"url\": \"...\", \"profile\": \"Profile 1\" or \"Default\"}\n"
            "- new_tab: {}\n"
            "- close_tab: {}\n"
            "- search_web: {\"query\": \"...\", \"engine\": \"google\" or \"youtube\"}\n"
            "- locate_and_click: {\"target\": \"Exact visual label on page like 'Sign in with Google' or 'WP Admin'\"}\n\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            '  "action": "open_url" | "new_tab" | "close_tab" | "search_web" | "locate_and_click",\n'
            '  "parameters": { ... },\n'
            '  "summary": "Brief summary of what this action does",\n'
            '  "spoken_confirmation": "Concise spoken phrase for Boss"\n'
            "}"
        )

        user_input = f"User Request: {user_prompt}\nCurrent State: {json.dumps(blackboard_state or {})}"

        try:
            raw = llm_client.complete_for_brain("browser", system_prompt, user_input, temperature=0.1, json_mode=True)
            plan = json.loads(raw)
        except Exception as e:
            logger.warning(f"Browser Brain LLM fallback note: {e}")
            # Dynamic fallback
            p_low = user_prompt.lower()
            if "drive" in p_low:
                plan = {"action": "open_url", "parameters": {"url": "https://drive.google.com"}, "summary": "Open Google Drive", "spoken_confirmation": "Opening Google Drive for you now, Boss."}
            elif "tab" in p_low:
                plan = {"action": "new_tab", "parameters": {}, "summary": "Open new tab", "spoken_confirmation": "Opening a new tab now, Boss."}
            else:
                plan = {"action": "open_url", "parameters": {"url": "https://www.google.com"}, "summary": "Open browser", "spoken_confirmation": "Opening the browser now, Boss."}

        # Execute planned browser action
        action = plan.get("action", "open_url")
        params = plan.get("parameters", {})
        result = self._dispatch_action(action, params)

        state_manager.record_action(
            agent_name="Brain.Browser",
            action=action,
            target=str(params.get("url") or params.get("target") or action),
            details=plan,
            status="success" if result.get("success", True) else "failed"
        )

        return {
            "brain": "browser",
            "plan": plan,
            "result": result,
            "spoken_response": plan.get("spoken_confirmation", "Browser action completed, Boss.")
        }

    def _dispatch_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "open_url":
            url = params.get("url", "https://www.google.com")
            profile = params.get("profile")
            return browser_tools.open_url(url, profile=profile)
        elif action == "new_tab":
            return browser_tools.new_tab()
        elif action == "close_tab":
            return browser_tools.close_current_tab()
        elif action == "search_web":
            query = params.get("query", "")
            engine = params.get("engine", "google")
            if engine == "youtube":
                return browser_tools.search_youtube(query)
            return browser_tools.search_google(query)
        elif action == "locate_and_click":
            target = params.get("target", "")
            return vision_control.locate_and_click(target)
        return {"success": False, "error": f"Unknown browser action: {action}"}

    def execute(self, task_name: str, parameters: Dict[str, Any], blackboard: Any) -> Dict[str, Any]:
        prompt = parameters.get("prompt") or parameters.get("user_prompt") or task_name
        res = self.plan_and_execute(prompt, blackboard.get_full_snapshot())
        blackboard.set("browser_state", {"last_action": res["plan"], "result": res["result"]}, source_brain="browser")
        return res

brain_browser = BrowserBrain()
