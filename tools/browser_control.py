import asyncio
import webbrowser
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Browser")

class BrowserTools:
    """Fast Playwright browser controller with fallback to system default browser."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_url(self, url: str) -> str:
        if not url.startswith("http://") and not url.startswith("https://"):
            return f"https://{url}"
        return url

    def _get_chrome_exe(self) -> Optional[Path]:
        import os
        candidates = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    CHROME_PROFILES = {
        "risala": "Profile 1",
        "risala digital": "Profile 1",
        "risala digital marketing": "Profile 1",
        "agency": "Profile 1",
        "work": "Profile 1",
        "seo": "Profile 1",
        "web": "Profile 1",
        "digital": "Profile 1",
        "itzdushyant": "Default",
        "itz dushyant": "Default",
        "dushyant": "Default",
        "personal": "Default"
    }

    def resolve_profile(self, name_or_alias: Optional[str] = None) -> str:
        """Resolves profile nickname to exact Chrome profile directory name."""
        if not name_or_alias:
            return "Profile 1"  # Default to Risala Digital Marketing
        clean = name_or_alias.lower().strip()
        for k, v in self.CHROME_PROFILES.items():
            if k in clean:
                return v
        return "Profile 1"

    def open_profile(self, profile_name: str, url: str = "https://www.google.com") -> Dict[str, Any]:
        """Launches Chrome with the specified user profile (Risala Digital Marketing or itzdushyant)."""
        target = self.resolve_profile(profile_name)
        return self.open_url_quick(url, profile=target)

    def open_url_quick(self, url: str, profile: Optional[str] = None) -> Dict[str, Any]:
        """Directly launches URL in specified Chrome profile (defaults to Risala Digital Marketing for agency/web tasks)."""
        clean_url = self._ensure_url(url)
        chrome_exe = self._get_chrome_exe()
        target_profile = self.resolve_profile(profile)

        try:
            if chrome_exe and chrome_exe.exists():
                import subprocess
                subprocess.Popen([str(chrome_exe), f"--profile-directory={target_profile}", clean_url], shell=False)
                state_manager.record_action("BrowserTools", "OPEN_URL", clean_url, details={"profile": target_profile}, status="success")
                return {"success": True, "url": clean_url, "profile": target_profile, "message": f"Opened {clean_url} in Chrome ({target_profile})"}
            else:
                webbrowser.open(clean_url)
                state_manager.record_action("BrowserTools", "OPEN_URL", clean_url, status="success")
                return {"success": True, "url": clean_url, "message": f"Opened {clean_url} in browser"}
        except Exception as e:
            state_manager.record_action("BrowserTools", "OPEN_URL", clean_url, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def search_google(self, query: str) -> Dict[str, Any]:
        """Searches Google for query in user's browser."""
        import urllib.parse
        encoded = urllib.parse.quote(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        res = self.open_url_quick(url)
        res["message"] = f"Searching Google for '{query}', Boss."
        return res

    def search_youtube(self, query: str) -> Dict[str, Any]:
        """Searches YouTube for query in user's browser."""
        import urllib.parse
        encoded = urllib.parse.quote(query.strip())
        url = f"https://www.youtube.com/results?search_query={encoded}"
        res = self.open_url_quick(url)
        res["message"] = f"Searching YouTube for '{query}', Boss."
        return res

    def new_tab(self) -> Dict[str, Any]:
        """Opens a new browser tab with Ctrl+T."""
        import pyautogui
        pyautogui.hotkey('ctrl', 't')
        state_manager.record_action("BrowserTools", "NEW_TAB", "Ctrl+T", status="success")
        return {"success": True, "message": "Opened new tab, Boss."}

    def reload_tab(self) -> Dict[str, Any]:
        """Reloads current browser tab with Ctrl+R."""
        import pyautogui
        pyautogui.hotkey('ctrl', 'r')
        state_manager.record_action("BrowserTools", "RELOAD_TAB", "Ctrl+R", status="success")
        return {"success": True, "message": "Reloading page, Boss."}

    def switch_tab(self) -> Dict[str, Any]:
        """Switches to the next browser tab with Ctrl+Tab."""
        import pyautogui
        pyautogui.hotkey('ctrl', 'tab')
        state_manager.record_action("BrowserTools", "SWITCH_TAB", "Ctrl+Tab", status="success")
        return {"success": True, "message": "Switched tab, Boss."}

    async def _init_playwright(self, headless: bool = False):
        """Initializes Playwright browser session if not already running."""
        try:
            from playwright.async_api import async_playwright
            if not self._playwright:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=headless)
                self._context = await self._browser.new_context()
                self._page = await self._context.new_page()
        except Exception as e:
            logger.warning(f"Playwright initialization note: {e}")
            raise

    async def navigate(self, url: str, headless: bool = False) -> Dict[str, Any]:
        """Navigates to URL using Playwright for programmatic control."""
        clean_url = self._ensure_url(url)
        try:
            await self._init_playwright(headless=headless)
            response = await self._page.goto(clean_url, timeout=30000)
            title = await self._page.title()
            state_manager.record_action("BrowserTools", "NAVIGATE", clean_url, details={"title": title}, status="success")
            return {
                "success": True,
                "url": clean_url,
                "title": title,
                "status": response.status if response else 200
            }
        except Exception as e:
            # Fallback to quick browser open if Playwright fails
            logger.info("Falling back to system browser open...")
            return self.open_url_quick(clean_url)

    async def click(self, selector: str) -> Dict[str, Any]:
        """Clicks an element by CSS selector, text, or accessibility label."""
        if not self._page:
            return {"success": False, "error": "No active browser session"}
        try:
            await self._page.click(selector, timeout=10000)
            state_manager.record_action("BrowserTools", "CLICK", selector, status="success")
            return {"success": True, "message": f"Clicked {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Fills input or types text into an element."""
        if not self._page:
            return {"success": False, "error": "No active browser session"}
        try:
            await self._page.fill(selector, text, timeout=10000)
            state_manager.record_action("BrowserTools", "TYPE_TEXT", selector, details={"length": len(text)}, status="success")
            return {"success": True, "message": f"Typed text into {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, output_path: str) -> Dict[str, Any]:
        """Takes a screenshot only when requested for debugging or visual verification."""
        if not self._page:
            return {"success": False, "error": "No active browser session"}
        try:
            await self._page.screenshot(path=output_path)
            state_manager.record_action("BrowserTools", "SCREENSHOT", output_path, status="success")
            return {"success": True, "path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_browser(self):
        """Closes Playwright browser instance cleanly."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
        except Exception:
            pass

browser_tools = BrowserTools()
