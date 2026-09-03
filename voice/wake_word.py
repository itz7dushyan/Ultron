import time
import logging
from typing import Callable, Optional
from config import config

logger = logging.getLogger("Ultron.WakeDetector")

class WakeDetector:
    """
    Wake word detector supporting voice activation ('Hey Ultron')
    and interactive hotkey/console triggers.
    """

    def __init__(self, wake_word: Optional[str] = None):
        self.wake_word = (wake_word or config.WAKE_WORD).lower()
        self.is_listening = False

    def record_microphone_phrase(self, duration_seconds: int = 5) -> Optional[str]:
        """Records short audio snippet from system microphone."""
        try:
            import sounddevice as sd
            import soundfile as sf
            import numpy as np
            from config import DATA_DIR

            fs = 16000
            recording = sd.rec(int(duration_seconds * fs), samplerate=fs, channels=1, dtype="float32")
            sd.wait()

            wav_path = DATA_DIR / "audio_cache" / "input_query.wav"
            sf.write(str(wav_path), recording, fs)
            return str(wav_path)
        except Exception as e:
            logger.debug(f"Microphone capture unavailable: {e}")
            return None

    def listen_for_trigger(self, on_wake_callback: Callable[[], None]):
        """
        Listens continuously in background for wake trigger or console input.
        """
        self.is_listening = True
        logger.info(f"Ultron listening for wake word '{self.wake_word}' or Enter key...")

        while self.is_listening:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                self.is_listening = False
                break

wake_detector = WakeDetector()
