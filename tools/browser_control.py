import asyncio
import webbrowser
import logging
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

    def open_url_quick(self, url: str) -> Dict[str, Any]:
        """Directly launches URL in user's default OS browser (instant zero-dependency)."""
        clean_url = self._ensure_url(url)
        try:
            webbrowser.open(clean_url)
            state_manager.record_action("BrowserTools", "OPEN_URL", clean_url, status="success")
            return {"success": True, "url": clean_url, "message": f"Opened {clean_url} in browser"}
        except Exception as e:
            state_manager.record_action("BrowserTools", "OPEN_URL", clean_url, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

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
