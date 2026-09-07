import time
import logging
import threading
from typing import Dict, Any, Optional
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.WhatsAppControl")

class WhatsAppControl:
    """
    Automated WhatsApp Desktop & Incoming Call Management Daemon.
    Handles:
    - Auto-detecting incoming voice/video calls when in 'Busy' mode.
    - Declining calls and dispatching automated replies.
    - Sending messages to contacts on command.
    """

    def __init__(self):
        self.is_busy_mode = False
        self.busy_reply_message = "I'm busy right now, talk later."
        self._listener_thread = None
        self._running = False

    def set_busy_mode(self, enabled: bool = True, custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Activates or deactivates auto-call decline and busy message mode."""
        self.is_busy_mode = enabled
        if custom_message:
            self.busy_reply_message = custom_message
        
        if enabled and not self._running:
            self.start_call_listener()
        elif not enabled and self._running:
            self.stop_call_listener()

        state_manager.record_action(
            "WhatsAppControl",
            "SET_BUSY_MODE",
            target=str(enabled),
            details={"reply_message": self.busy_reply_message},
            status="success"
        )
        return {
            "success": True,
            "busy_mode": self.is_busy_mode,
            "reply_message": self.busy_reply_message,
            "message": f"WhatsApp Busy Mode {'ENABLED' if enabled else 'DISABLED'}."
        }

    def start_call_listener(self):
        """Starts background thread monitoring for incoming calls."""
        if self._running:
            return
        self._running = True
        self._listener_thread = threading.Thread(target=self._call_monitor_loop, daemon=True)
        self._listener_thread.start()
        logger.info("WhatsApp Call Monitor Daemon started in background.")

    def stop_call_listener(self):
        """Stops background call monitor."""
        self._running = False

    def _call_monitor_loop(self):
        """Monitors for incoming WhatsApp call windows and handles them."""
        import pyautogui
        while self._running:
            if self.is_busy_mode:
                try:
                    # Look for active WhatsApp windows or call indicators
                    windows = pyautogui.getWindowsWithTitle("WhatsApp")
                    for win in windows:
                        title_lower = win.title.lower()
                        if "incoming" in title_lower or "voice call" in title_lower or "video call" in title_lower:
                            logger.info(f"Incoming call detected on window: {win.title}")
                            self._handle_incoming_call(win)
                except Exception as e:
                    logger.debug(f"Call monitor note: {e}")
            time.sleep(1.0)

    def _handle_incoming_call(self, window):
        """Declines call and sends busy message."""
        try:
            import pyautogui
            # Focus call window and decline (e.g. Escape or hotkey)
            window.activate()
            time.sleep(0.3)
            pyautogui.press('esc')
            time.sleep(0.5)

            # Send automated message
            self.send_whatsapp_message(message=self.busy_reply_message)
            state_manager.record_action(
                "WhatsAppControl",
                "DECLINED_INCOMING_CALL",
                target=window.title,
                details={"sent_message": self.busy_reply_message},
                status="success"
            )
        except Exception as e:
            logger.warning(f"Failed to auto-decline call: {e}")

    def send_whatsapp_message(self, contact_name: Optional[str] = None, message: str = "") -> Dict[str, Any]:
        """Types and sends a message in active or targeted WhatsApp chat."""
        try:
            import pyautogui
            if contact_name:
                # Search contact via Ctrl+F / Ctrl+N
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.3)
                pyautogui.write(contact_name, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)

            # Type message and hit Enter
            pyautogui.write(message, interval=0.02)
            time.sleep(0.2)
            pyautogui.press('enter')

            state_manager.record_action(
                "WhatsAppControl",
                "SEND_MESSAGE",
                target=contact_name or "Active Chat",
                details={"message": message},
                status="success"
            )
            return {"success": True, "target": contact_name, "message": message}
        except Exception as e:
            logger.error(f"WhatsApp send message failed: {e}")
            return {"success": False, "error": str(e)}

whatsapp_control = WhatsAppControl()
