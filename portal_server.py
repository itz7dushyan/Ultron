import json
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from tools.system_telemetry import system_telemetry
from shared_state.state_manager import state_manager
from agents.manager import manager_agent
from config import PROJECT_ROOT

PORTAL_DIR = PROJECT_ROOT / "portal"

class UltronPortalHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler serving Ultron Web HUD and JSON APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PORTAL_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/vitals":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            vitals = system_telemetry.get_system_vitals()
            self.wfile.write(json.dumps(vitals).encode("utf-8"))
            return

        elif self.path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            events = state_manager.get_history(limit=10)
            self.wfile.write(json.dumps(events, default=str).encode("utf-8"))
            return

        # Serve static portal files
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/command":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                payload = json.loads(post_data)
                command = payload.get("command", "")
                result = manager_agent.handle_user_command(command)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, default=str).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def start_server(port: int = 8080, open_browser: bool = True):
    """Starts the local Web HUD server and optionally launches browser."""
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, UltronPortalHandler)
    url = f"http://localhost:{port}"
    print(f"\n========================================================")
    print(f"      ULTRON WEB HUD PORTAL ACTIVE AT: {url}")
    print(f"========================================================\n")
    
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nUltron Web HUD stopped.")
        httpd.server_close()

if __name__ == "__main__":
    start_server()
