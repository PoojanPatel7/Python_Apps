"""
╔══════════════════════════════════════════════╗
║      Speed Checker — Live Speed Monitor      ║
║     Real-time Download & Upload Tracker      ║
╚══════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import font as tkfont
import psutil
import time
import math
import os
import sys


class SpeedMonitorApp:
    """A premium dark-themed real-time internet speed monitor."""

    # ── Color Palette ────────────────────────────────────────────
    BG_DARK       = "#0a0a0f"
    BG_CARD       = "#12121a"
    BG_CARD_HOVER = "#1a1a28"
    BORDER_DIM    = "#1e1e30"
    BORDER_GLOW   = "#2a2a45"

    # Accent colors
    CYAN_BRIGHT   = "#00e5ff"
    CYAN_DIM      = "#007a8a"
    CYAN_GLOW     = "#00b8d4"
    MAGENTA       = "#ff00e5"
    MAGENTA_DIM   = "#8a007a"
    MAGENTA_GLOW  = "#d400b8"
    GREEN_ACCENT  = "#00ff88"
    RED_ACCENT    = "#ff3366"
    YELLOW_ACCENT = "#ffd600"

    TEXT_PRIMARY   = "#e8e8f0"
    TEXT_SECONDARY = "#8888a0"
    TEXT_DIM       = "#555570"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Speed Checker")
        self.root.configure(bg=self.BG_DARK)
        self.root.resizable(True, True)

        # ── Window geometry ──────────────────────────────────────
        win_w, win_h = 520, 680
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - win_w - 30
        y = 40
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(440, 580)

        # Remove default title bar for sleek look (optional — keep it for drag)
        self.root.overrideredirect(False)

        # ── State ────────────────────────────────────────────────
        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()
        self.dl_history: list[float] = [0.0] * 60
        self.ul_history: list[float] = [0.0] * 60
        self.peak_dl = 0.0
        self.peak_ul = 0.0
        self.total_dl = 0.0
        self.total_ul = 0.0
        self.frame_count = 0

        # ── Fonts ────────────────────────────────────────────────
        self.font_title    = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.font_speed_xl = tkfont.Font(family="Consolas", size=48, weight="bold")
        self.font_speed_lg = tkfont.Font(family="Consolas", size=28, weight="bold")
        self.font_unit     = tkfont.Font(family="Segoe UI", size=13)
        self.font_label    = tkfont.Font(family="Segoe UI", size=10)
        self.font_small    = tkfont.Font(family="Segoe UI", size=9)
        self.font_tiny     = tkfont.Font(family="Consolas", size=8)

        # ── Build UI ────────────────────────────────────────────
        self._build_ui()

        # ── Start update loop ────────────────────────────────────
        self.root.after(100, self._update_speed)

    # ══════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Main container with padding
        main = tk.Frame(self.root, bg=self.BG_DARK)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Header ───────────────────────────────────────────────
        header = tk.Frame(main, bg=self.BG_DARK)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header, text="⚡ SPEED CHECKER", font=self.font_title,
            fg=self.CYAN_BRIGHT, bg=self.BG_DARK
        ).pack(side="left")

        self.status_label = tk.Label(
            header, text="● LIVE", font=self.font_small,
            fg=self.GREEN_ACCENT, bg=self.BG_DARK
        )
        self.status_label.pack(side="right")

        # Separator line
        sep = tk.Canvas(main, height=2, bg=self.BG_DARK, highlightthickness=0)
        sep.pack(fill="x", pady=(0, 12))
        sep.create_line(0, 1, 2000, 1, fill=self.BORDER_GLOW, width=1)

        # ── Speed Cards Container ────────────────────────────────
        cards = tk.Frame(main, bg=self.BG_DARK)
        cards.pack(fill="x", pady=(0, 10))
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        # Download Card
        self.dl_card = self._create_speed_card(
            cards, "⬇  DOWNLOAD", self.CYAN_BRIGHT, self.CYAN_DIM, 0
        )

        # Upload Card
        self.ul_card = self._create_speed_card(
            cards, "⬆  UPLOAD", self.MAGENTA, self.MAGENTA_DIM, 1
        )

        # ── Live Graph ───────────────────────────────────────────
        graph_frame = tk.Frame(main, bg=self.BG_CARD, highlightbackground=self.BORDER_DIM,
                               highlightthickness=1)
        graph_frame.pack(fill="both", expand=True, pady=(6, 8))

        graph_header = tk.Frame(graph_frame, bg=self.BG_CARD)
        graph_header.pack(fill="x", padx=12, pady=(8, 2))

        tk.Label(
            graph_header, text="BANDWIDTH GRAPH", font=self.font_small,
            fg=self.TEXT_SECONDARY, bg=self.BG_CARD
        ).pack(side="left")

        self.graph_max_label = tk.Label(
            graph_header, text="max: 0 Mbps", font=self.font_tiny,
            fg=self.TEXT_DIM, bg=self.BG_CARD
        )
        self.graph_max_label.pack(side="right")

        self.graph_canvas = tk.Canvas(
            graph_frame, bg=self.BG_CARD, highlightthickness=0, height=130
        )
        self.graph_canvas.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        # ── Stats Bar ────────────────────────────────────────────
        stats = tk.Frame(main, bg=self.BG_CARD, highlightbackground=self.BORDER_DIM,
                         highlightthickness=1)
        stats.pack(fill="x", pady=(0, 4))

        stats_inner = tk.Frame(stats, bg=self.BG_CARD)
        stats_inner.pack(fill="x", padx=12, pady=10)
        for i in range(4):
            stats_inner.columnconfigure(i, weight=1)

        self.stat_peak_dl = self._create_stat(stats_inner, "PEAK ↓", self.CYAN_DIM, 0)
        self.stat_peak_ul = self._create_stat(stats_inner, "PEAK ↑", self.MAGENTA_DIM, 1)
        self.stat_total_dl = self._create_stat(stats_inner, "TOTAL ↓", self.TEXT_DIM, 2)
        self.stat_total_ul = self._create_stat(stats_inner, "TOTAL ↑", self.TEXT_DIM, 3)

        # ── Footer ───────────────────────────────────────────────
        tk.Label(
            main, text="monitoring all network interfaces", font=self.font_tiny,
            fg=self.TEXT_DIM, bg=self.BG_DARK
        ).pack(pady=(4, 0))

    def _create_speed_card(self, parent, title, accent, accent_dim, col):
        """Create a speed display card (download or upload)."""
        card = tk.Frame(
            parent, bg=self.BG_CARD,
            highlightbackground=self.BORDER_DIM, highlightthickness=1
        )
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 4, 4 if col == 0 else 0), pady=0)

        inner = tk.Frame(card, bg=self.BG_CARD)
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Title
        tk.Label(
            inner, text=title, font=self.font_small,
            fg=accent_dim, bg=self.BG_CARD, anchor="w"
        ).pack(fill="x")

        # Speed value (BIG)
        speed_var = tk.StringVar(value="0.00")
        speed_label = tk.Label(
            inner, textvariable=speed_var, font=self.font_speed_lg,
            fg=accent, bg=self.BG_CARD, anchor="w"
        )
        speed_label.pack(fill="x", pady=(2, 0))

        # Unit
        unit_var = tk.StringVar(value="Mbps")
        tk.Label(
            inner, textvariable=unit_var, font=self.font_unit,
            fg=self.TEXT_SECONDARY, bg=self.BG_CARD, anchor="w"
        ).pack(fill="x")

        # Bar indicator
        bar_canvas = tk.Canvas(inner, height=4, bg=self.BG_DARK, highlightthickness=0)
        bar_canvas.pack(fill="x", pady=(8, 0))

        return {
            "frame": card,
            "speed_var": speed_var,
            "unit_var": unit_var,
            "speed_label": speed_label,
            "bar_canvas": bar_canvas,
            "accent": accent,
            "accent_dim": accent_dim,
        }

    def _create_stat(self, parent, title, color, col):
        """Create a small stat widget."""
        frame = tk.Frame(parent, bg=self.BG_CARD)
        frame.grid(row=0, column=col, sticky="nsew")

        tk.Label(
            frame, text=title, font=self.font_tiny,
            fg=self.TEXT_DIM, bg=self.BG_CARD
        ).pack()

        var = tk.StringVar(value="0.00")
        tk.Label(
            frame, textvariable=var, font=self.font_label,
            fg=color, bg=self.BG_CARD
        ).pack()

        return var

    # ══════════════════════════════════════════════════════════════
    #  SPEED MEASUREMENT & UPDATE
    # ══════════════════════════════════════════════════════════════

    def _format_speed(self, bytes_per_sec: float) -> tuple[str, str]:
        """Convert bytes/s to human-readable speed with appropriate unit."""
        bits = bytes_per_sec * 8
        if bits >= 1_000_000_000:
            return f"{bits / 1_000_000_000:.2f}", "Gbps"
        elif bits >= 1_000_000:
            return f"{bits / 1_000_000:.2f}", "Mbps"
        elif bits >= 1_000:
            return f"{bits / 1_000:.1f}", "Kbps"
        else:
            return f"{bits:.0f}", "bps"

    def _format_bytes(self, total_bytes: float) -> str:
        """Format total bytes transferred."""
        if total_bytes >= 1_073_741_824:
            return f"{total_bytes / 1_073_741_824:.2f} GB"
        elif total_bytes >= 1_048_576:
            return f"{total_bytes / 1_048_576:.1f} MB"
        elif total_bytes >= 1024:
            return f"{total_bytes / 1024:.0f} KB"
        return f"{total_bytes:.0f} B"

    def _update_speed(self):
        """Main update loop — runs every 1 second."""
        now = time.time()
        current_net = psutil.net_io_counters()

        dt = now - self.prev_time
        if dt <= 0:
            dt = 1.0

        dl_bytes = (current_net.bytes_recv - self.prev_net.bytes_recv) / dt
        ul_bytes = (current_net.bytes_sent - self.prev_net.bytes_sent) / dt

        self.prev_net = current_net
        self.prev_time = now

        # Convert to Mbps for history
        dl_mbps = (dl_bytes * 8) / 1_000_000
        ul_mbps = (ul_bytes * 8) / 1_000_000

        # Update history
        self.dl_history.append(dl_mbps)
        self.dl_history.pop(0)
        self.ul_history.append(ul_mbps)
        self.ul_history.pop(0)

        # Track peaks
        self.peak_dl = max(self.peak_dl, dl_mbps)
        self.peak_ul = max(self.peak_ul, ul_mbps)

        # Track totals
        self.total_dl += dl_bytes * dt
        self.total_ul += ul_bytes * dt

        # ── Update Download Card ─────────────────────────────────
        dl_val, dl_unit = self._format_speed(dl_bytes)
        self.dl_card["speed_var"].set(dl_val)
        self.dl_card["unit_var"].set(dl_unit)
        self._update_bar(self.dl_card, dl_mbps, self.peak_dl)

        # Pulse color based on activity
        if dl_mbps > 1:
            self.dl_card["speed_label"].configure(fg=self.CYAN_BRIGHT)
        elif dl_mbps > 0.1:
            self.dl_card["speed_label"].configure(fg=self.CYAN_GLOW)
        else:
            self.dl_card["speed_label"].configure(fg=self.CYAN_DIM)

        # ── Update Upload Card ───────────────────────────────────
        ul_val, ul_unit = self._format_speed(ul_bytes)
        self.ul_card["speed_var"].set(ul_val)
        self.ul_card["unit_var"].set(ul_unit)
        self._update_bar(self.ul_card, ul_mbps, self.peak_ul)

        if ul_mbps > 1:
            self.ul_card["speed_label"].configure(fg=self.MAGENTA)
        elif ul_mbps > 0.1:
            self.ul_card["speed_label"].configure(fg=self.MAGENTA_GLOW)
        else:
            self.ul_card["speed_label"].configure(fg=self.MAGENTA_DIM)

        # ── Update Stats ─────────────────────────────────────────
        self.stat_peak_dl.set(f"{self.peak_dl:.2f} Mbps")
        self.stat_peak_ul.set(f"{self.peak_ul:.2f} Mbps")
        self.stat_total_dl.set(self._format_bytes(self.total_dl))
        self.stat_total_ul.set(self._format_bytes(self.total_ul))

        # ── Update Graph ─────────────────────────────────────────
        self._draw_graph()

        # ── Blink live indicator ─────────────────────────────────
        self.frame_count += 1
        if self.frame_count % 2 == 0:
            self.status_label.configure(fg=self.GREEN_ACCENT)
        else:
            self.status_label.configure(fg="#006644")

        # Schedule next update (1 second)
        self.root.after(1000, self._update_speed)

    def _update_bar(self, card: dict, current_mbps: float, peak_mbps: float):
        """Update the speed bar indicator."""
        canvas = card["bar_canvas"]
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1:
            w = 200

        ratio = min(current_mbps / max(peak_mbps, 1), 1.0)
        bar_w = max(int(w * ratio), 2)

        # Background
        canvas.create_rectangle(0, 0, w, 4, fill=self.BG_DARK, outline="")
        # Active bar
        canvas.create_rectangle(0, 0, bar_w, 4, fill=card["accent"], outline="")

    def _draw_graph(self):
        """Draw the live bandwidth graph."""
        canvas = self.graph_canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        padding = 4
        graph_w = w - padding * 2
        graph_h = h - padding * 2

        all_vals = self.dl_history + self.ul_history
        max_val = max(max(all_vals), 0.1)

        self.graph_max_label.configure(text=f"max: {max_val:.1f} Mbps")

        # Draw grid lines
        for i in range(5):
            y = padding + (graph_h * i) / 4
            canvas.create_line(
                padding, y, w - padding, y,
                fill=self.BORDER_DIM, width=1, dash=(2, 4)
            )

        n = len(self.dl_history)
        step = graph_w / max(n - 1, 1)

        # ── Draw Upload fill ─────────────────────────────────────
        ul_points = []
        for i, val in enumerate(self.ul_history):
            x = padding + i * step
            y = padding + graph_h - (val / max_val) * graph_h
            ul_points.append((x, y))

        if len(ul_points) >= 2:
            fill_pts = (
                [(padding, padding + graph_h)]
                + ul_points
                + [(padding + (n - 1) * step, padding + graph_h)]
            )
            flat = [coord for pt in fill_pts for coord in pt]
            canvas.create_polygon(flat, fill="#1a0020", outline="", smooth=True)

            line_pts = [coord for pt in ul_points for coord in pt]
            canvas.create_line(line_pts, fill=self.MAGENTA_DIM, width=1.5, smooth=True)

        # ── Draw Download fill ───────────────────────────────────
        dl_points = []
        for i, val in enumerate(self.dl_history):
            x = padding + i * step
            y = padding + graph_h - (val / max_val) * graph_h
            dl_points.append((x, y))

        if len(dl_points) >= 2:
            fill_pts = (
                [(padding, padding + graph_h)]
                + dl_points
                + [(padding + (n - 1) * step, padding + graph_h)]
            )
            flat = [coord for pt in fill_pts for coord in pt]
            canvas.create_polygon(flat, fill="#001520", outline="", smooth=True)

            line_pts = [coord for pt in dl_points for coord in pt]
            canvas.create_line(line_pts, fill=self.CYAN_GLOW, width=2, smooth=True)

        # ── Draw current value dots ──────────────────────────────
        if dl_points:
            lx, ly = dl_points[-1]
            canvas.create_oval(lx - 4, ly - 4, lx + 4, ly + 4,
                               fill=self.CYAN_BRIGHT, outline="")
        if ul_points:
            lx, ly = ul_points[-1]
            canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3,
                               fill=self.MAGENTA, outline="")

        # Legend
        canvas.create_rectangle(w - 120, 6, w - 108, 14, fill=self.CYAN_BRIGHT, outline="")
        canvas.create_text(w - 104, 10, text="Download", anchor="w",
                           fill=self.TEXT_DIM, font=self.font_tiny)
        canvas.create_rectangle(w - 120, 20, w - 108, 28, fill=self.MAGENTA, outline="")
        canvas.create_text(w - 104, 24, text="Upload", anchor="w",
                           fill=self.TEXT_DIM, font=self.font_tiny)


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    # Resolve icon path relative to script location
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    icon_path = os.path.join(script_dir, "icon.ico")

    # Set app icon (Window title bar + taskbar)
    try:
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception:
        pass

    # Dark title bar on Windows 10/11
    try:
        from ctypes import windll, c_int, byref, sizeof
        HWND = windll.user32.GetParent(root.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        windll.dwmapi.DwmSetWindowAttribute(
            HWND, DWMWA_USE_IMMERSIVE_DARK_MODE,
            byref(c_int(1)), sizeof(c_int)
        )
    except Exception:
        pass

    app = SpeedMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
