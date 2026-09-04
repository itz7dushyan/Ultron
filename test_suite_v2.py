import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_audio_cache():
    print("\n--- TEST 1: Instant Audio Greeting Cache ---")
    from voice.audio_engine import audio_engine, GREETINGS_DIR
    files = list(GREETINGS_DIR.glob("*.wav"))
    assert len(files) >= 10, f"Expected at least 10 cached greetings, found {len(files)}"
    print(f"[PASS] {len(files)} cached Ultron greetings ready in {GREETINGS_DIR}")
    
    t0 = time.perf_counter()
    greeting_key = audio_engine.play_instant_greeting()
    t_play = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Instant greeting played: '{greeting_key}' in {t_play:.1f}ms")

def test_wake_variants():
    print("\n--- TEST 2: Wake Word Phonetic Variants ---")
    from voice.wake_word import wake_detector, WAKE_VARIANTS
    test_phrases = [
        ("wake up ultron", True, ""),
        ("wake up ultron open chrome", True, "open chrome"),
        ("hey ultron make a document", True, "make a document"),
        ("yo ultron change wallpaper", True, "change wallpaper"),
        ("wake up", True, ""),
        ("ultron", True, ""),
        ("altron", True, ""),
        ("hello how are you", False, "")
    ]
    for text, exp_wake, exp_cmd in test_phrases:
        is_wake, cmd = wake_detector.is_wake_phrase(text)
        assert is_wake == exp_wake, f"Failed wake match for '{text}': got {is_wake}, expected {exp_wake}"
        if exp_cmd:
            assert exp_cmd in cmd, f"Expected cmd '{exp_cmd}' in '{cmd}'"
        print(f"[PASS] Phrase: '{text}' -> Wake: {is_wake}, Cmd: '{cmd}'")

def test_boss_persona():
    print("\n--- TEST 3: Persona & 'Boss' Addressing ---")
    from agents.thinker import thinker_agent
    res = thinker_agent.analyze_and_plan("wake up", {})
    spoken = res.get("spoken_response", "")
    assert "Boss" in spoken, f"Expected 'Boss' in greeting: {spoken}"
    assert "Sir" not in spoken, f"Did not expect 'Sir' in greeting: {spoken}"
    print(f"[PASS] Greeting spoken response: \"{spoken}\"")

def test_smart_wallpaper():
    print("\n--- TEST 4: Smart Curated Wallpaper Selection ---")
    from tools.wallpaper_control import wallpaper_control
    
    # 1. Interactive request
    res = wallpaper_control.change_wallpaper(theme="nature")
    assert res.get("interactive") is True, "Expected interactive mode"
    assert len(res.get("options", [])) == 5, f"Expected 5 options, got {len(res.get('options', []))}"
    print(f"[PASS] Interactive 5-option curation generated: {res.get('spoken_response')[:85]}...")
    
    # 2. Match follow-up choice
    choice_sunset = wallpaper_control.resolve_selection("sunset")
    assert choice_sunset and "Sunset" in choice_sunset["name"], f"Failed to match sunset: {choice_sunset}"
    print(f"[PASS] Follow-up 'sunset' matched: '{choice_sunset['name']}'")
    
    choice_mtn = wallpaper_control.resolve_selection("1")
    assert choice_mtn and "Mountain" in choice_mtn["name"], f"Failed to match 1: {choice_mtn}"
    print(f"[PASS] Follow-up '1' matched: '{choice_mtn['name']}'")

def test_hud_overlay():
    print("\n--- TEST 5: Orange Aurora & Pulsing Core HUD Overlay ---")
    from tools.hud_overlay import hud_overlay
    hud_overlay.start()
    hud_overlay.trigger_wake()
    time.sleep(0.5)
    hud_overlay.trigger_speaking(True)
    time.sleep(0.5)
    hud_overlay.trigger_speaking(False)
    time.sleep(0.2)
    hud_overlay.stop()
    print("[PASS] HUD Overlay initialized, cycled through WAKE -> SPEAKING -> IDLE states cleanly.")

def test_background_runners():
    print("\n--- TEST 6: Background Launcher Scripts ---")
    vbs = Path("c:/ULTRON/start_silent.vbs")
    bat_stop = Path("c:/ULTRON/stop_ultron.bat")
    bat_stat = Path("c:/ULTRON/status_ultron.bat")
    assert vbs.exists() and vbs.stat().st_size > 50, "start_silent.vbs missing or empty"
    assert bat_stop.exists() and bat_stop.stat().st_size > 50, "stop_ultron.bat missing or empty"
    assert bat_stat.exists() and bat_stat.stat().st_size > 50, "status_ultron.bat missing or empty"
    print(f"[PASS] start_silent.vbs, stop_ultron.bat, and status_ultron.bat are ready.")

if __name__ == "__main__":
    print("========================================================")
    print("       ULTRON 2.0 ADVANCED VERIFICATION SUITE")
    print("========================================================")
    try:
        test_audio_cache()
        test_wake_variants()
        test_boss_persona()
        test_smart_wallpaper()
        test_hud_overlay()
        test_background_runners()
        print("\n========================================================")
        print("   >>> ALL 6 VERIFICATION TEST SUITES PASSED! <<<")
        print("========================================================\n")
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
