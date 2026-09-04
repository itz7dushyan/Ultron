import math
import time
import random
import threading
import ctypes
from typing import Optional, List

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080

class HudParticle:
    """A floating glowing energy particle moving along screen borders."""
    def __init__(self, screen_w: int, screen_h: int, border: str):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.border = border  # 'bottom', 'top', 'left', 'right'
        self.reset()

    def reset(self):
        if self.border in ('bottom', 'top'):
            self.x = random.uniform(0, self.screen_w)
            self.base_y = self.screen_h - 18 if self.border == 'bottom' else 18
            self.y = self.base_y
            self.vx = random.uniform(-1.8, 1.8)
            self.vy = random.uniform(-0.6, 0.6)
        else:
            self.base_x = 18 if self.border == 'left' else self.screen_w - 18
            self.x = self.base_x
            self.y = random.uniform(0, self.screen_h)
            self.vx = random.uniform(-0.6, 0.6)
            self.vy = random.uniform(-1.8, 1.8)

        self.size = random.uniform(2.5, 6.0)
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(1.2, 2.5)
        self.color = random.choice(["#FF4500", "#FF6600", "#FF8800", "#FFA500", "#FFD700", "#FF3300"])

    def update(self, t: float, is_speaking: bool):
        mult = 2.4 if is_speaking else 1.0
        amp = 28 if is_speaking else 12

        if self.border == 'bottom':
            self.x += self.vx * mult
            if self.x < 0: self.x = self.screen_w
            elif self.x > self.screen_w: self.x = 0
            self.y = self.base_y - abs(math.sin(t * self.speed * 1.5 + self.phase)) * amp
        elif self.border == 'top':
            self.x += self.vx * mult
            if self.x < 0: self.x = self.screen_w
            elif self.x > self.screen_w: self.x = 0
            self.y = self.base_y + abs(math.sin(t * self.speed * 1.5 + self.phase)) * amp
        elif self.border == 'left':
            self.y += self.vy * mult
            if self.y < 0: self.y = self.screen_h
            elif self.y > self.screen_h: self.y = 0
            self.x = self.base_x + abs(math.sin(t * self.speed * 1.5 + self.phase)) * amp
        elif self.border == 'right':
            self.y += self.vy * mult
            if self.y < 0: self.y = self.screen_h
            elif self.y > self.screen_h: self.y = 0
            self.x = self.base_x - abs(math.sin(t * self.speed * 1.5 + self.phase)) * amp


