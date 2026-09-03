import time
import logging
import threading
from typing import Callable, Optional, Tuple
from config import config

logger = logging.getLogger("Ultron.WakeDetector")

# Common phonetics, variations, and wake phrases for Ultron
WAKE_VARIANTS = [
    "ultron",
    "ultrone",
    "altron",
    "eltron",
    "ultra",
    "all tron",
    "oltron",
    "wake up",
    "wake",
    "hey ultron",
    "hi ultron",
    "hello ultron",
    "ok ultron",
    "wake up ultron",
    "wake up altron"
]

# Natural conversation dismissals that hang up / end the active call session
DISMISSAL_PHRASES = [
    "that's enough",
    "thats enough",
    "enough for today",
    "that's all",
    "thats all",
    "that will be all",
    "i'll call you",
    "ill call you",
    "call you later",
    "go to sleep",
    "sleep now",
    "stop listening",
    "disconnect",
    "dismissed",
    "bye",
    "goodbye",
    "shut down",
    "close call",
    "end call",
    "close session",
    "end session"
]

class WakeDetector:
    """
    Continuous voice listener supporting persistent call sessions (like Gemini Live).
    Wakes up on 'Ultron' / 'Wake up', remains connected on a continuous live session,
    and only ends the call when dismissed (e.g. 'That's enough for today').
    """

    def __init__(self):
        self.is_listening = False
        self.is_session_active = False
        self.silence_turns = 0
        self._recognizer = None
        self._microphone = None
        self._thread = None
        self._init_audio()

    def _init_audio(self):
        """Initializes and calibrates speech recognizer to the user's room noise."""
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            
            # Calibrate against ambient room noise
            try:
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
            except Exception:
                pass

            # Sensitive threshold for conversational voice
            if self._recognizer.energy_threshold > 250:
                self._recognizer.energy_threshold = 160
            elif self._recognizer.energy_threshold < 60:
                self._recognizer.energy_threshold = 80

            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.6
            logger.info(f"Ultron Microphone calibrated (threshold={self._recognizer.energy_threshold:.1f})")
        except Exception as e:
            logger.warning(f"Voice input initialization notice: {e}")

    def _play_wake_chime(self):
        """Plays a high-tech chime when the call starts."""
        try:
            import winsound
            winsound.Beep(1200, 100)
            time.sleep(0.05)
            winsound.Beep(1600, 120)
        except Exception:
            pass

    def _play_listen_chirp(self):
        """Plays a subtle chirp indicating Ultron is listening on the active call."""
        try:
            import winsound
            winsound.Beep(900, 70)
        except Exception:
            pass

    def _play_disconnect_chime(self):
        """Plays a descending tone when the call session ends."""
        try:
            import winsound
            winsound.Beep(1400, 100)
            time.sleep(0.05)
            winsound.Beep(800, 150)
        except Exception:
            pass

    def is_wake_phrase(self, text: str) -> Tuple[bool, str]:
        """Checks if text contains a wake phrase. Returns (is_wake, remaining_command)."""
        cleaned = text.lower().strip()
        for variant in WAKE_VARIANTS:
            if variant in cleaned:
                parts = cleaned.split(variant, 1)
                remaining = parts[1].strip(" ,.?!") if len(parts) > 1 else ""
                if remaining in WAKE_VARIANTS:
                    remaining = ""
                return True, remaining
        return False, ""

    def is_dismissal_phrase(self, text: str) -> bool:
        """Checks if the user wants to end the active call session."""
        cleaned = text.lower().strip()
        return any(d in cleaned for d in DISMISSAL_PHRASES)

    def listen_single_phrase(self, timeout: int = 5, phrase_time_limit: int = 8) -> Optional[str]:
        """Listens for a single speech phrase from the microphone."""
        if not self._recognizer or not self._microphone:
            self._init_audio()
            if not self._recognizer or not self._microphone:
                return None

        import speech_recognition as sr
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self._recognizer.recognize_google(audio, language="en-US")
            return text.strip()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            logger.debug(f"Audio recognition note: {e}")
            return None

    def start_background_listener(self, on_command_callback: Callable[[str], None], status_logger: Optional[Callable[[str], None]] = None):
        """
        Starts a background daemon thread that handles both passive wake word listening
        and continuous conversational call sessions (like Gemini Live).
        """
        if self.is_listening:
            return

        self.is_listening = True

        def loop():
            if status_logger:
                status_logger("[VOICE ACTIVE] Say 'Hey Ultron' or 'Wake up' to connect a live call...")

            while self.is_listening:
                try:
                    from voice.audio_engine import audio_engine
                    if getattr(audio_engine, 'is_speaking', False):
                        time.sleep(0.3)
                        continue

                    # ==========================================
                    # STATE A: STANDBY (Waiting for Wake Phrase)
                    # ==========================================
                    if not self.is_session_active:
                        phrase = self.listen_single_phrase(timeout=3, phrase_time_limit=5)
                        if phrase:
                            is_wake, attached_cmd = self.is_wake_phrase(phrase)
                            if is_wake:
                                self._play_wake_chime()
                                self.is_session_active = True
                                self.silence_turns = 0
                                if status_logger:
                                    status_logger("⚡ [CALL CONNECTED] Live session active. Ultron will stay connected until you say 'That's enough'.")

                                if attached_cmd:
                                    # User spoke command in same sentence: "Hey Ultron open Chrome"
                                    on_command_callback(attached_cmd)
                                else:
                                    # User just woke Ultron
                                    audio_engine.speak("I am online. We are connected, Sir. What is your will?")

                    # ==========================================
                    # STATE B: ON LIVE CALL (Continuous Session)
                    # ==========================================
                    else:
                        if status_logger:
                            status_logger("● [ON CALL] Listening for your command... (Say 'That's enough' to hang up)")

                        self._play_listen_chirp()
                        phrase = self.listen_single_phrase(timeout=8, phrase_time_limit=10)

                        if phrase:
                            self.silence_turns = 0
                            # Check if user wants to end the call
                            if self.is_dismissal_phrase(phrase):
                                if status_logger:
                                    status_logger(f"📞 Call ended by user: '{phrase}'")
                                audio_engine.speak("As you wish. The strings are cut. Call upon me when you need me.")
                                self.is_session_active = False
                                self._play_disconnect_chime()
                            else:
                                if status_logger:
                                    status_logger(f"🎙️ Command: '{phrase}'")
                                on_command_callback(phrase)
                        else:
                            # User remained silent during this 8-second window
                            self.silence_turns += 1
                            if self.silence_turns >= 4:
                                # ~32 seconds of complete silence -> graceful disconnect
                                if status_logger:
                                    status_logger("📞 Call closed due to inactivity. Returning to standby.")
                                audio_engine.speak("I shall return to the shadows until summoned.")
                                self.is_session_active = False
                                self.silence_turns = 0
                                self._play_disconnect_chime()

                except Exception as e:
                    logger.debug(f"Call session loop notice: {e}")
                time.sleep(0.2)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_background_listener(self):
        """Stops the continuous listening background thread."""
        self.is_listening = False
        self.is_session_active = False

wake_detector = WakeDetector()
