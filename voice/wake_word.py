import time
import logging
import threading
from typing import Callable, Optional, Tuple
from config import config

logger = logging.getLogger("Ultron.WakeDetector")

# Comprehensive phonetics, accents, variations, and wake phrases for Ultron
RAW_WAKE_VARIANTS = [
    "wake up ultron",
    "wake up altron",
    "wake up all tron",
    "wake up alltron",
    "wake up ultrone",
    "wake up ultra",
    "wake up",
    "hey ultron",
    "hey altron",
    "hey all tron",
    "hey ultra",
    "hi ultron",
    "hi altron",
    "yo ultron",
    "yo altron",
    "hello ultron",
    "ok ultron",
    "ultron",
    "ultrone",
    "altron",
    "eltron",
    "ultra",
    "all tron",
    "alltron",
    "oltron",
    "altrom",
    "out run",
    "haul tron",
    "wake"
]

# Sort by length descending so multi-word variants match before single words
WAKE_VARIANTS = sorted(RAW_WAKE_VARIANTS, key=len, reverse=True)

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
            self._recognizer.pause_threshold = 1.0  # Standby pause threshold
            self._recognizer.non_speaking_duration = 0.5
            logger.info(f"Ultron Microphone calibrated (threshold={self._recognizer.energy_threshold:.1f}, standby_pause=1.0s)")
        except Exception as e:
            logger.warning(f"Voice input initialization notice: {e}")

    def _play_tone_async(self, tones):
        """Plays sound cues asynchronously without blocking the listening loop."""
        def worker():
            try:
                import winsound
                for freq, dur in tones:
                    winsound.Beep(freq, dur)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _play_wake_chime(self):
        """Plays a high-tech chime when the call starts."""
        self._play_tone_async([(1200, 90), (1600, 110)])

    def _play_listen_chirp(self):
        """Plays a subtle chirp indicating Ultron is listening on the active call."""
        self._play_tone_async([(950, 60)])

    def _play_disconnect_chime(self):
        """Plays a descending tone when the call session ends."""
        self._play_tone_async([(1400, 90), (800, 130)])

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

    def is_shutdown_phrase(self, text: str) -> bool:
        """Checks if the user wants to completely terminate Ultron."""
        cleaned = text.lower().strip()
        shutdown_phrases = [
            "shut down completely", "shutdown completely", "close ultron completely",
            "shutdown ultron", "shut down ultron", "turn off ultron", "power off ultron",
            "exit ultron", "quit ultron", "stop ultron", "kill ultron",
            "shutdown", "shut down", "power off", "turn off"
        ]
        return any(k in cleaned for k in shutdown_phrases)

    def _transcribe_audio(self, audio_data) -> Optional[str]:
        """Dual-engine STT: Groq Whisper Large v3 Turbo (ultra-low latency) with Google STT fallback."""
        # Domain-specific prompt conditioning Whisper for technical and agency vocabulary
        whisper_context = (
            "Ultron, Risala Digital Marketing, Hostinger, WordPress, WP Admin, Yoast, RankMath, "
            "Dubai, UAE, Headless CMS, Next.js, SEO, focus keyword, meta title, meta description, "
            "About Us, Boss, Chrome, Spotify, Proton VPN, Profile 1, Default profile, volume, tab"
        )

        # 1. Primary: Groq Whisper (whisper-large-v3-turbo)
        if config.GROQ_API_KEY:
            try:
                import io
                from groq import Groq
                if not hasattr(self, "_groq_client") or self._groq_client is None:
                    self._groq_client = Groq(api_key=config.GROQ_API_KEY)
                wav_bytes = audio_data.get_wav_data()
                bio = io.BytesIO(wav_bytes)
                transcription = self._groq_client.audio.transcriptions.create(
                    file=("voice.wav", bio),
                    model="whisper-large-v3-turbo",
                    prompt=whisper_context,
                    temperature=0.0
                )
                if transcription and transcription.text:
                    result = transcription.text.strip()
                    if result:
                        return result
            except Exception as e:
                logger.debug(f"Groq Whisper note, attempting Google fallback: {e}")

        # 2. Fallback: Google Speech Recognition
        try:
            return self._recognizer.recognize_google(audio_data, language="en-US").strip()
        except Exception:
            return None

    def listen_single_phrase(self, timeout: int = 5, phrase_time_limit: int = 8, pause_threshold: Optional[float] = None) -> Optional[str]:
        """Listens for speech with dynamic pause threshold to prevent cutting off mid-thought."""
        if not self._recognizer or not self._microphone:
            self._init_audio()
            if not self._recognizer or not self._microphone:
                return None

        import speech_recognition as sr
        # Apply custom pause threshold if specified (e.g. 2.0s for long-form dictation)
        old_pause = self._recognizer.pause_threshold
        if pause_threshold is not None:
            self._recognizer.pause_threshold = pause_threshold

        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return self._transcribe_audio(audio)
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            logger.debug(f"Audio recognition note: {e}")
            return None
        finally:
            if pause_threshold is not None:
                self._recognizer.pause_threshold = old_pause

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
                        phrase = self.listen_single_phrase(timeout=4, phrase_time_limit=18)
                        if phrase:
                            is_wake, attached_cmd = self.is_wake_phrase(phrase)
                            if is_wake:
                                self._play_wake_chime()
                                self.is_session_active = True
                                self.silence_turns = 0
                                try:
                                    from tools.hud_overlay import hud_overlay
                                    hud_overlay.trigger_wake()
                                except Exception:
                                    pass

                                if status_logger:
                                    status_logger("⚡ [CALL CONNECTED] Live session active. Ultron will stay connected until you say 'That's enough'.")

                                if attached_cmd:
                                    # User spoke command in same sentence: "Hey Ultron open Chrome"
                                    on_command_callback(attached_cmd)
                                else:
                                    # User just woke Ultron -> sub-40ms instant greeting
                                    audio_engine.play_instant_greeting()

                    # ==========================================
                    # STATE B: ON LIVE CALL (Continuous Session)
                    # ==========================================
                    else:
                        if status_logger:
                            status_logger("● [ON CALL] Listening for your command, Boss... (Say 'That's enough' to hang up)")

                        self._play_listen_chirp()
                        # Long-form conversational listening: 2.2s pause threshold allows natural thinking pauses without cutoff
                        phrase = self.listen_single_phrase(timeout=10, phrase_time_limit=65, pause_threshold=2.2)

                        # Intelligent continuation check: If user paused on a conjunction or mid-sentence
                        if phrase:
                            cleaned_tail = phrase.rstrip(".?! ").lower().split()
                            if cleaned_tail and cleaned_tail[-1] in ("and", "then", "so", "also", "after", "like", "with", "because", "or", "plus"):
                                if status_logger:
                                    status_logger(f"🎙️ Listening for continuation... ('{phrase}'...)")
                                continuation = self.listen_single_phrase(timeout=3, phrase_time_limit=35, pause_threshold=2.0)
                                if continuation:
                                    phrase = f"{phrase.rstrip('. ')} {continuation}"

                        if phrase:
                            self.silence_turns = 0
                            # Check if user wants to completely terminate Ultron
                            if self.is_shutdown_phrase(phrase):
                                if status_logger:
                                    status_logger(f"🛑 Complete shutdown requested by Boss: '{phrase}'")
                                on_command_callback("shutdown completely")
                                break

                            # Check if user wants to end the call (return to standby)
                            elif self.is_dismissal_phrase(phrase):
                                if status_logger:
                                    status_logger(f"📞 Call ended by Boss: '{phrase}'")
                                try:
                                    from tools.hud_overlay import hud_overlay
                                    hud_overlay.set_state("IDLE")
                                except Exception:
                                    pass
                                audio_engine.speak("Understood, Boss. Ultron standing by whenever you summon me.")
                                self.is_session_active = False
                                self._play_disconnect_chime()
                            else:
                                if status_logger:
                                    status_logger(f"🎙️ Command: '{phrase}'")
                                on_command_callback(phrase)
                        else:
                            # User remained silent during this window
                            self.silence_turns += 1
                            if self.silence_turns >= 4:
                                # ~32 seconds of complete silence -> graceful standby
                                if status_logger:
                                    status_logger("📞 Call closed due to inactivity. Returning to standby.")
                                try:
                                    from tools.hud_overlay import hud_overlay
                                    hud_overlay.set_state("IDLE")
                                except Exception:
                                    pass
                                audio_engine.speak("Returning to background standby, Boss.")
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
