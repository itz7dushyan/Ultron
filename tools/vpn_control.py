import subprocess
from typing import Dict, Any, Optional
from config import config
from shared_state.state_manager import state_manager
from tools.app_control import app_tools

class VPNTools:
    """VPN connection controller supporting multiple protocols and providers."""

    COUNTRY_CODES = {
        "germany": "DE",
        "united states": "US",
        "usa": "US",
        "united kingdom": "UK",
        "uk": "UK",
        "india": "IN",
        "japan": "JP",
        "singapore": "SG",
        "canada": "CA",
        "france": "FR",
        "netherlands": "NL"
    }

    def connect(self, country_or_server: str) -> Dict[str, Any]:
        """
        Connects to a VPN server in the requested country.
        """
        clean_target = country_or_server.strip().lower()
        vpn_type = config.VPN_TYPE.lower()
        state_manager.record_action("VPNTools", "CONNECT_VPN_REQUEST", country_or_server)

        try:
            # 1. ProtonVPN (CLI or Official Launcher)
            if "proton" in clean_target or "proton" in vpn_type:
                launcher = Path("C:\\Program Files\\Proton\\VPN\\ProtonVPN.Launcher.exe")
                if launcher.exists():
                    subprocess.Popen([str(launcher)], shell=False)
                    state_manager.record_action("VPNTools", "LAUNCH_PROTONVPN", str(launcher), status="success")
                    return {"success": True, "provider": "ProtonVPN", "message": "Launched Proton VPN application, Boss."}

                code = self.COUNTRY_CODES.get(clean_target, clean_target.upper())
                cmd = ["protonvpn-cli", "c", "--cc", code]
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                    success = res.returncode == 0
                    state_manager.record_action("VPNTools", "CONNECT_PROTONVPN", code, status="success" if success else "failed")
                    return {"success": success, "provider": "ProtonVPN", "output": res.stdout or res.stderr}
                except Exception:
                    pass

            # 2. NordVPN CLI
            elif "nord" in vpn_type:
                cmd = ["nordvpn", "-c", "-g", clean_target]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                success = res.returncode == 0
                state_manager.record_action("VPNTools", "CONNECT_NORDVPN", clean_target, status="success" if success else "failed")
                return {"success": success, "provider": "NordVPN", "output": res.stdout or res.stderr}

            # 3. Windows Native rasdial
            elif "rasdial" in vpn_type or "windows" in vpn_type:
                conn_name = config.VPN_CONNECTION_NAME or clean_target
                cmd = f"rasdial \"{conn_name}\""
                res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=15)
                success = res.returncode == 0
                state_manager.record_action("VPNTools", "CONNECT_RASDIAL", conn_name, status="success" if success else "failed")
                return {"success": success, "provider": "Windows rasdial", "connection": conn_name, "output": res.stdout or res.stderr}

            # 4. Fallback: Launch VPN GUI app directly
            else:
                app_launch = app_tools.open_app(vpn_type)
                state_manager.record_action("VPNTools", "LAUNCH_VPN_APP", vpn_type, status="success" if app_launch.get("success") else "failed")
                return {
                    "success": app_launch.get("success", False),
                    "message": f"Opened {vpn_type} application. Please select {country_or_server} in the interface.",
                    "details": app_launch
                }

        except Exception as e:
            state_manager.record_action("VPNTools", "CONNECT_VPN", country_or_server, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def disconnect(self) -> Dict[str, Any]:
        """Disconnects the active VPN connection."""
        vpn_type = config.VPN_TYPE.lower()
        try:
            if "proton" in vpn_type:
                subprocess.run(["protonvpn-cli", "d"], capture_output=True, text=True, timeout=15)
            elif "nord" in vpn_type:
                subprocess.run(["nordvpn", "-d"], capture_output=True, text=True, timeout=15)
            else:
                conn_name = config.VPN_CONNECTION_NAME
                subprocess.run(["powershell", "-Command", f"rasdial \"{conn_name}\" /disconnect"], capture_output=True, text=True, timeout=15)

            state_manager.record_action("VPNTools", "DISCONNECT_VPN", status="success")
            return {"success": True, "message": "VPN disconnected successfully"}
        except Exception as e:
            state_manager.record_action("VPNTools", "DISCONNECT_VPN", details=str(e), status="failed")
            return {"success": False, "error": str(e)}

vpn_tools = VPNTools()
