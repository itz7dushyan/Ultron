import os
import winreg
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from shared_state.state_manager import state_manager

# Common application aliases on Windows
COMMON_APPS = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "firefox": "firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "vscode": "code.cmd",
    "code": "code.cmd",
    "spotify": "spotify.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe"
}

class AppTools:
    """Windows Application Controller for opening and closing apps without screenshot delay."""

    def _find_in_registry(self, app_name: str) -> Optional[str]:
        """Search Windows App Paths registry for the executable."""
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths")
        ]
        exe_candidate = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
        
        for root_key, subkey_path in keys:
            try:
                with winreg.OpenKey(root_key, f"{subkey_path}\\{exe_candidate}") as key:
                    path, _ = winreg.QueryValueEx(key, "")
                    if path and os.path.exists(path):
                        return path
            except (FileNotFoundError, OSError):
                continue
        return None

    def _find_in_start_menu(self, app_name: str) -> Optional[Path]:
        """Search common Windows Start Menu shortcut folders."""
        search_dirs = [
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs"
        ]
        query = app_name.lower().replace(".exe", "")
        for base in search_dirs:
            if not base.exists():
                continue
            for shortcut in base.rglob("*.lnk"):
                if query in shortcut.stem.lower():
                    return shortcut
        return None

    def open_app(self, app_name: str) -> Dict[str, Any]:
        """
        Launches an application by name or common alias.
        """
        clean_name = app_name.strip().lower()
        target = COMMON_APPS.get(clean_name, app_name)

        try:
            # 1. Check if it's a protocol (e.g. ms-settings:)
            if ":" in target and not Path(target).is_absolute():
                os.startfile(target)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Opened {app_name}"}

            # 2. Check if registered in Windows App Paths
            reg_path = self._find_in_registry(target)
            if reg_path:
                subprocess.Popen([reg_path], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", reg_path, status="success")
                return {"success": True, "target": reg_path, "message": f"Launched {app_name}"}

            # 3. Check Start Menu shortcuts
            shortcut = self._find_in_start_menu(clean_name)
            if shortcut:
                os.startfile(str(shortcut))
                state_manager.record_action("AppTools", "OPEN_APP", str(shortcut), status="success")
                return {"success": True, "target": str(shortcut), "message": f"Launched shortcut for {app_name}"}

            # 4. Fallback: try direct startfile or shell launch
            try:
                os.startfile(target)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Launched {app_name}"}
            except Exception:
                # 5. Last fallback: powershell Start-Process
                subprocess.Popen(["powershell", "-Command", f"Start-Process '{target}'"], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Triggered launch of {app_name}"}

        except Exception as e:
            state_manager.record_action("AppTools", "OPEN_APP", app_name, details=str(e), status="failed")
            return {"success": False, "error": f"Failed to open {app_name}: {str(e)}"}

    def close_app(self, app_name: str) -> Dict[str, Any]:
        """
        Terminates running processes matching the given app name.
        """
        clean_name = app_name.strip().lower()
        target = COMMON_APPS.get(clean_name, clean_name)
        if not target.endswith(".exe"):
            target = f"{target}.exe"

        terminated_pids = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if target in proc_name or clean_name in proc_name:
                        proc.terminate()
                        terminated_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if terminated_pids:
                state_manager.record_action("AppTools", "CLOSE_APP", app_name, details={"pids": terminated_pids}, status="success")
                return {"success": True, "message": f"Closed {app_name} (terminated {len(terminated_pids)} process instances)"}
            else:
                return {"success": False, "message": f"No running processes found matching {app_name}"}
        except Exception as e:
            state_manager.record_action("AppTools", "CLOSE_APP", app_name, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def list_running_apps(self) -> List[Dict[str, Any]]:
        """Returns a summarized list of running processes."""
        running = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and not name.startswith("System") and not name.startswith("svchost"):
                    running.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(list(running))

app_tools = AppTools()
