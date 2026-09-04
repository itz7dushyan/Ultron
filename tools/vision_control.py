import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import config, DATA_DIR
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.VisionControl")
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

# Ensure Per-Monitor DPI Awareness so screen pixels match cursor coordinates at 150% scaling
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class VisionControl:
    """
    Multimodal Vision & Screen Analysis powered by Gemini 3.7 Flash.
    Provides desktop screenshotting, screen reading, visual element localization,
    and DPI-calibrated mouse interaction.
    """

    def capture_screen(self, filename: str = "current_screen.png") -> Optional[Path]:
        """Captures a high-resolution screenshot of the primary Windows display."""
        target_path = SCREENSHOTS_DIR / filename

        # Method 1: MSS (Fast, direct GDI capture, independent of desktop handle issues)
        try:
            import mss
            from PIL import Image
            with mss.MSS() as sct:
                # Primary monitor
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.save(str(target_path))
                return target_path
        except Exception as e:
            logger.debug(f"MSS grab notice: {e}")

        # Method 2: PIL ImageGrab fallback
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(str(target_path))
            return target_path
        except Exception as e:
            logger.debug(f"PIL ImageGrab fallback notice: {e}")

        return None

    def analyze_screen(self, user_question: str = "Describe what is currently on my screen.") -> Dict[str, Any]:
        """
        Captures the active screen and performs multimodal vision reasoning using Gemini 3.7 Flash.
        """
        image_path = self.capture_screen()
        if not image_path or not image_path.exists():
            return {
                "success": False,
                "error": "Could not capture active screen surface. Ensure desktop is accessible.",
                "analysis": "Screen capture is currently unavailable."
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

    def locate_element(self, target_description: str, screenshot_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Visually grounds a UI element or button on screen using Gemini 3.7 Flash.
        Returns normalized bounding box and calibrated screen pixel coordinates.
        """
        img_path = screenshot_path or self.capture_screen("element_locate.png")
        if not img_path or not img_path.exists():
            return {"found": False, "error": "Unable to capture screen for element localization."}

        try:
            from PIL import Image
            import google.generativeai as genai

            img = Image.open(img_path)
            img_w, img_h = img.size

            system_instruction = (
                "You are Ultron's Visual Grounding and UI Locator engine.\n"
                f"The image resolution is {img_w}x{img_h} pixels.\n"
                f"Locate the target UI element or text: '{target_description}'.\n"
                "Return ONLY a JSON object matching this exact schema:\n"
                "{\n"
                '  "found": true/false,\n'
                '  "confidence": 0.0 to 1.0,\n'
                '  "element_name": "exact label or name of element",\n'
                '  "box_2d": [ymin, xmin, ymax, xmax],\n'  # normalized 0-1000
                '  "description": "short description of location"\n'
                "}\n"
                "If the element is not visible or cannot be found, return {\"found\": false, \"error\": \"Reason\"}."
            )

            api_key = config.GEMINI_API_KEY or config.GEMINI_FALLBACK_API_KEY
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-3.7-flash",
                system_instruction=system_instruction,
                generation_config={"response_mime_type": "application/json", "temperature": 0.1}
            )

            resp = model.generate_content([f"Find this UI element on screen: {target_description}", img])
            data = json.loads(resp.text)

            if not data.get("found"):
                return {"found": False, "error": data.get("error", f"Could not find '{target_description}' on screen.")}

            box = data.get("box_2d", [0, 0, 0, 0])
            ymin, xmin, ymax, xmax = box[0], box[1], box[2], box[3]

            # Convert normalized 0-1000 coordinates to actual screen pixels
            center_x = int(((xmin + xmax) / 2.0) * (img_w / 1000.0))
            center_y = int(((ymin + ymax) / 2.0) * (img_h / 1000.0))

            return {
                "found": True,
                "confidence": data.get("confidence", 0.9),
                "element_name": data.get("element_name", target_description),
                "box_2d": box,
                "center_x": center_x,
                "center_y": center_y,
                "screen_size": (img_w, img_h),
                "description": data.get("description", "")
            }
        except Exception as e:
            logger.warning(f"Element visual grounding note: {e}")
            return {"found": False, "error": str(e)}

    def click_element(self, target_description: str, double_click: bool = False, right_click: bool = False) -> Dict[str, Any]:
        """
        Locates an element on screen visually via Gemini 3.7 Flash and clicks it with calibrated coordinates.
        """
        loc = self.locate_element(target_description)
        if not loc.get("found"):
            return {
                "success": False,
                "target": target_description,
                "error": loc.get("error", f"Element '{target_description}' not visible on screen.")
            }

        cx = loc["center_x"]
        cy = loc["center_y"]

        try:
            import pyautogui
            # Smooth cursor transition
            pyautogui.moveTo(cx, cy, duration=0.25)
            if double_click:
                pyautogui.doubleClick()
                action_name = "DOUBLE_CLICK"
            elif right_click:
                pyautogui.rightClick()
                action_name = "RIGHT_CLICK"
            else:
                pyautogui.click()
                action_name = "CLICK"

            state_manager.record_action(
                agent_name="VisionControl",
                action=action_name,
                target=target_description,
                details={"x": cx, "y": cy, "confidence": loc.get("confidence")},
                status="success"
            )

            return {
                "success": True,
                "target": target_description,
                "x": cx,
                "y": cy,
                "message": f"Clicked '{target_description}' at ({cx}, {cy}), Boss."
            }
        except Exception as e:
            return {"success": False, "target": target_description, "error": str(e)}

vision_control = VisionControl()

