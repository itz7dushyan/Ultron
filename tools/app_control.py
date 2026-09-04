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
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "vscode": "code.cmd",
    "code": "code.cmd",
    "spotify": "spotify.exe",
    "proton": "ProtonVPN.Launcher.exe",
    "proton vpn": "ProtonVPN.Launcher.exe",
    "protonvpn": "ProtonVPN.Launcher.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe"
}

SPOTIFY_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft\\WindowsApps\\Spotify.exe",
    Path(os.environ.get("APPDATA", "")) / "Spotify\\Spotify.exe",
    "spotify:"
]

PROTON_PATHS = [
    Path("C:\\Program Files\\Proton\\VPN\\ProtonVPN.Launcher.exe"),
    Path("C:\\Program Files\\Proton\\VPN\\v4.4.1\\ProtonVPN.Client.exe"),
    Path("C:\\Program Files\\Proton\\VPN\\v4.3.14\\ProtonVPN.Client.exe")
]

class AppTools:
    """Windows Application Controller for opening and closing apps without delay."""

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
        """Search common Windows Start Menu shortcut folders with fuzzy token matching."""
        search_dirs = [
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Microsoft\\Windows\\Start Menu\\Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft\\Windows\\Start Menu\\Programs"
        ]
        query = app_name.lower().replace(".exe", "").strip()
        tokens = [t for t in query.split() if len(t) > 2]

        candidates = []
        for base in search_dirs:
            if not base.exists():
                continue
            for shortcut in base.rglob("*.lnk"):
                stem = shortcut.stem.lower()
                # Exact match
                if query == stem:
                    return shortcut
                # Substring match
                if query in stem:
                    candidates.append((1, shortcut))
                # Token match
                elif tokens and any(t in stem for t in tokens):
                    candidates.append((2, shortcut))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None

    def _find_in_windows_apps(self, app_name: str) -> Optional[Path]:
        """Search Microsoft WindowsApps folder for UWP and Store apps."""
        winapps = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft\\WindowsApps"
        if not winapps.exists():
            return None
        query = app_name.lower().replace(".exe", "").strip()
        for exe in winapps.glob("*.exe"):
            if query in exe.stem.lower():
                return exe
        return None

    def _clean_app_name(self, raw_name: str) -> str:
        """Strips conversational noise and verbs from user speech."""
        name = raw_name.lower().strip()
        for noise in ("please open", "open", "launch", "start", "run", "kholo", "chalao", "app", "application", "the"):
            if name.startswith(noise + " "):
                name = name[len(noise) + 1:].strip()
            elif name.endswith(" " + noise):
                name = name[:-len(noise) - 1].strip()
        return name.strip()

    def open_app(self, app_name: str) -> Dict[str, Any]:
        """
        Launches an application by name or common alias.
        """
        clean_name = self._clean_app_name(app_name)

        try:
            # 1. Specialized: Spotify
            if "spotify" in clean_name:
                for candidate in SPOTIFY_PATHS:
                    if isinstance(candidate, str) and candidate.startswith("spotify:"):
                        os.startfile(candidate)
                        state_manager.record_action("AppTools", "OPEN_APP", "spotify:", status="success")
                        return {"success": True, "target": "spotify:", "message": "Launched Spotify, Boss."}
                    elif isinstance(candidate, Path) and candidate.exists():
                        subprocess.Popen([str(candidate)], shell=False)
                        state_manager.record_action("AppTools", "OPEN_APP", str(candidate), status="success")
                        return {"success": True, "target": str(candidate), "message": "Launched Spotify, Boss."}

            # 2. Specialized: Proton VPN
            if "proton" in clean_name:
                for p_candidate in PROTON_PATHS:
                    if p_candidate.exists():
                        subprocess.Popen([str(p_candidate)], shell=False)
                        state_manager.record_action("AppTools", "OPEN_APP", str(p_candidate), status="success")
                        return {"success": True, "target": str(p_candidate), "message": "Launched Proton VPN, Boss."}

            # 3. Specialized: File Explorer
            if clean_name in ("file explorer", "explorer", "folder"):
                subprocess.Popen(["explorer.exe"], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", "explorer.exe", status="success")
                return {"success": True, "target": "explorer.exe", "message": "Opened File Explorer, Boss."}

            target = COMMON_APPS.get(clean_name, clean_name)

            # 4. Check if it's a protocol (e.g. ms-settings:)
            if ":" in target and not Path(target).is_absolute():
                os.startfile(target)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Opened {app_name}, Boss."}

            # 5. Check if registered in Windows App Paths
            reg_path = self._find_in_registry(target)
            if reg_path:
                subprocess.Popen([reg_path], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", reg_path, status="success")
                return {"success": True, "target": reg_path, "message": f"Launched {app_name}, Boss."}

            # 6. Check Start Menu shortcuts
            shortcut = self._find_in_start_menu(clean_name)
            if shortcut:
                os.startfile(str(shortcut))
                state_manager.record_action("AppTools", "OPEN_APP", str(shortcut), status="success")
                return {"success": True, "target": str(shortcut), "message": f"Launched {app_name}, Boss."}

            # 7. Check WindowsApps folder (UWP/Store apps)
            win_app = self._find_in_windows_apps(clean_name)
            if win_app:
                subprocess.Popen([str(win_app)], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", str(win_app), status="success")
                return {"success": True, "target": str(win_app), "message": f"Launched {app_name}, Boss."}

            # 8. Fallback: try direct startfile or shell launch
            try:
                os.startfile(target)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Launched {app_name}, Boss."}
            except Exception:
                subprocess.Popen(["powershell", "-Command", f"Start-Process '{target}'"], shell=False)
                state_manager.record_action("AppTools", "OPEN_APP", target, status="success")
                return {"success": True, "target": target, "message": f"Triggered launch of {app_name}, Boss."}

        except Exception as e:
            state_manager.record_action("AppTools", "OPEN_APP", app_name, details=str(e), status="failed")
            return {"success": False, "error": f"Failed to open {app_name}: {str(e)}"}

    def close_app(self, app_name: str) -> Dict[str, Any]:
        """
        Terminates running processes or closes active windows matching app_name.
        """
        clean_name = app_name.strip().lower()

        # 1. Close Active Tab (Ctrl+W)
        if clean_name in ("tab", "current tab", "this tab", "browser tab", "active tab"):
            return self.close_active_tab()

        # 2. Close Active Window (Alt+F4)
        if clean_name in ("window", "active window", "current window", "this window"):
            return self.close_active_window()

        # 3. Close File Explorer folder windows (without killing desktop shell!)
        if clean_name in ("file explorer", "explorer", "folder windows", "folders", "explorer.exe"):
            return self.close_file_explorer_windows()

        # 4. Specialized: Close Proton VPN
        if "proton" in clean_name:
            terminated = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if "proton" in proc.info['name'].lower():
                        proc.terminate()
                        terminated.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            state_manager.record_action("AppTools", "CLOSE_APP", "ProtonVPN", status="success")
            return {"success": True, "message": "Closed Proton VPN, Boss."}

        # 5. Specialized: Close Spotify
        if "spotify" in clean_name:
            terminated = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if "spotify" in proc.info['name'].lower():
                        proc.terminate()
                        terminated.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            state_manager.record_action("AppTools", "CLOSE_APP", "Spotify", status="success")
            return {"success": True, "message": "Closed Spotify, Boss."}

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
                return {"success": True, "message": f"Closed {app_name}, Boss."}
            else:
                return {"success": False, "message": f"No running process found for {app_name}, Boss."}
        except Exception as e:
            state_manager.record_action("AppTools", "CLOSE_APP", app_name, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def close_active_tab(self) -> Dict[str, Any]:
        """Closes the current active browser or editor tab using Ctrl+W."""
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'w')
            state_manager.record_action("AppTools", "CLOSE_TAB", "active_tab", status="success")
            return {"success": True, "message": "Closed current tab, Boss."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_active_window(self) -> Dict[str, Any]:
        """Closes the current active window using Alt+F4."""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            state_manager.record_action("AppTools", "CLOSE_WINDOW", "active_window", status="success")
            return {"success": True, "message": "Closed active window, Boss."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_file_explorer_windows(self) -> Dict[str, Any]:
        """Closes open File Explorer folder windows via Shell COM without terminating the Windows taskbar shell."""
        try:
            cmd = (
                "powershell -Command "
                "\"(New-Object -ComObject Shell.Application).Windows() | "
                "Where-Object { $_.Name -like '*Explorer*' } | ForEach-Object { $_.Quit() }\""
            )
            subprocess.run(cmd, shell=True, timeout=5)
            state_manager.record_action("AppTools", "CLOSE_APP", "File Explorer Windows", status="success")
            return {"success": True, "message": "Closed open File Explorer windows, Boss."}
        except Exception as e:
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
