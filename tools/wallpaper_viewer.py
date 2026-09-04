import threading
import time
import urllib.request
import tkinter as tk
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from config import DATA_DIR

THUMBNAILS_DIR = DATA_DIR / "wallpapers" / "thumbnails"
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

class WallpaperViewer:
    """
    Floating 4K Wallpaper Gallery Window.
    Displays curated wallpaper cards on screen so the user can see them and select.
    """

    def __init__(self):
        self._window: Optional[tk.Toplevel] = None
        self._root: Optional[tk.Tk] = None
        self._thread: Optional[threading.Thread] = None
        self.is_visible = False
        self.current_options: List[Dict[str, Any]] = []
        self.on_select_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def show(self, theme: str, options: List[Dict[str, Any]], on_select: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Shows the floating wallpaper preview window in a background GUI thread."""
        self.current_options = options
        self.on_select_callback = on_select

        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass

        self._thread = threading.Thread(target=self._run_gui, args=(theme, options), daemon=True)
        self._thread.start()

    def close(self):
        """Closes the gallery window."""
        if self._root:
            try:
                self._root.quit()
            except Exception:
                pass
        self.is_visible = False

    def _run_gui(self, theme: str, options: List[Dict[str, Any]]):
        try:
            self._root = tk.Tk()
            self._root.title(f"Ultron Wallpaper Gallery - {theme.title()}")
            self._root.attributes("-topmost", True)
            self._root.configure(bg="#0B0E14")

            # Center on screen
            win_w = 980
            win_h = 420
            sw = self._root.winfo_screenwidth()
            sh = self._root.winfo_screenheight()
            pos_x = (sw - win_w) // 2
            pos_y = (sh - win_h) // 2
            self._root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            self.is_visible = True

            # Header Frame
            header = tk.Frame(self._root, bg="#0B0E14")
            header.pack(fill="x", padx=20, pady=(15, 8))

            title = tk.Label(
                header,
                text=f"◈ ULTRON 4K WALLPAPER SELECTION: {theme.upper()}",
                font=("Segoe UI", 16, "bold"),
                fg="#FF6600",
                bg="#0B0E14"
            )
            title.pack(anchor="w")

            subtitle = tk.Label(
                header,
                text="Speak your choice (e.g. 'Sunset', 'Mountain', 'Option 1') or click any card below to apply:",
                font=("Segoe UI", 10),
                fg="#8899A6",
                bg="#0B0E14"
            )
            subtitle.pack(anchor="w")

            # Cards Container Frame
            cards_frame = tk.Frame(self._root, bg="#0B0E14")
            cards_frame.pack(fill="both", expand=True, padx=20, pady=10)

            for i, opt in enumerate(options[:5]):
                card = tk.Frame(
                    cards_frame,
                    bg="#141923",
                    bd=1,
                    relief="solid",
                    highlightbackground="#FF4500",
                    highlightthickness=1
                )
                card.pack(side="left", fill="both", expand=True, padx=6, pady=5)

                # Number Badge
                badge = tk.Label(
                    card,
                    text=f"OPTION {opt.get('id', i+1)}",
                    font=("Consolas", 10, "bold"),
                    fg="#FF9933",
                    bg="#221105",
                    padx=6,
                    pady=2
                )
                badge.pack(fill="x", pady=(8, 4), padx=8)

                # Color accent banner
                banner_colors = ["#FF4500", "#FF6600", "#FF8800", "#FFA500", "#FFB700"]
                accent = tk.Frame(card, height=4, bg=banner_colors[i % len(banner_colors)])
                accent.pack(fill="x", padx=8, pady=(0, 8))

                # Name Label
                name_lbl = tk.Label(
                    card,
                    text=opt.get("name", "Wallpaper"),
                    font=("Segoe UI", 11, "bold"),
                    fg="#FFFFFF",
                    bg="#141923",
                    wraplength=160,
                    justify="center"
                )
                name_lbl.pack(pady=4, padx=8)

                # Description Label
                desc_lbl = tk.Label(
                    card,
                    text=opt.get("desc", ""),
                    font=("Segoe UI", 8),
                    fg="#8899A6",
                    bg="#141923",
                    wraplength=160,
                    justify="center"
                )
                desc_lbl.pack(pady=4, padx=8, fill="both", expand=True)

                # Click Button
                def make_handler(chosen_opt):
                    return lambda: self._handle_card_click(chosen_opt)

                btn = tk.Button(
                    card,
                    text="Apply 4K",
                    font=("Segoe UI", 9, "bold"),
                    fg="#FFFFFF",
                    bg="#CC4400",
                    activebackground="#FF5500",
                    activeforeground="#FFFFFF",
                    relief="flat",
                    cursor="hand2",
                    command=make_handler(opt)
                )
                btn.pack(fill="x", padx=12, pady=(4, 12))

            # Footer / Close hint
            footer = tk.Frame(self._root, bg="#0B0E14")
            footer.pack(fill="x", padx=20, pady=(0, 10))
            
            close_btn = tk.Button(
                footer,
                text="✕ Dismiss Gallery",
                font=("Segoe UI", 9),
                fg="#778899",
                bg="#141923",
                relief="flat",
                command=self.close
            )
            close_btn.pack(side="right")

            # Auto-close after 35 seconds of inactivity
            self._root.after(35000, self.close)
            self._root.mainloop()
        except Exception as e:
            pass
        finally:
            self.is_visible = False

    def _handle_card_click(self, opt: Dict[str, Any]):
        """Handler when user clicks a card."""
        if self.on_select_callback:
            try:
                self.on_select_callback(opt)
            except Exception:
                pass
        self.close()

wallpaper_viewer = WallpaperViewer()
