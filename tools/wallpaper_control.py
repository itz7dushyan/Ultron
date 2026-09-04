import os
import random
import ctypes
import winreg
import urllib.request
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import DATA_DIR
from shared_state.state_manager import state_manager

logger = logging.getLogger("Ultron.Wallpaper")

WALLPAPERS_DIR = DATA_DIR / "wallpapers"
WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)

# Curated 4K Wallpapers with explicit names & descriptions for smart selection
WALLPAPER_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "nature": [
        {
            "id": 1,
            "name": "Alpine Mountain Peak",
            "desc": "Crisp snowy summits under crystal clear skies",
            "keywords": ["1", "one", "first", "alpine", "mountain", "peak", "snow"],
            "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 2,
            "name": "Misty Autumn Forest",
            "desc": "Lush evergreen pine forest immersed in morning mist",
            "keywords": ["2", "two", "second", "forest", "mist", "autumn", "trees", "pine"],
            "url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 3,
            "name": "Emerald Aurora Lake",
            "desc": "Vibrant green northern lights reflecting over still waters",
            "keywords": ["3", "three", "third", "aurora", "lake", "northern lights", "green", "emerald"],
            "url": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 4,
            "name": "Tropical Sunset Coast",
            "desc": "Golden hour waves gently crashing on scenic shore",
            "keywords": ["4", "four", "fourth", "sunset", "coast", "beach", "ocean", "sea"],
            "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 5,
            "name": "Cascading Waterfall Valley",
            "desc": "Pristine mountain waterfall surrounded by emerald moss",
            "keywords": ["5", "five", "fifth", "waterfall", "valley", "cascade", "stream"],
            "url": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?q=80&w=2560&auto=format&fit=crop"
        }
    ],
    "cyberpunk": [
        {
            "id": 1,
            "name": "Neon Neo-Tokyo Skyline",
            "desc": "Futuristic skyscrapers glowing in rain",
            "keywords": ["1", "one", "skyline", "tokyo", "city"],
            "url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 2,
            "name": "Cyber Alleyway",
            "desc": "Synthwave purple neon signs in rain-slicked alley",
            "keywords": ["2", "two", "alley", "alleyway", "purple"],
            "url": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 3,
            "name": "Synthwave Horizon",
            "desc": "Retro-futuristic sports car and purple sunset",
            "keywords": ["3", "three", "horizon", "retro", "synthwave"],
            "url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 4,
            "name": "Orange Circuit Core",
            "desc": "High-tech bionic processor matrix with orange energy",
            "keywords": ["4", "four", "circuit", "orange", "core"],
            "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 5,
            "name": "Blade Runner Metropolis",
            "desc": "Towering futuristic megastructure at dusk",
            "keywords": ["5", "five", "metropolis", "blade runner", "towers"],
            "url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=2560&auto=format&fit=crop"
        }
    ],
    "space": [
        {
            "id": 1,
            "name": "Deep Cosmic Nebula",
            "desc": "Hubble gas pillars in deep violet and cyan",
            "keywords": ["1", "one", "nebula", "violet", "gas", "pillars"],
            "url": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 2,
            "name": "Earth Orbit Horizon",
            "desc": "Curvature of blue Earth against dark cosmos",
            "keywords": ["2", "two", "earth", "orbit", "horizon"],
            "url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 3,
            "name": "Milky Way Arch",
            "desc": "Billion stars spanning dark mountainous night",
            "keywords": ["3", "three", "milky way", "galaxy", "stars"],
            "url": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 4,
            "name": "Solar Flare Corona",
            "desc": "Massive solar flare eruption in orange plasma",
            "keywords": ["4", "four", "sun", "solar", "flare", "corona"],
            "url": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 5,
            "name": "Interstellar Starfield",
            "desc": "Crystal clear cluster of distant galaxies",
            "keywords": ["5", "five", "cluster", "starfield", "deep space"],
            "url": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=80&w=2560&auto=format&fit=crop"
        }
    ],
    "ultron": [
        {
            "id": 1,
            "name": "Crimson Ultron Core",
            "desc": "Marvel Ultron menacing red optics in dark metallic armor",
            "keywords": ["1", "one", "core", "red", "eyes", "crimson"],
            "url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 2,
            "name": "Vibranium Chassis",
            "desc": "Sleek titanium and vibranium mechanical plates",
            "keywords": ["2", "two", "vibranium", "armor", "chassis", "metal"],
            "url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 3,
            "name": "Neural Arc Matrix",
            "desc": "Pulsing red robotic arc core with circuit glow",
            "keywords": ["3", "three", "arc", "matrix", "glow", "circuits"],
            "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 4,
            "name": "Autonomous Drone Armada",
            "desc": "Metallic sentinels taking flight in formations",
            "keywords": ["4", "four", "drone", "armada", "sentinels", "fleet"],
            "url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 5,
            "name": "Artificial Superintelligence",
            "desc": "Interconnected cybernetic hivemind in high definition",
            "keywords": ["5", "five", "ai", "mind", "hivemind", "intelligence"],
            "url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2560&auto=format&fit=crop"
        }
    ],
    "dark": [
        {
            "id": 1,
            "name": "Obsidian Geometric Waves",
            "desc": "Minimalist matte black 3D low-poly landscape",
            "keywords": ["1", "one", "obsidian", "geometric", "polygons", "black"],
            "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 2,
            "name": "Liquid Charcoal Silk",
            "desc": "Monochrome dark fluid curves with subtle lighting",
            "keywords": ["2", "two", "charcoal", "liquid", "silk", "fluid"],
            "url": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 3,
            "name": "Minimalist Nocturne",
            "desc": "Deep pitch black with razor-thin golden horizon",
            "keywords": ["3", "three", "nocturne", "minimal", "gold", "horizon"],
            "url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 4,
            "name": "Carbon Fiber Weave",
            "desc": "Aerospace carbon texture with subtle contrast",
            "keywords": ["4", "four", "carbon", "fiber", "texture", "weave"],
            "url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2560&auto=format&fit=crop"
        },
        {
            "id": 5,
            "name": "Midnight Gradient",
            "desc": "Smoky dark grey atmospheric gradients",
            "keywords": ["5", "five", "midnight", "gradient", "smoke", "grey"],
            "url": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?q=80&w=2560&auto=format&fit=crop"
        }
    ]
}

