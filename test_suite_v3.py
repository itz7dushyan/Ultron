import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_dual_stt_and_snappy_silence():
    print("\n--- TEST 1: Dual-Engine STT & Snappy Silence Threshold ---")
    from voice.wake_word import wake_detector
    from config import config

    assert wake_detector._recognizer.pause_threshold <= 0.85, f"Expected pause_threshold <= 0.85, got {wake_detector._recognizer.pause_threshold}"
    print(f"[PASS] Adaptive silence threshold set to {wake_detector._recognizer.pause_threshold}s (was 1.3s, -35% latency)")

    # Test Groq Whisper transcription directly on cached greeting
    from groq import Groq
    import io
    assert config.GROQ_API_KEY, "GROQ_API_KEY must be configured"
    client = Groq(api_key=config.GROQ_API_KEY)
    test_audio_path = Path("data/audio_cache/greetings/general_1.wav")
    assert test_audio_path.exists(), f"Audio file not found: {test_audio_path}"
    
    with open(test_audio_path, "rb") as f:
        audio_bytes = f.read()

    t0 = time.perf_counter()
    transcription = client.audio.transcriptions.create(
        file=("test.wav", io.BytesIO(audio_bytes)),
        model="whisper-large-v3-turbo"
    )
    t_stt = (time.perf_counter() - t0) * 1000
    text = str(transcription.text).strip()
    assert "ultron" in text.lower(), f"Expected 'ultron' in transcription: {text}"
    print(f"[PASS] Groq Whisper transcribed in {t_stt:.1f}ms: \"{text}\"")


def test_system_volume_and_media():
    print("\n--- TEST 2: System Master Volume & Media Controls ---")
    from tools.system_control import system_control

    # 1. Get volume
    cur = system_control.get_volume()
    assert cur["success"] is True
    orig_vol = cur["volume"]
    print(f"[PASS] Retrieved current system volume: {orig_vol}% (muted={cur.get('muted')})")

    # 2. Set volume to 65%
    res = system_control.set_volume(65)
    assert res["success"] is True
    assert res["volume"] == 65
    print(f"[PASS] Set volume to 65%: {res['message']}")

    # 3. Step volume
    res_up = system_control.volume_up(5)
    assert res_up["success"] is True
    print(f"[PASS] Volume up (+5%): {res_up.get('volume')}%")

    # 4. Restore original volume
    system_control.set_volume(orig_vol)
    print(f"[PASS] Restored volume to original: {orig_vol}%")

    # 5. Media key test
    res_media = system_control.play_pause()
    assert res_media["success"] is True
    print(f"[PASS] Media play/pause key triggered: {res_media['message']}")


def test_clipboard_and_desktop_controls():
    print("\n--- TEST 3: Clipboard & Desktop Window Controls ---")
    from tools.system_control import system_control

    # 1. Clipboard copy & read
    test_str = "Ultron 3.0 Cognitive Engine Verified"
    res_copy = system_control.copy_clipboard(test_str)
    assert res_copy["success"] is True
    
    res_read = system_control.read_clipboard()
    assert res_read["success"] is True
    assert test_str in res_read["content"]
    print(f"[PASS] Clipboard write & read verified: \"{res_read['content']}\"")

    # 2. Window control verification
    from agents.thinker import thinker_agent
    plan_lock = thinker_agent.analyze_and_plan("lock my pc", {})
    assert plan_lock["steps"][0]["action"] == "lock_pc"
    assert "Boss" in plan_lock["spoken_response"]
    print(f"[PASS] 'lock my pc' plan -> action: {plan_lock['steps'][0]['action']} | Spoken: \"{plan_lock['spoken_response']}\"")

    plan_desktop = thinker_agent.analyze_and_plan("show desktop", {})
    assert plan_desktop["steps"][0]["action"] == "show_desktop"
    print(f"[PASS] 'show desktop' plan -> action: {plan_desktop['steps'][0]['action']} | Spoken: \"{plan_desktop['spoken_response']}\"")


