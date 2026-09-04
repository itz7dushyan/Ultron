import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_audio_cache():
    print("\n--- TEST 1: 100% English Instant Audio Greeting Cache ---")
    from voice.audio_engine import audio_engine, GREETINGS_DIR
    from voice.generate_cache import GREETINGS_MAP
    
    files = list(GREETINGS_DIR.glob("*.wav"))
    assert len(files) >= 13, f"Expected at least 13 cached greetings, found {len(files)}"
    
    # Assert NO Hindi words in greetings
    hindi_keywords = ["kya", "aaj", "aadesh", "kijiye", "karna", "wale", "hai"]
    for k, text in GREETINGS_MAP.items():
        for hw in hindi_keywords:
            assert hw not in text.lower().split(), f"Found Hindi keyword '{hw}' in greeting {k}: {text}"
    print(f"[PASS] {len(files)} 100% English Ultron greetings verified in {GREETINGS_DIR}")
    
    t0 = time.perf_counter()
    greeting_key = audio_engine.play_instant_greeting()
    t_play = (time.perf_counter() - t0) * 1000
    print(f"[PASS] Instant greeting played: '{greeting_key}' in {t_play:.1f}ms")

def test_wake_variants():
    print("\n--- TEST 2: Wake Word Phonetic Variants ---")
    from voice.wake_word import wake_detector
    test_phrases = [
        ("wake up ultron", True, ""),
        ("wake up ultron open spotify", True, "open spotify"),
        ("hey ultron close file explorer", True, "close file explorer"),
        ("yo ultron open proton vpn", True, "open proton vpn"),
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

def test_app_and_window_controls():
    print("\n--- TEST 3: Comprehensive App & Window Controls ---")
    from agents.thinker import thinker_agent
    from tools.app_control import app_tools

    # 1. Spotify
    plan_spotify = thinker_agent.analyze_and_plan("open spotify", {})
    assert plan_spotify["steps"][0]["action"] == "open_app"
    assert plan_spotify["steps"][0]["parameters"]["app_name"] == "spotify"
    print(f"[PASS] 'open spotify' -> {plan_spotify['steps'][0]} | Spoken: \"{plan_spotify['spoken_response']}\"")

    plan_spotify_close = thinker_agent.analyze_and_plan("spotify band kar do", {})
    assert plan_spotify_close["steps"][0]["action"] == "close_app"
    print(f"[PASS] 'spotify band kar do' -> {plan_spotify_close['steps'][0]} | Spoken: \"{plan_spotify_close['spoken_response']}\"")

    # 2. Proton VPN
    plan_proton = thinker_agent.analyze_and_plan("open Proton VPN", {})
    assert plan_proton["steps"][0]["action"] == "connect_vpn"
    print(f"[PASS] 'open Proton VPN' -> {plan_proton['steps'][0]} | Spoken: \"{plan_proton['spoken_response']}\"")

    # 3. File Explorer Close
    plan_fe_close = thinker_agent.analyze_and_plan("close file explorer", {})
    assert plan_fe_close["steps"][0]["action"] == "close_app"
    assert plan_fe_close["steps"][0]["parameters"]["app_name"] == "file explorer"
    print(f"[PASS] 'close file explorer' -> {plan_fe_close['steps'][0]} | Spoken: \"{plan_fe_close['spoken_response']}\"")

    # 4. Tab Close
    plan_tab = thinker_agent.analyze_and_plan("tab band karo", {})
    assert plan_tab["steps"][0]["action"] == "close_tab"
    print(f"[PASS] 'tab band karo' -> {plan_tab['steps'][0]} | Spoken: \"{plan_tab['spoken_response']}\"")

def test_smart_wallpaper_and_gallery():
    print("\n--- TEST 4: Smart Curated Wallpaper Selection & Visual Gallery ---")
    from tools.wallpaper_control import wallpaper_control
    from tools.wallpaper_viewer import wallpaper_viewer
    
    # 1. Interactive request with visual gallery
    res = wallpaper_control.change_wallpaper(theme="nature")
    assert res.get("interactive") is True, "Expected interactive mode"
    assert len(res.get("options", [])) == 5, f"Expected 5 options, got {len(res.get('options', []))}"
    assert "Boss, I have displayed" in res.get("spoken_response", ""), f"Expected English spoken response: {res.get('spoken_response')}"
    print(f"[PASS] Visual Gallery triggered, English spoken response: \"{res.get('spoken_response')}\"")
    time.sleep(1)
    wallpaper_viewer.close()

    # 2. Match follow-up choice
    choice_sunset = wallpaper_control.resolve_selection("sunset")
    assert choice_sunset and "Sunset" in choice_sunset["name"], f"Failed to match sunset: {choice_sunset}"
    print(f"[PASS] Follow-up 'sunset' matched: '{choice_sunset['name']}'")

def test_media_organizer():
    print("\n--- TEST 5: Screenshot Capture & Numbered Organizer ---")
    from tools.media_organizer import media_organizer
    import tempfile
    
    # Create temporary folder with dummy screenshot images
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(3):
            p = Path(temp_dir) / f"random_screen_{i}.png"
            p.write_bytes(b"dummy image data")
            time.sleep(0.02)
        
        res = media_organizer.organize_screenshots(temp_dir)
        assert res["success"] is True, f"Organization failed: {res}"
        assert res["count"] == 3, f"Expected 3 files renamed, got {res['count']}"
        renamed = [f.name for f in Path(temp_dir).iterdir() if f.name.startswith("Screenshot_")]
        assert len(renamed) == 3, f"Expected 3 renamed Screenshot_ files, found {renamed}"
        print(f"[PASS] Successfully organized {res['count']} screenshots into: {renamed}")

def test_background_runners():
    print("\n--- TEST 6: Background Launcher & Stopper Scripts ---")
    vbs = Path("c:/ULTRON/start_silent.vbs")
    bat_stop = Path("c:/ULTRON/stop_ultron.bat")
    bat_stat = Path("c:/ULTRON/status_ultron.bat")
    assert vbs.exists() and vbs.stat().st_size > 50, "start_silent.vbs missing or empty"
    assert bat_stop.exists() and bat_stop.stat().st_size > 50, "stop_ultron.bat missing or empty"
    assert bat_stat.exists() and bat_stat.stat().st_size > 50, "status_ultron.bat missing or empty"
    print(f"[PASS] start_silent.vbs, stop_ultron.bat, and status_ultron.bat are ready and verified.")

if __name__ == "__main__":
    print("========================================================")
    print("       ULTRON 2.1 ADVANCED VERIFICATION SUITE")
    print("========================================================")
    try:
        test_audio_cache()
        test_wake_variants()
        test_app_and_window_controls()
        test_smart_wallpaper_and_gallery()
        test_media_organizer()
        test_background_runners()
        print("\n========================================================")
        print("   >>> ALL 6 VERIFICATION TEST SUITES PASSED! <<<")
        print("========================================================\n")
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