class UltronHudOverlay:
    """
    Futuristic Screen-Border Aurora & Central Pulsing Arc Reactor HUD Overlay.
    - Click-Through: WS_EX_TRANSPARENT ensures clicks pass to desktop/apps completely.
    - Zero Taskbar presence: WS_EX_TOOLWINDOW.
    - Dynamic: Aurora waves pulse and particle frequency doubles when Ultron speaks!
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._root = None
        self._canvas = None
        self.is_active = False
        self.is_speaking = False
        self.current_state = "IDLE"  # IDLE, LISTENING, SPEAKING
        self.fade_alpha = 0.0
        self.target_alpha = 0.0
        self.last_active_time = 0.0
        self.particles: List[HudParticle] = []
        self._running = False

    def start(self):
        """Launches HUD overlay window in background GUI thread."""
        if self._thread and self._thread.is_alive():
            return

        self._running = True
        self._thread = threading.Thread(target=self._gui_loop, daemon=True)
        self._thread.start()

    def set_state(self, state: str):
        """Sets state: 'IDLE', 'LISTENING', 'SPEAKING'."""
        self.current_state = state.upper()
        if self.current_state in ("LISTENING", "SPEAKING"):
            self.last_active_time = time.time()
            self.target_alpha = 1.0
            self.is_speaking = (self.current_state == "SPEAKING")
        else:
            self.is_speaking = False

    def trigger_wake(self):
        """Triggers vibrant wake animation on wake-word detection."""
        self.set_state("LISTENING")
        self.last_active_time = time.time()

    def trigger_speaking(self, speaking: bool):
        """Toggles speaking state."""
        self.is_speaking = speaking
        if speaking:
            self.current_state = "SPEAKING"
            self.last_active_time = time.time()
            self.target_alpha = 1.0
        else:
            self.current_state = "LISTENING"
            self.last_active_time = time.time()

    def _gui_loop(self):
        import tkinter as tk
        try:
            self._root = tk.Tk()
            self._root.title("Ultron Aura HUD")
            self._root.overrideredirect(True)
            self._root.wm_attributes("-topmost", True)
            
            # Pure transparency key
            transparent_color = "#000001"
            self._root.wm_attributes("-transparentcolor", transparent_color)
            self._root.config(bg=transparent_color)

            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            self._root.geometry(f"{screen_w}x{screen_h}+0+0")

            self._canvas = tk.Canvas(
                self._root,
                width=screen_w,
                height=screen_h,
                bg=transparent_color,
                highlightthickness=0
            )
            self._canvas.pack(fill="both", expand=True)

            # Apply Windows click-through styles & HWND_TOPMOST
            hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
            if hwnd == 0:
                hwnd = self._root.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
            )
            # Assert TopMost and ShowWindow
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

            # Start with an immediate wake flare so user sees Ultron has come alive
            self.fade_alpha = 1.0
            self.target_alpha = 1.0
            self.last_active_time = time.time()

            # Initialize 80 glowing particles along screen borders
            self.particles = []
            for _ in range(35):
                self.particles.append(HudParticle(screen_w, screen_h, 'bottom'))
            for _ in range(25):
                self.particles.append(HudParticle(screen_w, screen_h, 'top'))
            for _ in range(12):
                self.particles.append(HudParticle(screen_w, screen_h, 'left'))
            for _ in range(12):
                self.particles.append(HudParticle(screen_w, screen_h, 'right'))

            start_time = time.time()

            def animate():
                if not self._running:
                    self._root.destroy()
                    return

                t = time.time() - start_time
                now = time.time()

                # Inactivity timer: auto-dim to IDLE after 8s of silence
                if self.current_state != "IDLE" and (now - self.last_active_time) > 8.0:
                    self.target_alpha = 0.0
                    if self.fade_alpha <= 0.05:
                        self.current_state = "IDLE"

                # Smooth alpha interpolation
                self.fade_alpha += (self.target_alpha - self.fade_alpha) * 0.12

                self._canvas.delete("all")

                if self.fade_alpha > 0.02:
                    cx = screen_w // 2
                    cy = screen_h // 2

                    # 1. Draw Border Aurora Energy Ribbons
                    self._draw_aurora_ribbon(screen_w, screen_h, t, is_top=False)
                    self._draw_aurora_ribbon(screen_w, screen_h, t, is_top=True)

                    # 2. Draw Floating Glowing Particles
                    for p in self.particles:
                        p.update(t, self.is_speaking)
                        sz = p.size * (1.3 if self.is_speaking else 1.0)
                        self._canvas.create_oval(
                            p.x - sz, p.y - sz, p.x + sz, p.y + sz,
                            fill=p.color, outline=""
                        )

                    # 3. Draw Central Floating 3D Arc Reactor Core ("ULTRON")
                    self._draw_central_reactor(cx, cy, t)

                self._root.after(16, animate)  # ~60 FPS

            self._root.after(16, animate)
            self._root.mainloop()
        except Exception as e:
            pass

    def _draw_aurora_ribbon(self, screen_w: int, screen_h: int, t: float, is_top: bool):
        """Draws smooth organic aurora wave ribbons along the screen border."""
        base_y = 12 if is_top else screen_h - 12
        step = 30
        points = []
        mult = 2.5 if self.is_speaking else 1.0
        amp = 18 if self.is_speaking else 7

        for x in range(0, screen_w + step, step):
            wave1 = math.sin(x * 0.008 + t * 2.2 * mult)
            wave2 = math.cos(x * 0.015 - t * 1.6 * mult)
            y_offset = (wave1 + wave2) * amp * (1 if is_top else -1)
            points.append((x, base_y + y_offset))

        # Draw glowing wave lines
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self._canvas.create_line(x1, y1, x2, y2, fill="#FF4500", width=4)
            self._canvas.create_line(x1, y1, x2, y2, fill="#FFA500", width=1.8)

    def _draw_central_reactor(self, cx: int, cy: int, t: float):
        """Draws 3D-styled pulsing circular arc reactor core with 'ULTRON' text."""
        # Bass bounce calculation
        bounce = (math.sin(t * 8.0) * 8.0) if self.is_speaking else (math.sin(t * 2.0) * 2.0)
        base_r = 65 + bounce

        # Outer Bass Shockwave Ring
        if self.is_speaking:
            ripple_r = base_r + 20 + abs(math.sin(t * 6.0)) * 25
            self._canvas.create_oval(
                cx - ripple_r, cy - ripple_r, cx + ripple_r, cy + ripple_r,
                outline="#FF4500", width=1.5
            )

        # Concentric Tech Rings
        self._canvas.create_oval(
            cx - (base_r + 14), cy - (base_r + 14), cx + (base_r + 14), cy + (base_r + 14),
            outline="#FF8800", width=2
        )
        self._canvas.create_oval(
            cx - base_r, cy - base_r, cx + base_r, cy + base_r,
            outline="#FFAA00", width=3
        )

        # Rotating Segmented Arc Segments
        angle_offset = t * (3.0 if self.is_speaking else 1.0)
        for i in range(6):
            start_ang = (i * 60 + angle_offset * 40) % 360
            self._canvas.create_arc(
                cx - (base_r + 6), cy - (base_r + 6), cx + (base_r + 6), cy + (base_r + 6),
                start=start_ang, extent=32, outline="#FFD700", width=3.5, style="arc"
            )

        # Inner Glowing Orb
        inner_r = base_r - 16
        self._canvas.create_oval(
            cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
            fill="#330A00", outline="#FF5500", width=2.5
        )

        # Core Pulsing Dot
        center_glow = 8 + (abs(math.sin(t * 10.0)) * 6 if self.is_speaking else 3)
        self._canvas.create_oval(
            cx - center_glow, cy - (center_glow + 14), cx + center_glow, cy - (center_glow + 14),
            fill="#FFD700", outline="#FFA500"
        )

        # Central Text: ULTRON
        status_text = "SPEAKING" if self.is_speaking else "LISTENING"
        self._canvas.create_text(
            cx, cy + 2,
            text="ULTRON",
            fill="#FFFFFF",
            font=("Segoe UI Black", 16, "bold")
        )
        self._canvas.create_text(
            cx, cy + 20,
            text=status_text,
            fill="#FFA500",
            font=("Consolas", 8, "bold")
        )

    def stop(self):
        """Stops HUD overlay cleanly."""
        self._running = False

hud_overlay = UltronHudOverlay()
