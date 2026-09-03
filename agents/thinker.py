import json
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent

class ThinkerAgent(BaseAgent):
    """
    Thinker Agent: Evaluates user intent, breaks down complex tasks into atomic
    action steps, assesses risks, and selects optimal execution paths.
    """

    def __init__(self):
        super().__init__(
            name="Thinker",
            role_description="System architect and analytical planner for Ultron."
        )

    def analyze_and_plan(self, user_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decomposes a user's instruction into structured plan steps.
        """
        system_prompt = (
            "You are the Thinker Agent of Ultron, a high-level system architect and cognitive planner on Windows 11.\n"
            "Your job is to analyze the user's command, consider the current system context, identify risks, and produce an actionable plan.\n\n"
            "Available tools across agents:\n"
            "- AppControl: open_app, close_app\n"
            "- BrowserControl: open_url, navigate, click, type_text\n"
            "- FileOps: create_directory, write_file, read_file, move_file, delete_path, search_files\n"
            "- ShellControl: execute_command (PowerShell)\n"
            "- VPNControl: connect_vpn, disconnect_vpn\n"
            "- APIGateway: send_email, post_to_instagram, create_facebook_ad_campaign, make_call\n"
            "- SystemTelemetry: system_status, hardware_stats\n"
            "- VisionControl: analyze_screen, screenshot\n"
            "- Coder: generate_project_code, edit_code\n"
            "- QADebugger: verify_code, test_execution\n\n"
            "You must respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "intent_summary": "Short 1-sentence description of intent",\n'
            '  "requires_confirmation": true/false,\n'
            '  "confirmation_reason": "Explanation if confirmation is needed, else null",\n'
            '  "steps": [\n'
            '    {\n'
            '      "step_id": 1,\n'
            '      "assigned_agent": "Executor" or "Coder" or "QA",\n'
            '      "action": "open_app" | "navigate" | "write_file" | "execute_command" | "connect_vpn" | "api_call" | "code_project",\n'
            '      "parameters": {"key": "value"},\n'
            '      "description": "Brief description of step"\n'
            '    }\n'
            '  ],\n'
            '  "spoken_response": "Concise, natural sentence Ultron should speak back to the user upon starting."\n'
            "}"
        )

        prompt_clean = user_prompt.strip().lower()
        if prompt_clean in ("wake", "wake up", "hey", "hello", "hi", "ultron", "yo", "k", "ok"):
            plan = {
                "intent_summary": "System wake & greeting acknowledgment",
                "requires_confirmation": False,
                "steps": [],
                "spoken_response": "Online and ready, Sir. What would you like me to do?"
            }
            self.log(action="PLAN_CREATED", target=plan["intent_summary"], details={"step_count": 0, "risk": False})
            return plan

        # Fast Reflex Engine: Sub-second local execution for standard desktop commands
        reflex_plan = self._fast_reflex_plan(user_prompt)
        if reflex_plan:
            self.log(
                action="PLAN_CREATED",
                target=reflex_plan["intent_summary"],
                details={"step_count": len(reflex_plan.get("steps", [])), "risk": False, "reflex": True}
            )
            return reflex_plan

        from tools.memory_bank import memory_bank
        context["persistent_memory"] = memory_bank.list_all()

        user_content = (
            f"User Instruction: {user_prompt}\n"
            f"Current Context: {json.dumps(context, default=str)}\n"
        )

        raw_response = self.llm.complete(system_prompt, user_content, temperature=0.1, json_mode=True)
        plan = self.parse_json(raw_response)

        # Fallback safeguard if parsing yields incomplete plan
        if not plan.get("steps"):
            plan = self._fallback_plan(user_prompt)

        self.log(
            action="PLAN_CREATED",
            target=plan.get("intent_summary", user_prompt[:40]),
            details={"step_count": len(plan.get("steps", [])), "risk": plan.get("requires_confirmation")}
        )
        return plan

    def _fast_reflex_plan(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Ultra-fast local intent classifier (<5ms). Handles standard desktop actions,
        document generation, and memory preferences instantly.
        """
        p = user_prompt.lower().strip()

        # 1. Document Creation & Writing Requests (Google Docs / Paragraphs / Folder Move)
        if any(w in p for w in ("document", "doc", "docs", "paragraph", "essay")) and any(w in p for w in ("open", "create", "make", "write")):
            topic = user_prompt
            for prefix in (
                "open a google document and write a paragraph on the topic",
                "open a google document and write a paragraph on",
                "make a google document on the topic",
                "make a google document on",
                "create a google document on the topic",
                "create a google document on",
                "write a paragraph on the topic",
                "write a paragraph on",
                "write about",
                "document on"
            ):
                if prefix in p:
                    topic = user_prompt[p.find(prefix) + len(prefix):].strip(" :.,")
                    break
            
            # Clean topic from subsequent instructions
            for stopper in ("then make a folder", "make a folder", "and then", "then", "and make"):
                if stopper in topic.lower():
                    topic = topic[:topic.lower().find(stopper)].strip(" :.,")

            if not topic or len(topic) < 2:
                topic = "AI in 2026"

            # Check if user also requested a target folder on the laptop
            target_folder = None
            if "voice model testing" in p:
                target_folder = "Voice model testing"
            elif "folder" in p or "directory" in p:
                for marker in ("called", "named"):
                    if marker in p:
                        sub = p.split(marker, 1)[1]
                        for stopper in ("and", "then", "download", "to", "inside", "folder"):
                            if stopper in sub:
                                sub = sub.split(stopper, 1)[0]
                        clean_folder = sub.strip(" '\".,")
                        if len(clean_folder) >= 2:
                            target_folder = clean_folder.title()
                            break

            params = {"topic": topic, "app_target": "google_docs"}
            if target_folder:
                params["target_folder"] = target_folder
                spoken_msg = f"Creating your Google Document on {topic}, establishing the '{target_folder}' folder on your laptop, and moving the document inside it now."
                intent_msg = f"Create Google Doc on '{topic}', create '{target_folder}' folder, and save document"
            else:
                spoken_msg = f"Opening Google Docs in your personal profile and writing the paragraph on {topic} now."
                intent_msg = f"Create document and write paragraph on {topic}"

            return {
                "intent_summary": intent_msg,
                "requires_confirmation": False,
                "steps": [
                    {
                        "step_id": 1,
                        "assigned_agent": "Executor",
                        "action": "create_document",
                        "parameters": params,
                        "description": f"Generate document on {topic} and save to {target_folder or 'Documents'}"
                    }
                ],
                "spoken_response": spoken_msg
            }

        # 2. Chrome Profile & Long-Term Memory Setting
        if "personal profile" in p or "chrome profile" in p:
            profile = "Default"
            for candidate in ("profile 1", "profile 10", "profile 12", "profile 13", "profile 4", "profile 5", "default"):
                if candidate in p:
                    profile = candidate.title()
                    break
            return {
                "intent_summary": "Update personal Chrome profile preference",
                "requires_confirmation": False,
                "steps": [
                    {
                        "step_id": 1,
                        "assigned_agent": "Executor",
                        "action": "set_chrome_profile",
                        "parameters": {"profile": profile},
                        "description": f"Save personal Chrome profile preference: {profile}"
                    }
                ],
                "spoken_response": f"I have committed {profile} to memory as your personal Chrome profile."
            }

        # Guard: Do not intercept complex multi-part sentences in simple site launcher
        if any(w in p for w in ("and write", "and then", "search for", "write")):
            return None

        # 3. Specific Websites / Chrome / Browser
        if any(w in p for w in ("youtube", "google", "chatgpt", "github", "reddit", "twitter", "facebook", "instagram")):
            url = "https://www.google.com"
            site_name = "Google"
            if "youtube" in p:
                url = "https://www.youtube.com"
                site_name = "YouTube"
            elif "chatgpt" in p:
                url = "https://chatgpt.com"
                site_name = "ChatGPT"
            elif "github" in p:
                url = "https://github.com"
                site_name = "GitHub"
            elif "reddit" in p:
                url = "https://www.reddit.com"
                site_name = "Reddit"
            elif "twitter" in p or " x " in f" {p} ":
                url = "https://x.com"
                site_name = "X"
            elif "instagram" in p:
                url = "https://www.instagram.com"
                site_name = "Instagram"

            return {
                "intent_summary": f"Open {site_name} in browser",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": url}, "description": f"Navigate to {site_name}"}
                ],
                "spoken_response": f"Opening {site_name} now."
            }

        # 4. General Chrome / Browser launch
        if "chrome" in p or "browser" in p:
            return {
                "intent_summary": "Launch web browser",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": "https://www.google.com"}, "description": "Open default browser"}
                ],
                "spoken_response": "Launching your web browser."
            }

        # 3. System Vitals & Hardware Telemetry
        if any(k in p for k in ("battery", "system status", "hardware", "laptop doing", "system doing", "cpu", "ram", "specs")):
            return {
                "intent_summary": "Inspect hardware and system telemetry",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "system_status", "parameters": {}, "description": "Fetch live system metrics"}
                ],
                "spoken_response": "Accessing hardware telemetry now."
            }

        # 4. Desktop Screen Vision / Screenshot
        if any(k in p for k in ("screenshot", "screen capture", "look at my screen", "see my screen")):
            return {
                "intent_summary": "Capture and analyze desktop screen",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "screenshot", "parameters": {}, "description": "Capture screen"}
                ],
                "spoken_response": "Capturing visual telemetry from your desktop."
            }

        # 5. Standard Applications
        if "notepad" in p:
            return {
                "intent_summary": "Open Notepad",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "notepad"}, "description": "Open Notepad"}],
                "spoken_response": "Opening Notepad."
            }
        if "calculator" in p:
            return {
                "intent_summary": "Open Calculator",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "calc"}, "description": "Open Calculator"}],
                "spoken_response": "Opening Calculator."
            }

        return None

    def _fallback_plan(self, user_prompt: str) -> Dict[str, Any]:
        """Provides dynamic fallback plan when LLM is in offline mode."""
        prompt_lower = user_prompt.lower()
        if "chrome" in prompt_lower or "chatgpt" in prompt_lower or "browser" in prompt_lower:
            url = "https://chatgpt.com" if "chatgpt" in prompt_lower else "https://google.com"
            return {
                "intent_summary": "Launch browser and open requested site",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": url}, "description": f"Open {url}"}
                ],
                "spoken_response": f"Opening your browser to {url}."
            }
        elif "vpn" in prompt_lower:
            country = "Germany" if "germany" in prompt_lower else "United States"
            return {
                "intent_summary": f"Connect VPN to {country}",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "connect_vpn", "parameters": {"country": country}, "description": f"Connect VPN to {country}"}
                ],
                "spoken_response": f"Connecting your VPN to {country} now."
            }
        elif "folder" in prompt_lower or "desktop" in prompt_lower or "project" in prompt_lower:
            return {
                "intent_summary": "Create project workspace and scaffold files",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "create_directory", "parameters": {"path": "Desktop/UltronProject"}, "description": "Create project directory"},
                    {"step_id": 2, "assigned_agent": "Coder", "action": "code_project", "parameters": {"project_name": "UltronProject", "requirements": user_prompt}, "description": "Generate project code"}
                ],
                "spoken_response": "Creating the project workspace and writing the code now."
            }
        else:
            return {
                "intent_summary": "Standing by for user command",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "echo", "parameters": {"message": user_prompt}, "description": "Standing by"}
                ],
                "spoken_response": "Acknowledged. Standing by for your next command, Sir."
            }

thinker_agent = ThinkerAgent()
