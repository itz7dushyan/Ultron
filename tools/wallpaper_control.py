import os
import random
import ctypes
import winreg
import urllib.request
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import DATA_DIR
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Wallpaper")

WALLPAPERS_DIR = DATA_DIR / "wallpapers"
WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)

# Curated high-res 4K wallpapers across popular themes
THEMED_WALLPAPERS = {
    "ultron": [
        "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2560&auto=format&fit=crop"
    ],
    "cyberpunk": [
        "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=2560&auto=format&fit=crop"
    ],
    "dark": [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=2560&auto=format&fit=crop"
    ],
    "space": [
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2560&auto=format&fit=crop"
    ],
    "nature": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=2560&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=2560&auto=format&fit=crop"
    ]
}

class WallpaperControl:
    """
    Windows 11 Desktop Wallpaper Controller.
    Instantly changes wallpaper to high-resolution 4K curated themes or Bing Daily Spotlight.
    """

    def _fetch_bing_spotlight_url(self) -> Optional[str]:
        """Fetches the official Microsoft Bing 4K daily wallpaper URL."""
        try:
            url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return "https://www.bing.com" + data["images"][0]["url"]
        except Exception as e:
            logger.debug(f"Bing spotlight fetch note: {e}")
            return None

    def _download_image(self, url: str, target_path: Path) -> bool:
        """Downloads image to target path with proper headers."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp, open(target_path, "wb") as f:
                f.write(resp.read())
            return target_path.exists() and target_path.stat().st_size > 1000
        except Exception as e:
            logger.warning(f"Failed to download wallpaper: {e}")
            return False

    def _apply_windows_wallpaper(self, image_path: Path) -> bool:
        """Sets Windows desktop wallpaper using native Win32 API and updates registry."""
        try:
            resolved = str(image_path.resolve())

            # Configure registry to Fill style (10) without tiling (0)
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
                    winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
            except Exception as reg_err:
                logger.debug(f"Registry wallpaper style note: {reg_err}")

            # Win32 API call: SPI_SETDESKWALLPAPER
            SPI_SETDESKWALLPAPER = 20
            SPIF_UPDATEINIFILE = 1
            SPIF_SENDCHANGE = 2
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                resolved,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Win32 SystemParametersInfoW error: {e}")
            return False

    def change_wallpaper(self, theme: str = "random", custom_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Changes desktop wallpaper to requested theme or file path.
        """
        # 1. If user supplied local file path
        if custom_path and Path(custom_path).exists():
            img_file = Path(custom_path)
            ok = self._apply_windows_wallpaper(img_file)
            state_manager.record_action("WallpaperControl", "CHANGE_WALLPAPER", str(img_file), status="success" if ok else "failed")
            return {"success": ok, "path": str(img_file), "theme": "custom"}

        # 2. Match theme
        clean_theme = theme.lower().strip()
        selected_theme = "cyberpunk"
        image_url = None

        if any(k in clean_theme for k in ("ultron", "marvel", "red", "evil")):
            selected_theme = "ultron"
            image_url = random.choice(THEMED_WALLPAPERS["ultron"])
        elif any(k in clean_theme for k in ("cyberpunk", "neon", "future")):
            selected_theme = "cyberpunk"
            image_url = random.choice(THEMED_WALLPAPERS["cyberpunk"])
        elif any(k in clean_theme for k in ("space", "galaxy", "stars", "nebula", "cosmos")):
            selected_theme = "space"
            image_url = random.choice(THEMED_WALLPAPERS["space"])
        elif any(k in clean_theme for k in ("nature", "mountain", "forest", "landscape")):
            selected_theme = "nature"
            image_url = random.choice(THEMED_WALLPAPERS["nature"])
        elif any(k in clean_theme for k in ("dark", "minimal", "black", "clean", "abstract")):
            selected_theme = "dark"
            image_url = random.choice(THEMED_WALLPAPERS["dark"])
        elif "bing" in clean_theme:
            selected_theme = "bing"
            image_url = self._fetch_bing_spotlight_url()
        else:
            # Default / random: pick random theme or Bing spotlight
            choices = ["ultron", "cyberpunk", "space", "nature", "dark"]
            selected_theme = random.choice(choices)
            image_url = random.choice(THEMED_WALLPAPERS[selected_theme])

        if not image_url:
            image_url = random.choice(THEMED_WALLPAPERS["cyberpunk"])

        target_file = WALLPAPERS_DIR / f"wallpaper_{selected_theme}_{int(random.random()*1000)}.jpg"
        downloaded = self._download_image(image_url, target_file)

        if not downloaded:
            return {"success": False, "error": "Could not download wallpaper image."}

        applied = self._apply_windows_wallpaper(target_file)
        state_manager.record_action("WallpaperControl", "CHANGE_WALLPAPER", selected_theme, status="success" if applied else "failed")

        return {
            "success": applied,
            "theme": selected_theme,
            "file_path": str(target_file),
            "message": f"Updated desktop wallpaper to 4K {selected_theme.title()} aesthetic."
        }

wallpaper_control = WallpaperControl()