class WallpaperControl:
    """
    Windows 11 Desktop Wallpaper Controller.
    Supports interactive choice curation, natural voice selection, and instant 4K setting.
    """

    def __init__(self):
        self.pending_theme: Optional[str] = None
        self.pending_options: List[Dict[str, Any]] = []

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

    def get_theme_options(self, theme: str) -> List[Dict[str, Any]]:
        """Returns the curated options for the requested theme."""
        clean = theme.lower().strip()
        matched = "nature"
        for key in WALLPAPER_CATALOG:
            if key in clean:
                matched = key
                break
        self.pending_theme = matched
        self.pending_options = WALLPAPER_CATALOG[matched]
        return self.pending_options

    def resolve_selection(self, user_choice: str) -> Optional[Dict[str, Any]]:
        """Matches user's follow-up choice (e.g. '1', 'mountain', 'sunset') against pending options."""
        choice_clean = user_choice.lower().strip()
        options = self.pending_options or WALLPAPER_CATALOG.get("nature", [])

        for opt in options:
            if any(k in choice_clean.split() or k == choice_clean for k in opt["keywords"]):
                return opt
            if opt["name"].lower() in choice_clean:
                return opt

        # Fallback: check if number is spoken
        for i, opt in enumerate(options, 1):
            if str(i) in choice_clean or f"number {i}" in choice_clean or f"option {i}" in choice_clean:
                return opt

        return None

    def apply_wallpaper_url(self, name: str, url: str, theme: str = "custom") -> Dict[str, Any]:
        """Downloads and applies a specific wallpaper URL directly."""
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        target_file = WALLPAPERS_DIR / f"{theme}_{safe_name}.jpg"

        if not target_file.exists() or target_file.stat().st_size < 1000:
            ok = self._download_image(url, target_file)
            if not ok:
                return {"success": False, "error": f"Failed to download {name} wallpaper."}

        applied = self._apply_windows_wallpaper(target_file)
        state_manager.record_action("WallpaperControl", "CHANGE_WALLPAPER", f"{theme}: {name}", status="success" if applied else "failed")
        return {
            "success": applied,
            "theme": theme,
            "name": name,
            "file_path": str(target_file),
            "message": f"Successfully applied 4K '{name}' wallpaper to your desktop, Boss."
        }

    def change_wallpaper(self, theme: str = "random", custom_path: Optional[str] = None, option_choice: Optional[str] = None) -> Dict[str, Any]:
        """
        Changes desktop wallpaper. If option_choice is provided, sets directly.
        """
        if custom_path and Path(custom_path).exists():
            img_file = Path(custom_path)
            ok = self._apply_windows_wallpaper(img_file)
            state_manager.record_action("WallpaperControl", "CHANGE_WALLPAPER", str(img_file), status="success" if ok else "failed")
            return {"success": ok, "path": str(img_file), "theme": "custom", "message": "Custom wallpaper set, Boss."}

        # Check if user is answering a pending choice (e.g. 'sunset', 'first one', '2')
        if option_choice:
            matched_opt = self.resolve_selection(option_choice)
            if matched_opt:
                return self.apply_wallpaper_url(matched_opt["name"], matched_opt["url"], self.pending_theme or "custom")

        # Check theme
        clean_theme = theme.lower().strip()
        matched_category = "nature"
        for cat in WALLPAPER_CATALOG:
            if cat in clean_theme:
                matched_category = cat
                break

        options = self.get_theme_options(matched_category)
        
        # Check if prompt included a specific option keyword right away (e.g. "change wallpaper to nature mountain")
        for opt in options:
            if any(k in clean_theme for k in opt["keywords"] if len(k) > 2):
                return self.apply_wallpaper_url(opt["name"], opt["url"], matched_category)

        # Pick random if "random" explicitly requested
        if clean_theme in ("random", "bing"):
            if clean_theme == "bing":
                b_url = self._fetch_bing_spotlight_url()
                if b_url:
                    return self.apply_wallpaper_url("Bing Spotlight", b_url, "bing")
            opt = random.choice(options)
            return self.apply_wallpaper_url(opt["name"], opt["url"], matched_category)

        # Interactive options return: Ultron will speak the curated options to the user
        opt_names = [f"{o['id']}: {o['name']}" for o in options]
        spoken = (
            f"Boss, maine {matched_category.title()} category se 5 4K options ready kiye hain: "
            f"1 - {options[0]['name']}, 2 - {options[1]['name']}, 3 - {options[2]['name']}, "
            f"4 - {options[3]['name']}, aur 5 - {options[4]['name']}. "
            f"Aap kaunsa lagana chahenge, ya koi specific style bataiye?"
        )

        return {
            "success": True,
            "interactive": True,
            "theme": matched_category,
            "options": options,
            "spoken_response": spoken,
            "message": f"Presented 5 {matched_category} wallpaper options: {', '.join(opt_names)}"
        }

wallpaper_control = WallpaperControl()
