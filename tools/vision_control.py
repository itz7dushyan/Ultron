import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import config, DATA_DIR
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.VisionControl")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

class VisionControl:
    """Multimodal Vision & Screen Analysis powered by Gemini 3.7 Flash."""

    def capture_screen(self, filename: str = "current_screen.png") -> Optional[Path]:
        """Captures a screenshot of the active Windows display."""
        target_path = SCREENSHOTS_DIR / filename
        
        # Method 1: Try PIL ImageGrab
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(str(target_path))
            return target_path
        except Exception as e:
            logger.debug(f"PIL ImageGrab attempt: {e}")

        # Method 2: Try MSS
        try:
            import mss
            with mss.MSS() as sct:
                sct.shot(output=str(target_path))
                return target_path
        except Exception as e:
            logger.debug(f"MSS grab attempt: {e}")

        return None

    def analyze_screen(self, user_question: str = "Describe what is currently on my screen.") -> Dict[str, Any]:
        """
        Captures the active screen and performs multimodal vision reasoning using Gemini 3.7 Flash.
        """
        image_path = self.capture_screen()
        if not image_path or not image_path.exists():
            return {
                "success": False,
                "error": "Could not capture active screen surface. Ensure you are running on an active Windows desktop session.",
                "analysis": "Screen capture is unavailable in background service mode."
            }

        try:
            import google.generativeai as genai
            from PIL import Image

            api_key = config.GEMINI_API_KEY or config.GEMINI_FALLBACK_API_KEY
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3.7-flash")

            img = Image.open(image_path)
            prompt = (
                f"You are the Vision module of Ultron. The user asks: '{user_question}'.\n"
                "Analyze this screenshot of their Windows desktop carefully and provide a direct, concise, and helpful answer."
            )
            response = model.generate_content([prompt, img])
            analysis_text = response.text.strip()

            state_manager.record_action(
                agent_name="VisionControl",
                action="ANALYZE_SCREEN",
                target=str(image_path),
                details={"question": user_question, "analysis_length": len(analysis_text)},
                status="success"
            )

            return {
                "success": True,
                "image_path": str(image_path),
                "analysis": analysis_text
            }
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": f"Encountered an issue analyzing the screen: {e}"
            }

vision_control = VisionControl()
