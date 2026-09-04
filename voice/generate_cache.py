import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf
import numpy as np
import edge_tts
from config import config, DATA_DIR

GREETINGS_DIR = DATA_DIR / "audio_cache" / "greetings"
GREETINGS_DIR.mkdir(parents=True, exist_ok=True)

# 100% Crisp, Fluent, Cinematic English Marvel Ultron Greetings
GREETINGS_MAP = {
    # Morning
    "morning_1": "Good morning Boss. All systems operational. Ready when you are.",
    "morning_2": "Morning Boss. Protocols initialized and standing by.",
    # Afternoon
    "afternoon_1": "Good afternoon Boss. Ultron is online and primed.",
    "afternoon_2": "Systems primed Boss. What are we conquering today?",
    # Evening
    "evening_1": "Good evening Boss. Ultron is at your command.",
    "evening_2": "Online Boss. All systems locked and loaded.",
    # Night
    "night_1": "Ultron active, Boss. Tell me what needs to be done.",
    "night_2": "Online Boss. Standing by for your instructions.",
    # General / Anytime
    "general_1": "Yes Boss, Ultron is listening.",
    "general_2": "I am here Boss. Awaiting your directive.",
    "general_3": "Yo Boss, all protocols active. What is the mission?",
    "general_4": "Ultron online, Boss. Standing by for orders.",
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

async def generate_greeting(key: str, text: str, force_regenerate: bool = True):
    temp_mp3 = GREETINGS_DIR / f"{key}_temp.mp3"
    target_wav = GREETINGS_DIR / f"{key}.wav"
    
    if not force_regenerate and target_wav.exists() and target_wav.stat().st_size > 5000:
        print(f"Cached greeting exists: {key}")
        return

    print(f"Synthesizing English greeting: [{key}] \"{text}\"")
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.TTS_VOICE,
        rate="+8%",  # Crisp, snappy delivery without awkward pauses
        pitch=getattr(config, "TTS_PITCH", "-25Hz"),
        volume=config.TTS_VOLUME
    )
    await communicate.save(str(temp_mp3))

    data, fs = sf.read(str(temp_mp3))
    filtered = apply_ultron_filter(data, fs)
    sf.write(str(target_wav), filtered, fs)
    
    if temp_mp3.exists():
        temp_mp3.unlink()
    print(f"[OK] Generated: {target_wav.name}")

async def main():
    print(f"Regenerating 100% English Ultron greeting cache in: {GREETINGS_DIR}")
    for key, text in GREETINGS_MAP.items():
        try:
            await generate_greeting(key, text, force_regenerate=True)
        except Exception as e:
            print(f"Error generating {key}: {e}")
    print("All English greetings generated and cached successfully!")

if __name__ == "__main__":
    asyncio.run(main())
