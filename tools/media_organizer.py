import os
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from shared_state.state_manager import state_manager

DESKTOP_DIR = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default")) / "Desktop"

class MediaOrganizer:
    """
    Handles screenshot capture, media placement, and automated sequential numbering/organization.
    """

    def take_screenshot(self, target_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Captures full desktop screen and saves it into the target folder.
        """
        try:
            import pyautogui

            if target_folder:
                dest = Path(target_folder)
                if not dest.is_absolute():
                    dest = DESKTOP_DIR / target_folder
            else:
                dest = DESKTOP_DIR / "Screenshots"

            dest.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"Screenshot_{timestamp}.png"
            file_path = dest / filename

            img = pyautogui.screenshot()
            img.save(str(file_path))

            state_manager.record_action("MediaOrganizer", "TAKE_SCREENSHOT", str(file_path), status="success")
            return {
                "success": True,
                "file_path": str(file_path),
                "folder": str(dest),
                "message": f"Captured screenshot and saved to {dest.name}, Boss."
            }
        except Exception as e:
            state_manager.record_action("MediaOrganizer", "TAKE_SCREENSHOT", str(target_folder), details=str(e), status="failed")
            return {"success": False, "error": str(e)}

    def organize_screenshots(self, folder_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans a folder for screenshot images, sorts them chronologically, and renames
        them sequentially (Screenshot_001.png, Screenshot_002.png, etc.).
        """
        try:
            if folder_path:
                target_dir = Path(folder_path)
                if not target_dir.is_absolute():
                    target_dir = DESKTOP_DIR / folder_path
            else:
                target_dir = DESKTOP_DIR / "Screenshots"
                if not target_dir.exists():
                    target_dir = DESKTOP_DIR

            if not target_dir.exists():
                return {"success": False, "error": f"Directory '{target_dir}' does not exist."}

            image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
            images = [
                f for f in target_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

            if not images:
                return {"success": False, "message": f"No image files found to organize in {target_dir.name}, Boss."}

            # Sort chronologically by file creation timestamp
            images.sort(key=lambda x: x.stat().st_ctime)

            # Two-phase rename to avoid collision
            temp_files = []
            for i, img_path in enumerate(images, 1):
                ext = img_path.suffix
                temp_name = target_dir / f"__temp_organize_{i}_{int(time.time()*1000)}{ext}"
                img_path.rename(temp_name)
                temp_files.append(temp_name)

            renamed_count = 0
            for i, temp_path in enumerate(temp_files, 1):
                ext = temp_path.suffix
                new_name = target_dir / f"Screenshot_{i:03d}{ext}"
                temp_path.rename(new_name)
                renamed_count += 1

            state_manager.record_action("MediaOrganizer", "ORGANIZE_SCREENSHOTS", str(target_dir), details={"count": renamed_count}, status="success")
            return {
                "success": True,
                "count": renamed_count,
                "folder": str(target_dir),
                "message": f"Organized {renamed_count} screenshots sequentially in {target_dir.name}, Boss."
            }
        except Exception as e:
            state_manager.record_action("MediaOrganizer", "ORGANIZE_SCREENSHOTS", str(folder_path), details=str(e), status="failed")
            return {"success": False, "error": str(e)}

media_organizer = MediaOrganizer()
