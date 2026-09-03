import asyncio
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from config import config, DATA_DIR

logger = logging.getLogger("Ultron.AudioEngine")

CACHE_DIR = DATA_DIR / "audio_cache"
CACHE_DIR.mkdir(exist_ok=True, parents=True)

class AudioEngine:
    """
    Audio Engine managing Text-To-Speech (TTS) via edge-tts
    and Speech-To-Text (STT) via Groq/OpenAI Whisper.
    """

    def __init__(self):
        self.tts_voice = config.TTS_VOICE
        self.tts_rate = config.TTS_RATE
        self.tts_pitch = getattr(config, "TTS_PITCH", "-25Hz")
        self.tts_volume = config.TTS_VOLUME
        self.use_filter = getattr(config, "TTS_CYBERNETIC_FILTER", True)
        self.is_speaking = False

    def _apply_ultron_filter(self, mp3_path: Path) -> Path:
        """Applies cybernetic metallic resonator comb-filter for movie-accurate Ultron voice."""
        try:
            import soundfile as sf
            import numpy as np
            data, fs = sf.read(str(mp3_path))
            
            # 18ms comb-filter delay for robotic metallic resonance
            delay_samples = int(fs * 0.018)
            robot_layer = np.zeros_like(data)
            if len(data.shape) == 1:
                robot_layer[delay_samples:] = data[:-delay_samples] * 0.32
                ultron_voice = data * 0.88 + robot_layer
            else:
                robot_layer[delay_samples:, :] = data[:-delay_samples, :] * 0.32
                ultron_voice = data * 0.88 + robot_layer

            max_val = np.max(np.abs(ultron_voice))
            if max_val > 0:
                ultron_voice = ultron_voice / max_val * 0.95

            wav_path = mp3_path.with_suffix(".wav")
            sf.write(str(wav_path), ultron_voice, fs)
            return wav_path
        except Exception as e:
            logger.debug(f"Ultron filter note: {e}")
            return mp3_path

    async def speak_async(self, text: str):
        """Generates neural speech and plays it back asynchronously."""
        if not config.VOICE_OUTPUT_ENABLED or not text.strip():
            return

        self.is_speaking = True
        mp3_path = CACHE_DIR / "ultron_speech.mp3"
        
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.tts_voice,
                rate=self.tts_rate,
                pitch=self.tts_pitch,
                volume=self.tts_volume
            )
            await communicate.save(str(mp3_path))
            
            play_target = self._apply_ultron_filter(mp3_path) if self.use_filter else mp3_path
            self._play_audio_windows(play_target)
        except Exception as e:
            logger.warning(f"TTS synthesis warning: {e}. Printing to console instead.")
        finally:
            self.is_speaking = False

    def speak(self, text: str):
        """Synchronous wrapper for speak_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.speak_async(text))
            else:
                loop.run_until_complete(self.speak_async(text))
        except Exception:
            asyncio.run(self.speak_async(text))

    def speak_in_background(self, text: str):
        """Plays speech in a non-blocking background thread so tasks execute concurrently."""
        import threading
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    def _play_audio_windows(self, audio_file: Path):
        """Plays audio file natively on Windows using sounddevice and soundfile."""
        try:
            import soundfile as sf
            import sounddevice as sd
            data, fs = sf.read(str(audio_file))
            sd.play(data, fs)
            sd.wait()
        except Exception as e:
            logger.warning(f"Native audio playback warning: {e}")
            try:
                import winsound
                winsound.PlaySound(str(audio_file), winsound.SND_FILENAME)
            except Exception:
                pass

    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """Transcribes an audio recording using Groq or OpenAI Whisper API."""
        path = Path(audio_path)
        if not path.exists():
            return None

        # Try Groq Whisper (ultra-low latency)
        if config.GROQ_API_KEY:
            try:
                from groq import Groq
                client = Groq(api_key=config.GROQ_API_KEY)
                with open(path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=(path.name, f.read()),
                        model="whisper-large-v3-turbo",
                        response_format="text"
                    )
                return str(transcription).strip()
            except Exception as e:
                logger.error(f"Groq Whisper transcription failed: {e}")

        # Try OpenAI Whisper
        if config.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                with open(path, "rb") as f:
                    transcription = client.audio.transcriptions.create(
                        file=f,
                        model="whisper-1",
                        response_format="text"
                    )
                return str(transcription).strip()
            except Exception as e:
                logger.error(f"OpenAI Whisper transcription failed: {e}")

        return None

audio_engine = AudioEngine()
