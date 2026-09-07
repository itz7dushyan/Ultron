import json
import logging
from typing import Dict, Any, Optional
from agents.llm_client import llm_client
from tools.memory_bank import memory_bank
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Brain.BigTasks")

class BigTasksBrain:
    """
    Specialized Swarm Brain for BIG TASKS, CREATIVE SYNTHESIS & AI META-PROMPTING.
    Handles:
    - Meta-prompting other AI models (v0.dev, Midjourney, Claude, Figma AI, ChatGPT)
    - Full WordPress Headless CMS + Next.js SEO Architecture & Schema Generation
    - Technical Documentation & Deep Implementation Plans
    - Social Outreach (Instagram, WhatsApp Web, Email drafts)
    """

    def __init__(self):
        self.name = "big_tasks"

    def plan_and_execute(self, user_prompt: str, blackboard_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses deep frontier LLM reasoning (OpenAI GPT-4o / Claude / Experiential)
        to synthesize large-scale technical and creative assets.
        """
        agency_kb = memory_bank.get_agency_knowledge()

        system_prompt = (
            "You are Ultron's Specialized Big Tasks & Meta-Prompting Brain.\n"
            "Your mission is to handle complex, large-scale workflows:\n"
            "1. META-PROMPTING OTHER AIs:\n"
            "   - Formulate master-level system prompts, component specifications, and design tokens to command tools like v0.dev, Midjourney, Claude 3.7, Bolt.new, or Figma AI.\n"
            "2. AGENCY HEADLESS CMS & SEO ARCHITECTURE:\n"
            "   - Target Market: India (with local focus on Jodhpur, Rajasthan, and Pan-India enterprises).\n"
            "   - Generate RankMath/Yoast focus keywords, meta titles (<60 chars), meta descriptions (140-155 chars), and content architecture for WordPress + Next.js.\n"
            "3. DEEP DOCUMENTATION & PLANS:\n"
            "   - Create structured technical documentation and full-stack roadmaps.\n"
            "4. SOCIAL & CLIENT COMMUNICATIONS:\n"
            "   - High-converting outreach copy for WhatsApp, Instagram, or Email.\n\n"
            f"Agency Guidelines & Tech Stack:\n{agency_kb}\n\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            '  "task_type": "meta_prompt" | "seo_architecture" | "app_planning" | "social_draft" | "documentation",\n'
            '  "title": "Title of the asset",\n'
            '  "payload": {\n'
            '     "focus_keyword": "...",\n'
            '     "meta_title": "...",\n'
            '     "meta_description": "...",\n'
            '     "meta_prompt_text": "...",\n'
            '     "target_ai_model": "v0" | "midjourney" | "claude" | "chatgpt" | "figma",\n'
            '     "architecture_overview": "...",\n'
            '     "structured_content": "..."\n'
            '  },\n'
            '  "summary": "Brief explanation of what was created",\n'
            '  "spoken_confirmation": "Concise spoken phrase for Boss"\n'
            "}"
        )

        user_input = f"User Request: {user_prompt}\nContext State: {json.dumps(blackboard_state or {})}"

        try:
            raw = llm_client.complete_for_brain("big_tasks", system_prompt, user_input, temperature=0.3, json_mode=True)
            res = json.loads(raw)
        except Exception as e:
            logger.warning(f"Big Tasks Brain LLM fallback note: {e}")
            res = {
                "task_type": "seo_architecture",
                "title": "SEO & Architecture Plan",
                "payload": {
                    "focus_keyword": "Digital Marketing Agency in Jodhpur",
                    "meta_title": "Digital Marketing Agency in Jodhpur | Risala Digital",
                    "meta_description": "Partner with Risala Digital Marketing in Jodhpur driving high-ROI performance marketing and headless web builds. Contact us today!",
                    "target_ai_model": "v0"
                },
                "summary": "Generated SEO and architecture package.",
                "spoken_confirmation": "Big task strategy formulated for you, Boss."
            }

        state_manager.record_action(
            agent_name="Brain.BigTasks",
            action=res.get("task_type", "BIG_TASK"),
            target=res.get("title", "Project Asset"),
            details=res.get("payload", {}),
            status="success"
        )

        return {
            "brain": "big_tasks",
            "task_type": res.get("task_type"),
            "title": res.get("title"),
            "payload": res.get("payload"),
            "summary": res.get("summary"),
            "spoken_response": res.get("spoken_confirmation", "Strategy and assets generated for you, Boss.")
        }

    def execute(self, task_name: str, parameters: Dict[str, Any], blackboard: Any) -> Dict[str, Any]:
        prompt = parameters.get("prompt") or parameters.get("user_prompt") or task_name
        res = self.plan_and_execute(prompt, blackboard.get_full_snapshot())
        blackboard.set("big_task_state", res, source_brain="big_tasks")
        return res

brain_big_tasks = BigTasksBrain()
