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
        """Produces a natural, concise spoken answer for the user."""
        # If Thinker provided a great initial sentence and all went well
        initial_spoken = plan.get("spoken_response")
        
        # Check for cancellations
        cancelled = any(r.get("result", {}).get("cancelled") for r in step_results)
        if cancelled:
            return "Operation was cancelled as requested."

        failures = [r for r in step_results if not r.get("result", {}).get("success", True)]
        if failures:
            err = failures[0].get("result", {}).get("error", "an error")
            return f"I encountered an issue: {err}."

        if initial_spoken:
            return initial_spoken

        return "Done. I have executed your request."

manager_agent = ManagerAgent()