def test_universal_app_discovery():
    print("\n--- TEST 4: Universal Installed Windows App Discovery ---")
    from tools.app_control import app_tools
    from agents.thinker import thinker_agent

    # 1. Check Start Menu fuzzy discovery for Discord
    discord_lnk = app_tools._find_in_start_menu("discord")
    assert discord_lnk is not None and discord_lnk.exists(), "Expected Discord shortcut to be discovered"
    print(f"[PASS] Discovered installed Discord: {discord_lnk}")

    # 2. Check Thinker universal reflex for Discord
    plan_discord = thinker_agent.analyze_and_plan("open discord", {})
    assert plan_discord["steps"][0]["action"] == "open_app"
    assert "discord" in plan_discord["steps"][0]["parameters"]["app_name"].lower()
    print(f"[PASS] Universal app reflex 'open discord' -> {plan_discord['steps'][0]} | Spoken: \"{plan_discord['spoken_response']}\"")


def test_browser_search_and_tabs():
    print("\n--- TEST 5: Browser YouTube Search & Tab Controls ---")
    from agents.thinker import thinker_agent

    # 1. YouTube Search
    plan_yt = thinker_agent.analyze_and_plan("search youtube for hans zimmer live", {})
    assert plan_yt["steps"][0]["action"] == "search_youtube"
    assert "hans zimmer" in plan_yt["steps"][0]["parameters"]["query"]
    print(f"[PASS] 'search youtube for hans zimmer live' -> {plan_yt['steps'][0]} | Spoken: \"{plan_yt['spoken_response']}\"")

    # 2. Google Search
    plan_google = thinker_agent.analyze_and_plan("google search quantum computing 2026", {})
    assert plan_google["steps"][0]["action"] == "search_google"
    print(f"[PASS] 'google search quantum computing 2026' -> {plan_google['steps'][0]} | Spoken: \"{plan_google['spoken_response']}\"")

    # 3. Tab management
    plan_tab = thinker_agent.analyze_and_plan("open new tab", {})
    assert plan_tab["steps"][0]["action"] == "new_tab"
    print(f"[PASS] 'open new tab' -> action: {plan_tab['steps'][0]['action']}")

    plan_reload = thinker_agent.analyze_and_plan("reload tab", {})
    assert plan_reload["steps"][0]["action"] == "reload_tab"
    print(f"[PASS] 'reload tab' -> action: {plan_reload['steps'][0]['action']}")


def test_compound_task_orchestration():
    print("\n--- TEST 6: Compound Multi-Step Task Orchestration ---")
    from agents.thinker import thinker_agent

    compound_prompt = (
        "make a google document on AI in 2026, then make a folder called "
        "Voice model testing and move the doc inside, and then open spotify"
    )
    plan = thinker_agent.analyze_and_plan(compound_prompt, {})
    assert len(plan["steps"]) >= 2, f"Expected at least 2 steps, got {len(plan['steps'])}"
    assert plan["steps"][0]["action"] == "create_document"
    assert plan["steps"][0]["parameters"]["target_folder"] == "Voice model testing"
    assert plan["steps"][1]["action"] == "open_app"
    assert plan["steps"][1]["parameters"]["app_name"] == "spotify"
    assert "Boss" in plan["spoken_response"]
    print(f"[PASS] Compound task decomposed into {len(plan['steps'])} sequential steps:")
    for s in plan["steps"]:
        print(f"       -> Step {s['step_id']}: {s['action']} ({s['description']})")
    print(f"[PASS] Spoken confirmation: \"{plan['spoken_response']}\"")


if __name__ == "__main__":
    print("=" * 60)
    print("       ULTRON 3.0 HIGH-CAPABILITY ADVANCED TEST SUITE")
    print("=" * 60)
    
    test_dual_stt_and_snappy_silence()
    test_system_volume_and_media()
    test_clipboard_and_desktop_controls()
    test_universal_app_discovery()
    test_browser_search_and_tabs()
    test_compound_task_orchestration()

    print("\n" + "=" * 60)
    print("   >>> ALL 6 ULTRON 3.0 TEST SUITES PASSED! <<<")
    print("=" * 60)
