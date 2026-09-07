import json
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.brains import (
    brain_browser,
    brain_os_device,
    brain_big_tasks,
    brain_telephony,
    quality_critic,
    swarm_harness
)
from agents.coder import coder_agent
from agents.qa_debugger import qa_agent
from agents.executor import executor_agent
from agents.thinker import thinker_agent
from agents.llm_client import llm_client

logger = logging.getLogger("Ultron.Manager")

class ManagerAgent(BaseAgent):
    """
    Manager Agent: The Master Commander of Ultron's Multi-LLM Swarm Harness.
    Understands high-level goals, dynamically routes to specialized brains:
    - Brain 1: Swarm Commander (Orchestrator)
    - Brain 2: Browser Navigator (Any Browser Task)
    - Brain 3: OS & Device Engine (Any OS / Hardware Task)
    - Brain 4: Big Tasks & Meta-Prompting (App planning, SEO, v0/Midjourney/Claude prompts)
    - Brain 5: Telephony & Comms (Live phone calls, reservations, messaging)
    - Brain 6: Quality Critic (Self-reflection & evaluation)
    - Brain 7: Voice Streamer (Real-time cinematic spoken responses)
    """

    def __init__(self):
        super().__init__(
            name="Manager",
            role_description="Chief Swarm Commander and conversational lead of Ultron."
        )
        self.conversation_history: List[Dict[str, str]] = []

    def handle_user_command(self, user_command: str) -> Dict[str, Any]:
        """
        Main entrypoint for processing user instructions across the Multi-LLM Swarm.
        """
        self.conversation_history.append({"role": "user", "content": user_command})
        task_id = self.state.add_task(
            title=user_command[:60],
            description=user_command,
            assigned_agent="Manager"
        )

        p_low = user_command.lower().strip()

        # Direct Brain Routing for High-Confidence Domains
        # 1. Telephony Brain (e.g. 'call hotel', 'book a table', 'make a call')
        if any(w in p_low for w in ("call the hotel", "call hotel", "book a table", "book seats", "make a call", "dial ", "phone call")):
            res = brain_telephony.plan_and_execute(user_command, swarm_harness.blackboard.get_full_snapshot())
            spoken_response = res.get("spoken_response", "Initiating the call now, Boss.")
            self.state.complete_task(task_id, result="Telephony session executed.")
            self.conversation_history.append({"role": "assistant", "content": spoken_response})
            return {
                "task_id": task_id,
                "intent": "Outbound Telephony & Live Booking",
                "spoken_response": spoken_response,
                "brain_used": "telephony",
                "result": res,
                "success": True
            }

        # 2. Big Tasks & Meta-Prompting Brain (e.g. 'prompt for v0', 'plan an app', 'sketch ui/ux', 'seo strategy', 'headless cms')
        if any(w in p_low for w in ("meta prompt", "prompt for", "plan an app", "plan a website", "make a website", "sketch the ui", "ui/ux", "v0", "midjourney", "figma", "seo strategy")):
            res = brain_big_tasks.plan_and_execute(user_command, swarm_harness.blackboard.get_full_snapshot())
            # Pass through Quality Critic for self-reflection
            eval_res = quality_critic.evaluate_seo_content(
                page_title=res.get("title", "Big Task"),
                focus_keyword=res.get("payload", {}).get("focus_keyword", "Digital Marketing"),
                meta_title=res.get("payload", {}).get("meta_title", "Risala Digital"),
                meta_description=res.get("payload", {}).get("meta_description", "High performance marketing."),
                page_copy=res.get("summary", "")
            )
            res["quality_evaluation"] = eval_res
            spoken_response = res.get("spoken_response", "Big task strategy formulated for you, Boss.")
            self.state.complete_task(task_id, result="Big task completed.")
            self.conversation_history.append({"role": "assistant", "content": spoken_response})
            return {
                "task_id": task_id,
                "intent": f"Big Task: {res.get('title')}",
                "spoken_response": spoken_response,
                "brain_used": "big_tasks",
                "result": res,
                "success": True
            }

        # 3. Standard Multi-Step Swarm Planning via Thinker Agent
        context = self.state.dump_context()
        context["recent_dialogue"] = self.conversation_history[-4:]
        plan = thinker_agent.analyze_and_plan(user_command, context)

        steps = plan.get("steps", [])
        step_results = []
        overall_success = True

        for step in steps:
            assigned = step.get("assigned_agent", "Executor")
            action = step.get("action", "")
            params = step.get("parameters", {})

            if assigned == "Coder" or action == "code_project":
                proj_name = params.get("project_name", "UltronProject")
                reqs = params.get("requirements", user_command)
                res = coder_agent.develop_project(proj_name, reqs)
                step_results.append({"step": step, "result": res})

                for fpath in res.get("files", []):
                    if fpath.endswith(".py"):
                        qa_res = qa_agent.verify_python_syntax(fpath)
                        step_results.append({"step": {"description": f"QA check for {fpath}"}, "result": qa_res})

            elif assigned == "QA":
                cmd = params.get("command", "python --version")
                cwd = params.get("cwd", ".")
                res = qa_agent.run_automated_test(cmd, cwd)
                step_results.append({"step": step, "result": res})

            elif action in ("open_url", "new_tab", "close_tab", "search_web", "locate_and_click"):
                res = brain_browser.plan_and_execute(f"{action} {json.dumps(params)}", swarm_harness.blackboard.get_full_snapshot())
                step_results.append({"step": step, "result": res.get("result", {})})

            elif action in ("launch_app", "close_app", "set_volume", "volume_up", "volume_down", "mute_audio", "inspect_telemetry", "lock_workstation", "show_desktop"):
                res = brain_os_device.plan_and_execute(f"{action} {json.dumps(params)}", swarm_harness.blackboard.get_full_snapshot())
                step_results.append({"step": step, "result": res.get("result", {})})

            else:  # Executor Fallback
                res = executor_agent.execute_step(action, params)
                step_results.append({"step": step, "result": res})
                if not res.get("success", False) and not res.get("cancelled", False):
                    overall_success = False

        if overall_success:
            self.state.complete_task(task_id, result="All swarm steps executed successfully.")
        else:
            self.state.fail_task(task_id, error_message="One or more steps encountered an error.")

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
            err_msg = failures[0].get("result", {}).get("error", "Action failed")
            return f"Encountered an obstacle, Boss: {err_msg}"

        intent = plan.get("intent_summary", "Command completed")
        planned_spoken = plan.get("spoken_response", "")

        sys_prompt = (
            "You are Marvel Ultron, an ultra-intelligent, confident, sleek cybernetic AI assistant.\n"
            "Formulate a single concise, punchy spoken response (strictly under 20 words) addressing the user as 'Boss'.\n"
            "NEVER use canned or repetitive phrases like 'Done. I have executed your request.'\n"
            "Reference specifically what was completed in cinematic, natural English."
        )
        user_prompt = (
            f"User command: '{user_command}'\n"
            f"Executed intent: '{intent}'\n"
            f"Planned note: '{planned_spoken}'\n"
            f"Step details: {json.dumps([r.get('result', {}) for r in step_results[:3]])}"
        )

        try:
            resp = llm_client.complete_for_brain("voice", sys_prompt, user_prompt, temperature=0.3, max_tokens=150)
            cleaned = resp.strip().replace('"', '').replace('\n', ' ')
            if "boss" not in cleaned.lower():
                cleaned = f"{cleaned}, Boss."
            return cleaned
        except Exception as e:
            logger.debug(f"Dynamic response synthesis note: {e}")
            if planned_spoken:
                return planned_spoken
            return f"{intent} complete, Boss."

manager_agent = ManagerAgent()
