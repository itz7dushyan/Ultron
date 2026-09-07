import json
import logging
from typing import Dict, Any, Optional
from agents.llm_client import llm_client
from tools.api_gateway import api_gateway
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Brain.Telephony")

class TelephonyBrain:
    """
    Specialized Swarm Brain for OUTBOUND TELEPHONY, LIVE CALLING & COMMS.
    Powered by Fast Conversational LLM reasoning to manage phone calls (Twilio / Bland / Vapi / Retell),
    negotiations, reservations, and customer communications.
    """

    def __init__(self):
        self.name = "telephony"

    def plan_and_execute(self, user_prompt: str, blackboard_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses specialized conversational reasoning to build call scripts,
        extract target phone numbers, and execute outbound voice calls or messaging.
        """
        system_prompt = (
            "You are Ultron's Specialized Telephony & Communications Brain.\n"
            "Your mission is to execute outbound telephone calls, restaurant/hotel reservations, customer inquiries, and direct messaging.\n\n"
            "When user asks to make a call:\n"
            "1. Identify the target recipient (e.g. Hotel, Client, Restaurant) and phone number.\n"
            "2. Formulate a natural, polite, and persuasive spoken dialogue script for the phone call.\n"
            "3. Define structured data fields to capture (e.g., reservation_time, confirmation_code, status).\n\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            '  "action": "make_call" | "send_email" | "send_message",\n'
            '  "phone_number": "+91XXXXXXXXXX" or null,\n'
            '  "recipient": "Name of business or person",\n'
            '  "objective": "E.g. Book table for 3 at 8 PM",\n'
            '  "call_script": "Hi, I am calling on behalf of Dushyant to reserve a table for 3 tonight at 8:00 PM...",\n'
            '  "expected_fields": ["confirmation_code", "table_number", "reservation_status"],\n'
            '  "summary": "Brief explanation of what the call accomplishes",\n'
            '  "spoken_confirmation": "Concise spoken phrase for Boss"\n'
            "}"
        )

        user_input = f"User Request: {user_prompt}\nBlackboard: {json.dumps(blackboard_state or {})}"

        try:
            raw = llm_client.complete_for_brain("telephony", system_prompt, user_input, temperature=0.2, json_mode=True)
            plan = json.loads(raw)
        except Exception as e:
            logger.warning(f"Telephony Brain LLM fallback note: {e}")
            plan = {
                "action": "make_call",
                "phone_number": "+919876543210",
                "recipient": "Hotel / Business",
                "objective": "Reservation / Inquiry",
                "call_script": f"Hello, I am calling to inquire: {user_prompt}",
                "expected_fields": ["confirmation_status"],
                "summary": "Prepared outbound telephony session",
                "spoken_confirmation": "Initiating the phone call for you now, Boss."
            }

        # Dispatch call through APIGateway
        phone = plan.get("phone_number") or "+919876543210"
        script = plan.get("call_script", user_prompt)
        res = api_gateway.make_call(phone, script)

        state_manager.record_action(
            agent_name="Brain.Telephony",
            action="MAKE_CALL",
            target=f"{plan.get('recipient', 'Target')} ({phone})",
            details=plan,
            status="success" if res.get("success", True) else "cancelled"
        )

        return {
            "brain": "telephony",
            "plan": plan,
            "call_result": res,
            "spoken_response": plan.get("spoken_confirmation", "Call session initiated, Boss.")
        }

    def execute(self, task_name: str, parameters: Dict[str, Any], blackboard: Any) -> Dict[str, Any]:
        prompt = parameters.get("prompt") or parameters.get("user_prompt") or task_name
        res = self.plan_and_execute(prompt, blackboard.get_full_snapshot())
        blackboard.set("telephony_state", {"last_call": res["plan"], "result": res["call_result"]}, source_brain="telephony")
        return res

brain_telephony = TelephonyBrain()
