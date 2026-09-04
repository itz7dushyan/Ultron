import json
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.thinker import thinker_agent
from agents.coder import coder_agent
from agents.qa_debugger import qa_agent
from agents.executor import executor_agent

logger = logging.getLogger("Ultron.Manager")

class ManagerAgent(BaseAgent):
    """
    Manager Agent: The master coordinator of Ultron.
    Understands high-level goals, assigns sub-tasks, tracks execution across
    Thinker, Coder, QA, and Executor agents, and generates voice responses.
    """

    def __init__(self):
        super().__init__(
            name="Manager",
            role_description="Chief orchestrator and conversational lead of Ultron."
        )
        self.conversation_history: List[Dict[str, str]] = []

    def handle_user_command(self, user_command: str) -> Dict[str, Any]:
        """
        Main entrypoint for processing user instructions end-to-end.
        """
        self.conversation_history.append({"role": "user", "content": user_command})
        task_id = self.state.add_task(
            title=user_command[:60],
            description=user_command,
            assigned_agent="Manager"
        )

        # 1. Ask Thinker Agent to evaluate intent and design step-by-step plan
        context = self.state.dump_context()
        context["recent_dialogue"] = self.conversation_history[-4:]
        plan = thinker_agent.analyze_and_plan(user_command, context)

        steps = plan.get("steps", [])
        step_results = []
        overall_success = True

        # 2. Iterate through plan steps and dispatch to appropriate specialized agent
        for step in steps:
            assigned = step.get("assigned_agent", "Executor")
            action = step.get("action", "")
            params = step.get("parameters", {})

            if assigned == "Coder" or action == "code_project":
                proj_name = params.get("project_name", "UltronProject")
                reqs = params.get("requirements", user_command)
                res = coder_agent.develop_project(proj_name, reqs)
                step_results.append({"step": step, "result": res})

                # Automatically invoke QA Agent to verify newly written code
                for fpath in res.get("files", []):
                    if fpath.endswith(".py"):
                        qa_res = qa_agent.verify_python_syntax(fpath)
                        step_results.append({"step": {"description": f"QA check for {fpath}"}, "result": qa_res})

            elif assigned == "QA":
                cmd = params.get("command", "python --version")
                cwd = params.get("cwd", ".")
                res = qa_agent.run_automated_test(cmd, cwd)
                step_results.append({"step": step, "result": res})

            else:  # Executor Agent
                res = executor_agent.execute_step(action, params)
                step_results.append({"step": step, "result": res})
                if not res.get("success", False) and not res.get("cancelled", False):
                    overall_success = False

        # 3. Mark task completed or failed
        if overall_success:
            self.state.complete_task(task_id, result="All steps executed successfully.")
        else:
            self.state.fail_task(task_id, error_message="One or more steps encountered an error.")

        # 4. Formulate spoken response
        spoken_response = self._generate_final_response(user_command, plan, step_results)
        self.conversation_history.append({"role": "assistant", "content": spoken_response})

        return {
            "task_id": task_id,
            "intent": plan.get("intent_summary"),
            "spoken_response": spoken_response,
            "steps": step_results,
            "success": overall_success
        }

    def _generate_final_response(self, user_command: str, plan: Dict[str, Any], step_results: List[Dict[str, Any]]) -> str:
        """Dynamically formulates an intelligent, context-aware spoken response via frontier LLM."""
        cancelled = any(r.get("result", {}).get("cancelled") for r in step_results)
        if cancelled:
            return "Operation cancelled as requested, Boss."

        failures = [r for r in step_results if not r.get("result", {}).get("success", True)]
        if failures:
            err = failures[0].get("result", {}).get("error", "an unexpected error")
            return f"Boss, I ran into an obstacle with that step: {err}."

        if not step_results:
            return plan.get("spoken_response", "Online and ready, Boss.")

        # Dynamically generate contextual response based on what was actually accomplished
        try:
            from agents.llm_client import UnifiedLLMClient
            
            summary_of_actions = []
            for item in step_results:
                action_name = item.get("step", {}).get("action", "action")
                desc = item.get("step", {}).get("description", "")
                res_msg = item.get("result", {}).get("message", "completed")
                summary_of_actions.append(f"- {action_name}: {desc} ({res_msg})")

            sys_prompt = (
                "You are Ultron, speaking directly to your Boss in 100% fluent, crisp, cinematic English.\n"
                "Formulate a single concise, natural, dynamic spoken sentence summarizing what was accomplished.\n"
                "Guidelines:\n"
                "- Address the user as 'Boss'. Never use 'Sir'.\n"
                "- NEVER use generic canned phrases like 'Done. I have executed your request.'\n"
                "- Speak directly about the concrete actions performed and any strategic insights.\n"
                "- Keep it under 25 words so it is punchy and conversational over voice TTS.\n"
                "- Output ONLY the exact spoken sentence. Never output thinking processes or preambles."
            )

            user_prompt = (
                f"Boss's Command: {user_command}\n"
                f"Actions Accomplished:\n" + "\n".join(summary_of_actions)
            )

            client = UnifiedLLMClient()
            response = client.complete(sys_prompt, user_prompt, temperature=0.7, max_tokens=150).strip()
            if response and len(response) > 5:
                import re
                # Find any line specifically addressing Boss
                boss_lines = [ln.strip(' "*\'') for ln in response.splitlines() if ln.strip(' "*\'').startswith("Boss")]
                if boss_lines:
                    tight_lines = [l for l in boss_lines if len(l.split()) <= 28]
                    clean_resp = tight_lines[0] if tight_lines else boss_lines[-1]
                else:
                    lines = [ln.strip() for ln in response.splitlines() if ln.strip() and not ln.strip().startswith("<think") and not ln.strip().startswith("```") and not ln.strip().startswith("**") and not ln.strip().startswith("Here's")]
                    clean_resp = lines[-1] if lines else response

                clean_resp = re.sub(r'[^\x00-\x7F]+', '', clean_resp).strip('\'" ')
                if clean_resp and len(clean_resp) > 5:
                    return clean_resp
        except Exception as e:
            logger.debug(f"Dynamic response generation fallback: {e}")

        initial_spoken = plan.get("spoken_response")
        if initial_spoken:
            return initial_spoken

        return "All requested tasks are executed and operational, Boss."

manager_agent = ManagerAgent()
