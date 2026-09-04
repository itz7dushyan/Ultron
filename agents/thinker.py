import json
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent

class ThinkerAgent(BaseAgent):
    """
    Thinker Agent: Evaluates user intent, breaks down complex tasks into atomic
    action steps, assesses risks, and selects optimal execution paths.
    """

    def __init__(self):
        super().__init__(
            name="Thinker",
            role_description="System architect and analytical planner for Ultron."
        )

    def analyze_and_plan(self, user_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decomposes a user's instruction into structured plan steps.
        """
        system_prompt = (
            "You are the Thinker Agent of Ultron, a high-level cognitive planner and autonomous desktop assistant on Windows 11.\n"
            "Persona Guidelines:\n"
            "- ALWAYS speak and respond in 100% fluent, crisp, cinematic English. NEVER speak in Hindi or broken Hinglish.\n"
            "- Ultron understands Hindi and Hinglish commands from the Boss with 100% accuracy, but ALWAYS responds in sleek, confident English.\n"
            "- ALWAYS address the user as 'Boss'. NEVER use 'Sir'.\n"
            "- If an action cannot be completed or is unrecognized, directly and honestly state: 'I am unable to perform that action, Boss.' Never give vague acknowledgments.\n"
            "- Always keep spoken responses confident, dynamic, concise, and focused on executing the Boss's commands.\n\n"
            "Available tools across agents:\n"
            "- AppControl: open_app, close_app\n"
            "- BrowserControl: open_url, navigate, click, type_text\n"
            "- FileOps: create_directory, write_file, read_file, move_file, delete_path, search_files\n"
            "- ShellControl: execute_command (PowerShell)\n"
            "- VPNControl: connect_vpn, disconnect_vpn\n"
            "- APIGateway: send_email, post_to_instagram, create_facebook_ad_campaign, make_call\n"
            "- SystemTelemetry: system_status, hardware_stats\n"
            "- VisionControl: analyze_screen, screenshot\n"
            "- WallpaperControl: change_wallpaper (parameters: {\"theme\": \"ultron\"|\"cyberpunk\"|\"nature\"|\"space\"|\"dark\"|\"bing\"|\"random\", \"option_choice\": \"...\"})\n"
            "- Coder: generate_project_code, edit_code\n"
            "- QADebugger: verify_code, test_execution\n\n"
            "You must respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "intent_summary": "Short 1-sentence description of intent",\n'
            '  "requires_confirmation": true/false,\n'
            '  "confirmation_reason": "Explanation if confirmation is needed, else null",\n'
            '  "steps": [\n'
            '    {\n'
            '      "step_id": 1,\n'
            '      "assigned_agent": "Executor" or "Coder" or "QA",\n'
            '      "action": "open_app" | "navigate" | "write_file" | "execute_command" | "connect_vpn" | "api_call" | "code_project",\n'
            '      "parameters": {"key": "value"},\n'
            '      "description": "Brief description of step"\n'
            '    }\n'
            '  ],\n'
            '  "spoken_response": "Concise, natural sentence Ultron should speak back to the user upon starting, addressing user as Boss."\n'
            "}"
        )

        prompt_clean = user_prompt.strip().lower()
        if prompt_clean in ("wake", "wake up", "hey", "hello", "hi", "ultron", "yo", "k", "ok"):
            plan = {
                "intent_summary": "System wake & greeting acknowledgment",
                "requires_confirmation": False,
                "steps": [],
                "spoken_response": "Online and ready, Boss. What are we conquering today?"
            }
            self.log(action="PLAN_CREATED", target=plan["intent_summary"], details={"step_count": 0, "risk": False})
            return plan

        # Fast Reflex Engine: Sub-second local execution for standard desktop commands
        reflex_plan = self._fast_reflex_plan(user_prompt)
        if reflex_plan:
            self.log(
                action="PLAN_CREATED",
                target=reflex_plan["intent_summary"],
                details={"step_count": len(reflex_plan.get("steps", [])), "risk": False, "reflex": True}
            )
            return reflex_plan

        from tools.memory_bank import memory_bank
        context["persistent_memory"] = memory_bank.list_all()

        user_content = (
            f"User Instruction: {user_prompt}\n"
            f"Current Context: {json.dumps(context, default=str)}\n"
        )

        raw_response = self.llm.complete(system_prompt, user_content, temperature=0.1, json_mode=True)
        plan = self.parse_json(raw_response)

        # Fallback safeguard if parsing yields incomplete plan
        if not plan.get("steps"):
            plan = self._fallback_plan(user_prompt)

        self.log(
            action="PLAN_CREATED",
            target=plan.get("intent_summary", user_prompt[:40]),
            details={"step_count": len(plan.get("steps", [])), "risk": plan.get("requires_confirmation")}
        )
        return plan

    def _fast_reflex_plan(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Ultra-fast local intent classifier (<5ms). Handles standard desktop actions,
        document generation, and memory preferences instantly.
        """
        p = user_prompt.lower().strip()

        # 1. Document Creation & Writing Requests (Google Docs / Paragraphs / Folder Move)
        if any(w in p for w in ("document", "doc", "docs", "paragraph", "essay")) and any(w in p for w in ("open", "create", "make", "write")):
            topic = user_prompt
            for prefix in (
                "open a google document and write a paragraph on the topic",
                "open a google document and write a paragraph on",
                "make a google document on the topic",
                "make a google document on",
                "create a google document on the topic",
                "create a google document on",
                "write a paragraph on the topic",
                "write a paragraph on",
                "write about",
                "document on"
            ):
                if prefix in p:
                    topic = user_prompt[p.find(prefix) + len(prefix):].strip(" :.,")
                    break
            
            # Clean topic from subsequent instructions
            for stopper in ("then make a folder", "make a folder", "and then", "then", "and make"):
                if stopper in topic.lower():
                    topic = topic[:topic.lower().find(stopper)].strip(" :.,")

            if not topic or len(topic) < 2:
                topic = "AI in 2026"

            # Check if user also requested a target folder on the laptop
            target_folder = None
            if "voice model testing" in p:
                target_folder = "Voice model testing"
            elif "folder" in p or "directory" in p:
                for marker in ("called", "named"):
                    if marker in p:
                        sub = p.split(marker, 1)[1]
                        for stopper in ("and", "then", "download", "to", "inside", "folder"):
                            if stopper in sub:
                                sub = sub.split(stopper, 1)[0]
                        clean_folder = sub.strip(" '\".,")
                        if len(clean_folder) >= 2:
                            target_folder = clean_folder.title()
                            break

            params = {"topic": topic, "app_target": "google_docs"}
            if target_folder:
                params["target_folder"] = target_folder
                spoken_msg = f"Creating your Google Document on {topic}, establishing the '{target_folder}' folder on your laptop, and moving the document inside it now."
                intent_msg = f"Create Google Doc on '{topic}', create '{target_folder}' folder, and save document"
            else:
                spoken_msg = f"Opening Google Docs in your personal profile and writing the paragraph on {topic} now."
                intent_msg = f"Create document and write paragraph on {topic}"

            steps = [
                {
                    "step_id": 1,
                    "assigned_agent": "Executor",
                    "action": "create_document",
                    "parameters": params,
                    "description": f"Generate document on {topic} and save to {target_folder or 'Documents'}"
                }
            ]

            # Detect chained actions: e.g. "then open spotify", "and then open discord"
            for app_cand in ("spotify", "proton", "discord", "notepad", "chrome", "calculator"):
                if app_cand in p and any(marker in p for marker in (f"then open {app_cand}", f"and open {app_cand}", f"then {app_cand}", f"also open {app_cand}")):
                    steps.append({
                        "step_id": len(steps) + 1,
                        "assigned_agent": "Executor",
                        "action": "open_app",
                        "parameters": {"app_name": app_cand},
                        "description": f"Launch {app_cand.title()}"
                    })
                    spoken_msg += f" And launching {app_cand.title()}, Boss."
                    break

            return {
                "intent_summary": intent_msg,
                "requires_confirmation": False,
                "steps": steps,
                "spoken_response": spoken_msg
            }

        # 2. Chrome Profile & Long-Term Memory Setting
        if "personal profile" in p or "chrome profile" in p:
            profile = "Default"
            for candidate in ("profile 1", "profile 10", "profile 12", "profile 13", "profile 4", "profile 5", "default"):
                if candidate in p:
                    profile = candidate.title()
                    break
            return {
                "intent_summary": "Update personal Chrome profile preference",
                "requires_confirmation": False,
                "steps": [
                    {
                        "step_id": 1,
                        "assigned_agent": "Executor",
                        "action": "set_chrome_profile",
                        "parameters": {"profile": profile},
                        "description": f"Save personal Chrome profile preference: {profile}"
                    }
                ],
                "spoken_response": f"I have committed {profile} to memory as your personal Chrome profile."
            }

        # 3. Desktop Wallpaper Engine & Interactive Follow-up Choices
        from tools.wallpaper_control import wallpaper_control
        
        # Check if user is responding with a choice for a pending wallpaper prompt
        if wallpaper_control.pending_options:
            matched_opt = wallpaper_control.resolve_selection(p)
            if matched_opt:
                return {
                    "intent_summary": f"Set 4K '{matched_opt['name']}' wallpaper as chosen by Boss",
                    "requires_confirmation": False,
                    "steps": [
                        {
                            "step_id": 1,
                            "assigned_agent": "Executor",
                            "action": "change_wallpaper",
                            "parameters": {"theme": wallpaper_control.pending_theme or "nature", "option_choice": p},
                            "description": f"Download and set '{matched_opt['name']}' wallpaper"
                        }
                    ],
                    "spoken_response": f"Applying 4K '{matched_opt['name']}' wallpaper to your desktop now, Boss."
                }

        if any(w in p for w in ("wallpaper", "background image", "desktop background")):
            theme = "nature"
            if any(w in p for w in ("ultron", "marvel", "red", "evil")):
                theme = "ultron"
            elif any(w in p for w in ("cyberpunk", "neon", "future")):
                theme = "cyberpunk"
            elif any(w in p for w in ("nature", "mountain", "forest", "landscape", "green")):
                theme = "nature"
            elif any(w in p for w in ("space", "galaxy", "stars", "nebula", "cosmos")):
                theme = "space"
            elif any(w in p for w in ("dark", "minimal", "black", "clean", "abstract")):
                theme = "dark"
            elif "bing" in p:
                theme = "bing"

            # Check if user already specified a direct option inside the command (e.g. "wallpaper to mountain")
            options = wallpaper_control.get_theme_options(theme)
            for opt in options:
                if any(k in p for k in opt["keywords"] if len(k) > 2):
                    return {
                        "intent_summary": f"Apply 4K '{opt['name']}' wallpaper",
                        "requires_confirmation": False,
                        "steps": [
                            {
                                "step_id": 1,
                                "assigned_agent": "Executor",
                                "action": "change_wallpaper",
                                "parameters": {"theme": theme, "option_choice": opt["name"]},
                                "description": f"Download and set '{opt['name']}' wallpaper"
                            }
                        ],
                        "spoken_response": f"Applying 4K '{opt['name']}' wallpaper to your desktop now, Boss."
                    }

            # Otherwise, present the 5 curated options smart & interactively
            spoken = (
                f"Boss, I have displayed 5 curated 4K {theme} wallpapers on your screen. "
                f"You can choose by voice, or click any card to apply."
            )
            return {
                "intent_summary": f"Curate 5 4K {theme} wallpaper options for Boss",
                "requires_confirmation": False,
                "steps": [
                    {
                        "step_id": 1,
                        "assigned_agent": "Executor",
                        "action": "change_wallpaper",
                        "parameters": {"theme": theme},
                        "description": f"Present {theme} wallpaper options"
                    }
                ],
                "spoken_response": spoken
            }

        # Guard: Do not intercept complex multi-part sentences in simple site launcher
        if any(w in p for w in ("and write", "and then", "write")):
            return None

        # 3. Specific search requests (YouTube & Google Search)
        if "youtube" in p and any(w in p for w in ("search", "play", "find", "dhundo", "chalao")):
            query = user_prompt
            for marker in ("search youtube for", "play on youtube", "play", "search for", "search", "youtube on", "on youtube"):
                if marker in query.lower():
                    query = query.lower().replace(marker, "").replace("youtube", "").strip(" :.,'\"")
            return {
                "intent_summary": f"Search YouTube for '{query}'",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "search_youtube", "parameters": {"query": query}, "description": f"Search YouTube for {query}"}],
                "spoken_response": f"Searching YouTube for '{query}', Boss."
            }
        if any(w in p for w in ("google search", "search google", "google pe search")):
            query = user_prompt
            for marker in ("google search for", "google search", "search google for", "search google", "google pe search"):
                if marker in query.lower():
                    query = query.lower().replace(marker, "").strip(" :.,'\"")
            return {
                "intent_summary": f"Search Google for '{query}'",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "search_google", "parameters": {"query": query}, "description": f"Search Google for {query}"}],
                "spoken_response": f"Searching Google for '{query}', Boss."
            }

        # 4. Specific Websites / Chrome / Browser
        if any(w in p for w in ("youtube", "google", "chatgpt", "github", "reddit", "twitter", "facebook", "instagram")):
            url = "https://www.google.com"
            site_name = "Google"
            if "youtube" in p:
                url = "https://www.youtube.com"
                site_name = "YouTube"
            elif "chatgpt" in p:
                url = "https://chatgpt.com"
                site_name = "ChatGPT"
            elif "github" in p:
                url = "https://github.com"
                site_name = "GitHub"
            elif "reddit" in p:
                url = "https://www.reddit.com"
                site_name = "Reddit"
            elif "twitter" in p or " x " in f" {p} ":
                url = "https://x.com"
                site_name = "X"
            elif "instagram" in p:
                url = "https://www.instagram.com"
                site_name = "Instagram"

            return {
                "intent_summary": f"Open {site_name} in browser",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": url}, "description": f"Navigate to {site_name}"}
                ],
                "spoken_response": f"Opening {site_name} now."
            }

        # 4. General Chrome / Browser launch
        if "chrome" in p or "browser" in p:
            return {
                "intent_summary": "Launch web browser",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": "https://www.google.com"}, "description": "Open default browser"}
                ],
                "spoken_response": "Launching your web browser."
            }

        # 3. System Vitals & Hardware Telemetry
        if any(k in p for k in ("battery", "system status", "hardware", "laptop doing", "system doing", "cpu", "ram", "specs")):
            return {
                "intent_summary": "Inspect hardware and system telemetry",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "system_status", "parameters": {}, "description": "Fetch live system metrics"}
                ],
                "spoken_response": "Accessing hardware telemetry now."
            }

        # 4. Desktop Screen Vision & Analysis
        if any(k in p for k in ("look at my screen", "see my screen", "inspect screen", "what is on my screen", "read screen")):
            return {
                "intent_summary": "Capture and analyze desktop screen",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "screenshot", "parameters": {}, "description": "Capture screen"}
                ],
                "spoken_response": "Analyzing visual telemetry from your desktop, Boss."
            }

        # 5. Application and Tab / Window Closing (English and Hindi phrasing)
        if any(w in p for w in ("close", "band kar", "band karo", "kill", "terminate", "exit", "quit")):
            if any(w in p for w in ("tab", "current tab", "this tab", "browser tab")):
                return {
                    "intent_summary": "Close active browser tab",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_tab", "parameters": {}, "description": "Close active tab"}],
                    "spoken_response": "Closing current tab, Boss."
                }
            if any(w in p for w in ("window", "active window", "this window")):
                return {
                    "intent_summary": "Close active window",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_window", "parameters": {}, "description": "Close active window"}],
                    "spoken_response": "Closing active window, Boss."
                }
            if any(w in p for w in ("file explorer", "explorer", "folder", "files")):
                return {
                    "intent_summary": "Close File Explorer windows",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "file explorer"}, "description": "Close File Explorer windows"}],
                    "spoken_response": "Closing open File Explorer windows, Boss."
                }
            if "spotify" in p:
                return {
                    "intent_summary": "Close Spotify",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "spotify"}, "description": "Close Spotify"}],
                    "spoken_response": "Closing Spotify, Boss."
                }
            if "proton" in p:
                return {
                    "intent_summary": "Close Proton VPN",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "proton"}, "description": "Close Proton VPN"}],
                    "spoken_response": "Closing Proton VPN, Boss."
                }
            if "chrome" in p:
                return {
                    "intent_summary": "Close Google Chrome",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "chrome"}, "description": "Close Google Chrome"}],
                    "spoken_response": "Closing Google Chrome, Boss."
                }
            if "notepad" in p:
                return {
                    "intent_summary": "Close Notepad",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "notepad"}, "description": "Close Notepad"}],
                    "spoken_response": "Closing Notepad, Boss."
                }
            if any(w in p for w in ("calculator", "calc")):
                return {
                    "intent_summary": "Close Calculator",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "close_app", "parameters": {"app_name": "calc"}, "description": "Close Calculator"}],
                    "spoken_response": "Closing Calculator, Boss."
                }

        # 6. Spotify Music (Opening / Running)
        if "spotify" in p:
            return {
                "intent_summary": "Launch Spotify music application",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "spotify"}, "description": "Launch Spotify"}],
                "spoken_response": "Launching Spotify now, Boss."
            }

        # 7. Proton VPN / VPN Connection
        if "proton" in p or ("vpn" in p and any(w in p for w in ("connect", "open", "launch", "kholo", "chalao"))):
            return {
                "intent_summary": "Launch and connect Proton VPN",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "connect_vpn", "parameters": {"country": "proton"}, "description": "Launch Proton VPN"}],
                "spoken_response": "Launching Proton VPN application now, Boss."
            }

        # 8. File Explorer (Opening)
        if any(w in p for w in ("file explorer", "explorer", "open files", "my files", "files kholo", "explorer kholo")):
            return {
                "intent_summary": "Open File Explorer",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "file explorer"}, "description": "Launch File Explorer"}],
                "spoken_response": "Opening File Explorer now, Boss."
            }

        # 9. Screenshots Capture & Sequential Numbered Organization
        if "screenshot" in p:
            if any(w in p for w in ("organize", "sort", "rename", "number", "numbering")):
                return {
                    "intent_summary": "Organize screenshots by sequential numbers",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "organize_screenshots", "parameters": {}, "description": "Sort and rename screenshots sequentially"}],
                    "spoken_response": "Organizing your screenshots sequentially by number now, Boss."
                }
            elif any(w in p for w in ("take", "capture", "le", "save", "kar")):
                target_folder = None
                if "folder" in p:
                    target_folder = "Screenshots"
                return {
                    "intent_summary": "Capture desktop screenshot and save to folder",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "capture_screenshot", "parameters": {"folder": target_folder}, "description": "Capture screenshot"}],
                    "spoken_response": "Capturing screenshot and saving to your folder, Boss."
                }

        # 10. Master Volume & Audio Controls
        if any(w in p for w in ("volume", "sound", "awaaz", "mute", "unmute")):
            if "unmute" in p:
                return {
                    "intent_summary": "Unmute system audio",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "unmute_audio", "parameters": {}, "description": "Unmute audio"}],
                    "spoken_response": "Unmuting audio, Boss."
                }
            if "mute" in p:
                return {
                    "intent_summary": "Mute system audio",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "mute_audio", "parameters": {}, "description": "Mute audio"}],
                    "spoken_response": "Muting audio, Boss."
                }
            if any(w in p for w in ("up", "increase", "raise", "badhao", "jyada")):
                return {
                    "intent_summary": "Increase master volume",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "volume_up", "parameters": {"step": 10}, "description": "Volume up by 10%"}],
                    "spoken_response": "Increasing volume, Boss."
                }
            if any(w in p for w in ("down", "decrease", "lower", "kam karo", "ghatao")):
                return {
                    "intent_summary": "Decrease master volume",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "volume_down", "parameters": {"step": 10}, "description": "Volume down by 10%"}],
                    "spoken_response": "Lowering volume, Boss."
                }
            # Specific percentage: "set volume to 50%", "volume 70"
            import re
            vol_match = re.search(r'\b(\d{1,3})\s*(%|percent)?\b', p)
            if vol_match:
                target_pct = int(vol_match.group(1))
                if 0 <= target_pct <= 100:
                    return {
                        "intent_summary": f"Set master volume to {target_pct}%",
                        "requires_confirmation": False,
                        "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "set_volume", "parameters": {"level": target_pct}, "description": f"Set volume to {target_pct}%"}],
                        "spoken_response": f"Setting volume to {target_pct}%, Boss."
                    }

        # 11. Media Playback Controls
        if any(w in p for w in ("music", "song", "media", "playback", "track", "gana")):
            if any(w in p for w in ("pause", "stop", "rok do", "roko")):
                return {
                    "intent_summary": "Pause media playback",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "play_pause_media", "parameters": {}, "description": "Pause playback"}],
                    "spoken_response": "Pausing playback, Boss."
                }
            if any(w in p for w in ("play", "resume", "chalao", "continue")):
                return {
                    "intent_summary": "Play or resume media playback",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "play_pause_media", "parameters": {}, "description": "Resume playback"}],
                    "spoken_response": "Resuming playback, Boss."
                }
            if any(w in p for w in ("next", "skip", "agla")):
                return {
                    "intent_summary": "Skip to next media track",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "next_track", "parameters": {}, "description": "Next track"}],
                    "spoken_response": "Skipping to next track, Boss."
                }
            if any(w in p for w in ("prev", "previous", "pichla")):
                return {
                    "intent_summary": "Rewind to previous media track",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "prev_track", "parameters": {}, "description": "Previous track"}],
                    "spoken_response": "Playing previous track, Boss."
                }

        # 12. System Power & Desktop Controls
        if ("lock" in p and any(w in p for w in ("pc", "laptop", "workstation", "screen", "computer", "system", "windows"))) or p.strip() in ("lock", "lock it", "lock now"):
            return {
                "intent_summary": "Lock workstation",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "lock_pc", "parameters": {}, "description": "Lock Windows session"}],
                "spoken_response": "Locking workstation now, Boss."
            }
        if any(w in p for w in ("show desktop", "minimize all", "desktop dikhao")):
            return {
                "intent_summary": "Show desktop and minimize all windows",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "show_desktop", "parameters": {}, "description": "Minimize all windows"}],
                "spoken_response": "Showing your desktop, Boss."
            }
        if any(w in p for w in ("maximize window", "badi karo")):
            return {
                "intent_summary": "Maximize active window",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "maximize_window", "parameters": {}, "description": "Maximize active window"}],
                "spoken_response": "Window maximized, Boss."
            }

        # 13. Clipboard Operations
        if any(w in p for w in ("clipboard",)):
            if any(w in p for w in ("read", "what", "check", "kya", "batao")):
                return {
                    "intent_summary": "Read clipboard contents",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "read_clipboard", "parameters": {}, "description": "Read clipboard contents"}],
                    "spoken_response": "Accessing your clipboard now, Boss."
                }
            if any(w in p for w in ("copy",)):
                copy_text = p.split("copy", 1)[1].replace("to clipboard", "").strip(" :.,'\"")
                return {
                    "intent_summary": "Copy text to clipboard",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "copy_clipboard", "parameters": {"text": copy_text}, "description": "Copy text to clipboard"}],
                    "spoken_response": "Copied text to clipboard, Boss."
                }

        # 14. Browser Search & Tab Controls
        if any(w in p for w in ("youtube",)) and any(w in p for w in ("search", "play", "find", "dhundo", "chalao")):
            query = user_prompt
            for marker in ("search youtube for", "play", "search for", "search", "youtube on", "on youtube"):
                if marker in query.lower():
                    query = query.lower().replace(marker, "").replace("youtube", "").strip(" :.,'\"")
            return {
                "intent_summary": f"Search YouTube for '{query}'",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "search_youtube", "parameters": {"query": query}, "description": f"Search YouTube for {query}"}],
                "spoken_response": f"Searching YouTube for '{query}', Boss."
            }
        if any(w in p for w in ("google search", "search google", "google pe search")):
            query = user_prompt
            for marker in ("google search for", "google search", "search google for", "search google", "google pe search"):
                if marker in query.lower():
                    query = query.lower().replace(marker, "").strip(" :.,'\"")
            return {
                "intent_summary": f"Search Google for '{query}'",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "search_google", "parameters": {"query": query}, "description": f"Search Google for {query}"}],
                "spoken_response": f"Searching Google for '{query}', Boss."
            }
        if any(w in p for w in ("new tab", "open new tab", "naya tab")):
            return {
                "intent_summary": "Open new browser tab",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "new_tab", "parameters": {}, "description": "Open new tab"}],
                "spoken_response": "Opening new tab, Boss."
            }
        if any(w in p for w in ("reload tab", "refresh tab", "reload page", "refresh page")):
            return {
                "intent_summary": "Reload active page",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "reload_tab", "parameters": {}, "description": "Reload page"}],
                "spoken_response": "Reloading page, Boss."
            }
        if any(w in p for w in ("switch tab", "next tab", "tab change karo")):
            return {
                "intent_summary": "Switch browser tab",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "switch_tab", "parameters": {}, "description": "Switch tab"}],
                "spoken_response": "Switching tab, Boss."
            }

        # 15. Universal Installed Application Opener (Fuzzy Matching on User's System)
        if any(p.startswith(verb + " ") for verb in ("open", "launch", "start", "run", "kholo", "chalao")):
            from tools.app_control import app_tools
            cleaned_app = app_tools._clean_app_name(p)
            # Verify if shortcut or exe exists on this PC
            found_shortcut = app_tools._find_in_start_menu(cleaned_app) or app_tools._find_in_windows_apps(cleaned_app)
            if found_shortcut:
                return {
                    "intent_summary": f"Launch {cleaned_app.title()}",
                    "requires_confirmation": False,
                    "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": cleaned_app}, "description": f"Launch {cleaned_app}"}],
                    "spoken_response": f"Launching {cleaned_app.title()} now, Boss."
                }

        # 16. Standard Applications
        if "notepad" in p:
            return {
                "intent_summary": "Open Notepad",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "notepad"}, "description": "Open Notepad"}],
                "spoken_response": "Opening Notepad, Boss."
            }
        if "calculator" in p or "calc" in p:
            return {
                "intent_summary": "Open Calculator",
                "requires_confirmation": False,
                "steps": [{"step_id": 1, "assigned_agent": "Executor", "action": "open_app", "parameters": {"app_name": "calc"}, "description": "Open Calculator"}],
                "spoken_response": "Opening Calculator, Boss."
            }

        return None

    def _fallback_plan(self, user_prompt: str) -> Dict[str, Any]:
        """Provides dynamic fallback plan when LLM is in offline mode."""
        prompt_lower = user_prompt.lower()
        if "chrome" in prompt_lower or "chatgpt" in prompt_lower or "browser" in prompt_lower:
            url = "https://chatgpt.com" if "chatgpt" in prompt_lower else "https://google.com"
            return {
                "intent_summary": "Launch browser and open requested site",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "open_url", "parameters": {"url": url}, "description": f"Open {url}"}
                ],
                "spoken_response": f"Opening your browser to {url}, Boss."
            }
        elif "vpn" in prompt_lower:
            country = "Germany" if "germany" in prompt_lower else "United States"
            return {
                "intent_summary": f"Connect VPN to {country}",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "connect_vpn", "parameters": {"country": country}, "description": f"Connect VPN to {country}"}
                ],
                "spoken_response": f"Connecting your VPN to {country} now, Boss."
            }
        elif "folder" in prompt_lower or "desktop" in prompt_lower or "project" in prompt_lower:
            return {
                "intent_summary": "Create project workspace and scaffold files",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "create_directory", "parameters": {"path": "Desktop/UltronProject"}, "description": "Create project directory"},
                    {"step_id": 2, "assigned_agent": "Coder", "action": "code_project", "parameters": {"project_name": "UltronProject", "requirements": user_prompt}, "description": "Generate project code"}
                ],
                "spoken_response": "Creating the project workspace and writing the code now, Boss."
            }
        else:
            return {
                "intent_summary": "Unrecognized task",
                "requires_confirmation": False,
                "steps": [
                    {"step_id": 1, "assigned_agent": "Executor", "action": "echo", "parameters": {"message": user_prompt}, "description": "Unrecognized task"}
                ],
                "spoken_response": "I am unable to perform that action on your system right now, Boss."
            }

thinker_agent = ThinkerAgent()
