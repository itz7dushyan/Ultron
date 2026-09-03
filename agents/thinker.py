import json
from typing import Dict, Any
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
                "intent_summary": "Process general request",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "echo", "parameters": {"message": user_prompt}, "description": "Acknowledge request"}
                ],
                "spoken_response": "Right away. Processing your request."
            }

thinker_agent = ThinkerAgent()
