import subprocess
from typing import Dict, Any, Optional
from config import config
from shared_state.state_manager import state_manager
from tools.safety_sentinel import safety_sentinel

class ShellTools:
    """PowerShell execution sandbox with timeout and safety monitoring."""

    def execute_command(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes a shell command on Windows via PowerShell.
        """
        timeout_val = timeout or config.MAX_COMMAND_TIMEOUT_SECONDS

        # Security check: prompt user if dangerous
        if not safety_sentinel.authorize("SHELL_COMMAND", target=command, details=f"cwd={cwd}"):
            state_manager.record_action("ShellTools", "EXECUTE_COMMAND", command, details="User declined", status="cancelled")
            return {"success": False, "cancelled": True, "message": "Command execution cancelled by user"}

        try:
            # Use PowerShell on Windows
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command]
            
            process = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_val,
                encoding="utf-8",
                errors="replace"
            )

            success = process.returncode == 0
            state_manager.record_action(
                agent_name="ShellTools",
                action="EXECUTE_COMMAND",
                target=command[:80],
                details={"exit_code": process.returncode, "stdout_len": len(process.stdout)},
                status="success" if success else "error"
            )

            return {
                "success": success,
                "exit_code": process.returncode,
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip()
            }
        except subprocess.TimeoutExpired:
            state_manager.record_action("ShellTools", "EXECUTE_COMMAND", command, details="Command timed out", status="timeout")
            return {"success": False, "error": f"Command timed out after {timeout_val} seconds"}
        except Exception as e:
            state_manager.record_action("ShellTools", "EXECUTE_COMMAND", command, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

shell_tools = ShellTools()
