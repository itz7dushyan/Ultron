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

class WakeDetector:
    """
    Continuous passive voice listener and wake word detector for Ultron.
    Listens for 'Ultron' or 'Wake up' on the microphone with automatic ambient noise calibration.
    """

    def __init__(self):
        self.is_listening = False
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
            
            # Calibrate against ambient room noise so normal speaking voice is heard
            try:
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
            except Exception:
                pass

            # Ensure optimal sensitivity
            if self._recognizer.energy_threshold > 250:
                self._recognizer.energy_threshold = 160
            elif self._recognizer.energy_threshold < 60:
                self._recognizer.energy_threshold = 80

            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.6
            logger.info(f"Ultron Microphone calibrated (threshold={self._recognizer.energy_threshold:.1f})")
        except Exception as e:
            logger.warning(f"Voice input initialization notice: {e}")

    def _play_chime(self):
        """Plays a quick futuristic alert tone on wake detection."""
        try:
            import winsound
            winsound.Beep(1200, 100)
        except Exception:
            pass

    def is_wake_phrase(self, text: str) -> Tuple[bool, str]:
        """
        Checks if the recognized text contains any wake word or variant.
        Returns (is_wake, remaining_command).
        """
        cleaned = text.lower().strip()
        for variant in WAKE_VARIANTS:
            if variant in cleaned:
                # Extract any command spoken in the same sentence
                parts = cleaned.split(variant, 1)
                remaining = parts[1].strip(" ,.?!") if len(parts) > 1 else ""
                # If remaining is just another wake word variant, clear it
                if remaining in WAKE_VARIANTS:
                    remaining = ""
                return True, remaining
        return False, ""

    def listen_single_phrase(self, timeout: int = 4, phrase_time_limit: int = 7) -> Optional[str]:
        """Listens for a single speech phrase from the microphone."""
        if not self._recognizer or not self._microphone:
            self._init_audio()
            if not self._recognizer or not self._microphone:
                return None

        import speech_recognition as sr
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            # Fast Google Speech Recognition
            text = self._recognizer.recognize_google(audio, language="en-US")
            return text.strip()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            logger.debug(f"Audio recognition note: {e}")
            return None

    def start_background_listener(self, on_command_callback: Callable[[str], None], status_logger: Optional[Callable[[str], None]] = None):
        """
        Starts a background daemon thread that continuously listens for wake words
        and triggers on_command_callback when user speaks to Ultron.
        """
        if self.is_listening:
            return

        self.is_listening = True

        def loop():
            if status_logger:
                status_logger("[VOICE ACTIVE] Listening for 'Ultron' or 'Wake up' (normal speaking volume)...")

            while self.is_listening:
                try:
                    from voice.audio_engine import audio_engine
                    if getattr(audio_engine, 'is_speaking', False):
                        time.sleep(0.3)
                        continue

                    phrase = self.listen_single_phrase(timeout=3, phrase_time_limit=5)
                    if phrase:
                        is_wake, attached_cmd = self.is_wake_phrase(phrase)
                        if is_wake:
                            self._play_chime()
                            if status_logger:
                                status_logger(f"⚡ Wake word detected: '{phrase}'")

                            if attached_cmd:
                                # User said "Hey Ultron open YouTube"
                                on_command_callback(attached_cmd)
                            else:
                                # User just said "Hey Ultron" or "Wake up"
                                from voice.audio_engine import audio_engine
                                audio_engine.speak("Yes, Sir? I am listening.")
                                if status_logger:
                                    status_logger("● Listening for your command...")

                                follow_up = self.listen_single_phrase(timeout=5, phrase_time_limit=8)
                                if follow_up:
                                    if status_logger:
                                        status_logger(f"Received voice command: '{follow_up}'")
                                    on_command_callback(follow_up)
                                else:
                                    audio_engine.speak("Standing by.")
                except Exception as e:
                    logger.debug(f"Background listener loop notice: {e}")
                time.sleep(0.2)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_background_listener(self):
        """Stops the continuous listening background thread."""
        self.is_listening = False

wake_detector = WakeDetector()
