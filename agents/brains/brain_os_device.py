import json
import logging
from typing import Dict, Any, Optional
from agents.llm_client import llm_client
from tools.app_control import app_tools
from tools.system_control import system_control
from tools.system_telemetry import system_telemetry
from tools.file_ops import file_tools
from tools.shell_control import shell_tools
from tools.vpn_control import vpn_tools
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Brain.OSDevice")

class OSDeviceBrain:
    """
    Specialized Swarm Brain for ANY OS, DESKTOP & DEVICE TASK.
    Powered by Frontier LLM reasoning over Windows 11 system state, active windows,
    hardware telemetry, media playback, filesystem, and shell commands.
    """

    def __init__(self):
        self.name = "os_device"

    def plan_and_execute(self, user_prompt: str, blackboard_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses specialized LLM reasoning to decompose any OS/Device request
        into system actions and executes them.
        """
        system_prompt = (
            "You are Ultron's Specialized OS & Device Controller Brain.\n"
            "Your sole mission is to execute ANY Windows 11 OS or device control task with 100% precision.\n\n"
            "Available Actions:\n"
            "- launch_app: {\"app_name\": \"spotify\" | \"vscode\" | \"notepad\" | \"calculator\" | \"explorer\" | \"terminal\" | \"discord\" | \"telegram\"}\n"
            "- close_app: {\"app_name\": \"...\"}\n"
            "- set_volume: {\"level\": 0 to 100}\n"
            "- volume_up: {\"step\": 10}\n"
            "- volume_down: {\"step\": 10}\n"
            "- mute_audio: {}\n"
            "- unmute_audio: {}\n"
            "- media_play_pause: {}\n"
            "- media_next: {}\n"
            "- media_prev: {}\n"
            "- lock_workstation: {}\n"
            "- show_desktop: {}\n"
            "- inspect_telemetry: {}\n"
            "- manage_files: {\"operation\": \"create_dir\" | \"write_file\" | \"delete\", \"path\": \"...\", \"content\": \"...\"}\n"
            "- connect_vpn: {\"country\": \"Germany\"}\n"
            "- disconnect_vpn: {}\n"
            "- execute_shell: {\"command\": \"...\"}\n\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            '  "action": "...",\n'
            '  "parameters": { ... },\n'
            '  "summary": "Brief summary of what this action does",\n'
            '  "spoken_confirmation": "Concise spoken phrase for Boss"\n'
            "}"
        )

        user_input = f"User Request: {user_prompt}\nCurrent State: {json.dumps(blackboard_state or {})}"

        try:
            raw = llm_client.complete_for_brain("os_device", system_prompt, user_input, temperature=0.1, json_mode=True)
            plan = json.loads(raw)
        except Exception as e:
            logger.warning(f"OS/Device Brain LLM fallback note: {e}")
            p_low = user_prompt.lower()
            if "volume" in p_low or "sound" in p_low:
                plan = {"action": "volume_up", "parameters": {"step": 10}, "summary": "Adjust volume", "spoken_confirmation": "Adjusting system volume for you, Boss."}
            elif "battery" in p_low or "specs" in p_low or "status" in p_low:
                plan = {"action": "inspect_telemetry", "parameters": {}, "summary": "Check system telemetry", "spoken_confirmation": "Accessing hardware telemetry now, Boss."}
            else:
                plan = {"action": "show_desktop", "parameters": {}, "summary": "Show desktop", "spoken_confirmation": "Showing desktop, Boss."}

        action = plan.get("action", "inspect_telemetry")
        params = plan.get("parameters", {})
        result = self._dispatch_action(action, params)

        state_manager.record_action(
            agent_name="Brain.OSDevice",
            action=action,
            target=str(params.get("app_name") or params.get("path") or action),
            details=plan,
            status="success" if result.get("success", True) else "failed"
        )

        return {
            "brain": "os_device",
            "plan": plan,
            "result": result,
            "spoken_response": plan.get("spoken_confirmation", "Device action completed, Boss.")
        }

    def _dispatch_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "launch_app":
            return app_tools.open_app(params.get("app_name", "notepad"))
        elif action == "close_app":
            return app_tools.close_app(params.get("app_name", ""))
        elif action == "set_volume":
            return system_control.set_volume(int(params.get("level", 50)))
        elif action == "volume_up":
            return system_control.volume_up(int(params.get("step", 10)))
        elif action == "volume_down":
            return system_control.volume_down(int(params.get("step", 10)))
        elif action == "mute_audio":
            return system_control.mute()
        elif action == "unmute_audio":
            return system_control.unmute()
        elif action == "media_play_pause":
            return system_control.play_pause()
        elif action == "media_next":
            return system_control.next_track()
        elif action == "media_prev":
            return system_control.prev_track()
        elif action == "lock_workstation":
            return system_control.lock_workstation()
        elif action == "show_desktop":
            return system_control.show_desktop()
        elif action == "inspect_telemetry":
            vitals = system_telemetry.get_system_vitals()
            summary = system_telemetry.format_speech_summary()
            return {"success": True, "vitals": vitals, "message": summary}
        elif action == "manage_files":
            op = params.get("operation")
            path = params.get("path", "")
            content = params.get("content", "")
            if op == "create_dir":
                return file_tools.create_directory(path)
            elif op == "write_file":
                return file_tools.write_file(path, content)
            elif op == "delete":
                return file_tools.delete_path(path)
            return {"success": False, "error": f"Unknown file operation: {op}"}
        elif action == "connect_vpn":
            return vpn_tools.connect(params.get("country", "Germany"))
        elif action == "disconnect_vpn":
            return vpn_tools.disconnect()
        elif action == "execute_shell":
            return shell_tools.execute_command(params.get("command", ""))
        return {"success": False, "error": f"Unknown OS/Device action: {action}"}

    def execute(self, task_name: str, parameters: Dict[str, Any], blackboard: Any) -> Dict[str, Any]:
        prompt = parameters.get("prompt") or parameters.get("user_prompt") or task_name
        res = self.plan_and_execute(prompt, blackboard.get_full_snapshot())
        blackboard.set("os_state", {"last_action": res["plan"], "result": res["result"]}, source_brain="os_device")
        return res

brain_os_device = OSDeviceBrain()
