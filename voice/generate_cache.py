import asyncio
import os
from pathlib import Path
import soundfile as sf
import numpy as np
import edge_tts
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config, DATA_DIR

GREETINGS_DIR = DATA_DIR / "audio_cache" / "greetings"
GREETINGS_DIR.mkdir(parents=True, exist_ok=True)

GREETINGS_MAP = {
    # Morning
    "morning_1": "Good morning Boss. Systems operational. Kya karne wale hain aaj?",
    "morning_2": "Morning Boss. All protocols active. Aadesh kijiye.",
    # Afternoon
    "afternoon_1": "Good afternoon Boss. Ultron is online and ready.",
    "afternoon_2": "Systems primed Boss. What are we conquering today?",
    # Evening
    "evening_1": "Good evening Boss. Ultron is at your command.",
    "evening_2": "Online Boss. All systems locked and loaded. Kya plan hai?",
    # Night
    "night_1": "Ultron active, Boss. Tell me what needs to be done.",
    "night_2": "Online Boss. Standing by for your instructions.",
    # General / Anytime
    "general_1": "Yes Boss, Ultron is listening.",
    "general_2": "I am here Boss. Aadesh kijiye.",
    "general_3": "Yo Boss, all systems ready. Kya task hai?",
    "general_4": "Ultron online, Boss. Awaiting your command.",
    "general_5": "Standing by, Boss. How can I assist you?"
}

def apply_ultron_filter(data, fs):
    """Applies cybernetic metallic resonator comb-filter for movie-accurate Ultron voice."""
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
    return ultron_voice

async def generate_greeting(key: str, text: str):
    temp_mp3 = GREETINGS_DIR / f"{key}_temp.mp3"
    target_wav = GREETINGS_DIR / f"{key}.wav"
    
    if target_wav.exists() and target_wav.stat().st_size > 5000:
        print(f"Cached greeting already exists: {key}")
        return

    print(f"Synthesizing greeting: [{key}] \"{text}\"")
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.TTS_VOICE,
        rate=config.TTS_RATE,
        pitch=getattr(config, "TTS_PITCH", "-25Hz"),
        volume=config.TTS_VOLUME
    )
    await communicate.save(str(temp_mp3))

    data, fs = sf.read(str(temp_mp3))
    filtered = apply_ultron_filter(data, fs)
    sf.write(str(target_wav), filtered, fs)
    
    if temp_mp3.exists():
        temp_mp3.unlink()
    print(f"[OK] Created instant greeting: {target_wav.name}")

async def main():
    print(f"Generating instant Ultron greeting cache in: {GREETINGS_DIR}")
    for key, text in GREETINGS_MAP.items():
        try:
            await generate_greeting(key, text)
        except Exception as e:
            print(f"Error generating {key}: {e}")
    print("All greetings cached successfully!")

if __name__ == "__main__":
    asyncio.run(main())
