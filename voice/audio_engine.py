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
        self.tts_volume = config.TTS_VOLUME
        self.is_speaking = False

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
                volume=self.tts_volume
            )
            await communicate.save(str(mp3_path))
            self._play_audio_windows(mp3_path)
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

    def _play_audio_windows(self, audio_file: Path):
        """Plays audio file on Windows using Windows Media Player COM object without extra drivers."""
        try:
            # Escape path for PowerShell
            ps_path = str(audio_file.resolve()).replace("'", "''")
            ps_command = (
                f"$wmp = New-Object -ComObject WMPlayer.OCX; "
                f"$wmp.URL = '{ps_path}'; "
                f"$wmp.controls.play(); "
                f"while ($wmp.playState -ne 1 -and $wmp.playState -ne 8) {{ Start-Sleep -Milliseconds 150 }}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_command],
                capture_output=True,
                timeout=25
            )
        except Exception as e:
            logger.debug(f"Audio playback note: {e}")

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
