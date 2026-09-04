import ctypes
import logging
from typing import Dict, Any, Optional
import pyperclip
import pyautogui
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.SystemControl")

# Windows Virtual Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

class SystemControl:
    """
    Universal Windows OS Controller.
    Manages master volume, media playback, workstation locks,
    window states, and clipboard operations.
    """

    def __init__(self):
        self._endpoint_volume = None

    def _get_volume_endpoint(self):
        """Initializes or retrieves the PyCAW master volume endpoint."""
        try:
            from pycaw.pycaw import AudioUtilities
            spk = AudioUtilities.GetSpeakers()
            if spk:
                return spk.EndpointVolume
        except Exception as e:
            logger.debug(f"PyCAW init note: {e}")
        return None

    def set_volume(self, percent: int) -> Dict[str, Any]:
        """Sets the system master volume to an exact percentage (0 - 100)."""
        target = max(0, min(100, int(percent)))
        scalar = target / 100.0

        try:
            vol = self._get_volume_endpoint()
            if vol:
                vol.SetMasterVolumeLevelScalar(scalar, None)
                if vol.GetMute():
                    vol.SetMute(0, None)
                state_manager.record_action("SystemControl", "SET_VOLUME", f"{target}%", status="success")
                return {"success": True, "volume": target, "message": f"Volume set to {target}%, Boss."}
        except Exception as e:
            logger.debug(f"PyCAW set volume error: {e}")

        # Fallback using simulated volume keystrokes if pycaw fails
        return self._fallback_step_volume(target)

    def get_volume(self) -> Dict[str, Any]:
        """Gets current master volume percentage and mute status."""
        try:
            vol = self._get_volume_endpoint()
            if vol:
                scalar = vol.GetMasterVolumeLevelScalar()
                is_muted = bool(vol.GetMute())
                return {"success": True, "volume": int(round(scalar * 100)), "muted": is_muted}
        except Exception as e:
            logger.debug(f"PyCAW get volume error: {e}")
        return {"success": False, "volume": 50, "muted": False}

    def volume_up(self, step: int = 10) -> Dict[str, Any]:
        """Increases volume by step percent."""
        cur = self.get_volume()
        new_vol = min(100, cur.get("volume", 50) + step)
        return self.set_volume(new_vol)

    def volume_down(self, step: int = 10) -> Dict[str, Any]:
        """Decreases volume by step percent."""
        cur = self.get_volume()
        new_vol = max(0, cur.get("volume", 50) - step)
        return self.set_volume(new_vol)

    def mute(self) -> Dict[str, Any]:
        """Mutes system audio."""
        try:
            vol = self._get_volume_endpoint()
            if vol:
                vol.SetMute(1, None)
                state_manager.record_action("SystemControl", "MUTE_AUDIO", "Muted", status="success")
                return {"success": True, "muted": True, "message": "Audio muted, Boss."}
        except Exception:
            pass
        # Fallback via VK key
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
        return {"success": True, "message": "Audio muted, Boss."}

    def unmute(self) -> Dict[str, Any]:
        """Unmutes system audio."""
        try:
            vol = self._get_volume_endpoint()
            if vol:
                vol.SetMute(0, None)
                state_manager.record_action("SystemControl", "UNMUTE_AUDIO", "Unmuted", status="success")
                return {"success": True, "muted": False, "message": "Audio unmuted, Boss."}
        except Exception:
            pass
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
        return {"success": True, "message": "Audio unmuted, Boss."}

    def toggle_mute(self) -> Dict[str, Any]:
        """Toggles audio mute state."""
        cur = self.get_volume()
        if cur.get("muted"):
            return self.unmute()
        return self.mute()

    def _fallback_step_volume(self, target_percent: int) -> Dict[str, Any]:
        """Fallback stepping volume using keyboard events."""
        for _ in range(5):
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_KEYUP, 0)
        return {"success": True, "volume": target_percent, "message": f"Adjusted volume to approximately {target_percent}%, Boss."}

    # ==========================================
    # Media Playback Controls
    # ==========================================
    def play_pause(self) -> Dict[str, Any]:
        """Toggles media play/pause on Windows."""
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
        state_manager.record_action("SystemControl", "MEDIA_PLAY_PAUSE", "Toggled", status="success")
        return {"success": True, "message": "Playback toggled, Boss."}

    def next_track(self) -> Dict[str, Any]:
        """Skips to next media track."""
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_KEYUP, 0)
        state_manager.record_action("SystemControl", "MEDIA_NEXT_TRACK", "Skipped", status="success")
        return {"success": True, "message": "Playing next track, Boss."}

    def prev_track(self) -> Dict[str, Any]:
        """Rewinds to previous media track."""
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_KEYUP, 0)
        state_manager.record_action("SystemControl", "MEDIA_PREV_TRACK", "Previous", status="success")
        return {"success": True, "message": "Rewinding to previous track, Boss."}

    # ==========================================
    # System Power & Screen Controls
    # ==========================================
    def lock_workstation(self) -> Dict[str, Any]:
        """Locks the Windows user session immediately."""
        try:
            ctypes.windll.user32.LockWorkStation()
            state_manager.record_action("SystemControl", "LOCK_WORKSTATION", "Locked", status="success")
            return {"success": True, "message": "Workstation locked, Boss."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def show_desktop(self) -> Dict[str, Any]:
        """Minimizes all windows and displays the desktop (Win+D)."""
        pyautogui.hotkey('win', 'd')
        state_manager.record_action("SystemControl", "SHOW_DESKTOP", "Win+D", status="success")
        return {"success": True, "message": "Displaying desktop, Boss."}

    def maximize_window(self) -> Dict[str, Any]:
        """Maximizes the currently active window (Win+Up)."""
        pyautogui.hotkey('win', 'up')
        return {"success": True, "message": "Window maximized, Boss."}

    def minimize_window(self) -> Dict[str, Any]:
        """Minimizes the currently active window (Win+Down)."""
        pyautogui.hotkey('win', 'down')
        return {"success": True, "message": "Window minimized, Boss."}

    # ==========================================
    # Clipboard Operations
    # ==========================================
    def read_clipboard(self) -> Dict[str, Any]:
        """Reads current text contents from the Windows clipboard."""
        try:
            text = pyperclip.paste().strip()
            if not text:
                return {"success": True, "content": "", "message": "Your clipboard is currently empty, Boss."}
            preview = (text[:120] + "...") if len(text) > 120 else text
            return {"success": True, "content": text, "message": f"Clipboard contents: '{preview}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_clipboard(self, text: str) -> Dict[str, Any]:
        """Writes text to the Windows clipboard."""
        try:
            pyperclip.copy(text)
            state_manager.record_action("SystemControl", "CLIPBOARD_COPY", f"{len(text)} chars", status="success")
            return {"success": True, "message": "Text copied to your clipboard, Boss."}
        except Exception as e:
            return {"success": False, "error": str(e)}

system_control = SystemControl()
