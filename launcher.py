"""
╔══════════════════════════════════════════════════╗
║     ALL PYTHON APPS — Premium App Launcher       ║
║     Launch any of your 20 Python apps instantly   ║
╚══════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import threading
import math

# ─── Resolve base path (where this script lives) ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Premium Dark Theme ───
C = {
    "bg":       "#08080f",
    "bg2":      "#0e0e1a",
    "card":     "#14142a",
    "card_hov": "#1c1c3a",
    "border":   "#252545",
    "accent":   "#6c5ce7",
    "accent2":  "#a29bfe",
    "success":  "#00cec9",
    "pink":     "#fd79a8",
    "orange":   "#fdcb6e",
    "red":      "#ff7675",
    "cyan":     "#74b9ff",
    "green":    "#55efc4",
    "yellow":   "#ffeaa7",
    "text":     "#dfe6e9",
    "text2":    "#b2bec3",
    "dim":      "#636e72",
}

# ─── App Registry ───
APPS = [
    {
        "name": "Speed Checker",
        "icon": "🚀", "color": "#00cec9",
        "desc": "Real-time internet speed monitor",
        "folder": "01_Speed_Checker", "script": "main.py",
    },
    {
        "name": "Task Manager",
        "icon": "🖥️", "color": "#6c5ce7",
        "desc": "Process monitor & controller",
        "folder": "02_Task_Manager", "script": "main.py",
    },
    {
        "name": "YouTube Downloader",
        "icon": "▶", "color": "#ff7675",
        "desc": "YTDROP PRO — 4K/1080p/MP3",
        "folder": "03_YouTube_Downloader", "script": "youtube_downloader.py",
    },
    {
        "name": "Attendance Scraper",
        "icon": "📊", "color": "#fdcb6e",
        "desc": "Automated data extractor",
        "folder": "04_Attendance_Scraper", "script": "attendance_scraper.py",
    },
    {
        "name": "Document Converter",
        "icon": "📄", "color": "#74b9ff",
        "desc": "Offline file format converter",
        "folder": "05_Document_Converter", "script": "app.py",
    },
    {
        "name": "Image AI Analyzer",
        "icon": "🧠", "color": "#a29bfe",
        "desc": "VisionMind — offline analysis",
        "folder": "06_Image_AI_Analyzer", "script": "image_ai_app.py",
    },
    {
        "name": "Mini Python IDE",
        "icon": "💻", "color": "#55efc4",
        "desc": "Code editor + autocomplete",
        "folder": "07_Mini_Python_IDE", "script": "my_ide.py",
    },
    {
        "name": "Web Scraper",
        "icon": "🕷️", "color": "#fd79a8",
        "desc": "Visual web data extractor",
        "folder": "08_Web_Scraper", "script": "web_scraper.py",
    },
    {
        "name": "Advanced Scraper",
        "icon": "🌐", "color": "#00b894",
        "desc": "JS-rendered page scraper",
        "folder": "09_Advanced_Web_Scraper", "script": "advanced_scrape.py",
    },
    {
        "name": "WiFi & BLE Scanner",
        "icon": "📡", "color": "#0984e3",
        "desc": "Network & Bluetooth discovery",
        "folder": "10_WiFi_BLE_Scanner", "script": "scanner.py",
    },
    {
        "name": "App Shortcut Maker",
        "icon": "🔗", "color": "#e17055",
        "desc": "Windows shortcut creator",
        "folder": "11_App_Shortcut_Maker", "script": "app_maker.py",
    },
    {
        "name": "Attendance Dashboard",
        "icon": "📈", "color": "#00cec9",
        "desc": "Streamlit data visualizer",
        "folder": "12_Attendance_Dashboard", "script": "dashboard.py",
        "streamlit": True,
    },
    {
        "name": "Command Center",
        "icon": "🎯", "color": "#6c5ce7",
        "desc": "Integrated scraper + dashboard",
        "folder": "13_Attendance_Command_Center", "script": "command_center.py",
        "streamlit": True,
    },
    {
        "name": "TurboFTP Client",
        "icon": "🚀", "color": "#74b9ff",
        "desc": "Professional FTP client",
        "folder": "14_TurboFTP_Client", "script": "ftp_client.py",
    },
    {
        "name": "LAN File Share",
        "icon": "📁", "color": "#55efc4",
        "desc": "Premium LAN sharing + chat",
        "folder": "15_LAN_File_Share", "script": "local_lan.py",
    },
    {
        "name": "Screen Recorder",
        "icon": "🎬", "color": "#ff7675",
        "desc": "ScreenForge Pro recorder",
        "folder": "16_Screen_Recorder", "script": "screen_recorder.py",
    },
    {
        "name": "Script Manager",
        "icon": "🐍", "color": "#fdcb6e",
        "desc": "Environment & script runner",
        "folder": "17_Python_Script_Manager", "script": "script_manager.py",
    },
    {
        "name": "Temp File Cleaner",
        "icon": "🧹", "color": "#00b894",
        "desc": "System temp scanner & cleaner",
        "folder": "18_Temp_File_Cleaner", "script": "temp_cleaner.py",
    },
    {
        "name": "Package Scanner",
        "icon": "📦", "color": "#0984e3",
        "desc": "Python environment inspector",
        "folder": "19_Package_Library_Scanner", "script": "package_scanner.py",
    },
    {
        "name": "LAN Device Scanner",
        "icon": "📡", "color": "#e17055",
        "desc": "NetScope — network discovery",
        "folder": "20_LAN_Device_Scanner", "script": "lan_scanner.py",
    },
]


class AppLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ALL Python Apps — Launcher")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])
        self.running = {}  # Track running processes

        self._build_header()
        self._build_body()
        self._build_statusbar()

        # Periodic check for finished processes
        self._check_processes()

    # ── HEADER ──────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=C["bg2"], height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = tk.Frame(hdr, bg=C["bg2"])
        inner.pack(fill="both", expand=True, padx=30)

        # Logo
        tk.Label(inner, text="⚡", font=("Segoe UI Emoji", 28),
                 bg=C["bg2"], fg=C["accent"]).pack(side="left", padx=(0, 10))

        title_frame = tk.Frame(inner, bg=C["bg2"])
        title_frame.pack(side="left")

        tk.Label(title_frame, text="ALL Python Apps",
                 font=("Segoe UI", 22, "bold"),
                 bg=C["bg2"], fg=C["text"]).pack(anchor="w")

        tk.Label(title_frame, text=f"{len(APPS)} applications ready to launch",
                 font=("Segoe UI", 10),
                 bg=C["bg2"], fg=C["dim"]).pack(anchor="w")

        # Search
        search_frame = tk.Frame(inner, bg=C["card"], highlightbackground=C["border"],
                                highlightthickness=1)
        search_frame.pack(side="right", pady=20)

        tk.Label(search_frame, text="🔍", bg=C["card"], fg=C["dim"],
                 font=("Segoe UI Emoji", 12)).pack(side="left", padx=(10, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_apps())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     bg=C["card"], fg=C["text"], insertbackground=C["accent"],
                                     font=("Segoe UI", 11), relief="flat", bd=0, width=25)
        self.search_entry.pack(side="left", padx=(0, 10), pady=8)
        self.search_entry.insert(0, "")
        self.search_entry.bind("<FocusIn>", lambda e: None)

        # Accent line
        tk.Frame(self, bg=C["accent"], height=2).pack(fill="x")

    # ── SCROLLABLE BODY ─────────────────────────────────
    def _build_body(self):
        container = tk.Frame(self, bg=C["bg"])
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview,
                           bg=C["bg2"], troughcolor=C["bg"])
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=C["bg"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind("<Configure>",
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.app_cards = []
        self._render_grid()

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._render_grid()

    # ── RENDER GRID ─────────────────────────────────────
    def _render_grid(self, filter_text=""):
        # Clear existing cards
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.app_cards = []

        # Padding
        pad_frame = tk.Frame(self.grid_frame, bg=C["bg"], height=20)
        pad_frame.pack(fill="x")

        # Filter apps
        query = filter_text.lower().strip()
        filtered = [a for a in APPS if query in a["name"].lower() or query in a["desc"].lower()] \
            if query else APPS

        if not filtered:
            tk.Label(self.grid_frame, text="No apps match your search",
                     font=("Segoe UI", 14), fg=C["dim"], bg=C["bg"]).pack(pady=60)
            return

        # Calculate columns based on window width
        try:
            canvas_w = self.canvas.winfo_width()
        except Exception:
            canvas_w = 1100
        card_width = 240
        cols = max(2, min(5, canvas_w // (card_width + 20)))

        # Create grid rows
        for i, app in enumerate(filtered):
            row_idx = i // cols
            col_idx = i % cols

            if col_idx == 0:
                row_frame = tk.Frame(self.grid_frame, bg=C["bg"])
                row_frame.pack(fill="x", padx=30, pady=6)

            self._create_card(row_frame, app, card_width)

    def _create_card(self, parent, app, width):
        is_running = app["folder"] in self.running

        # Card frame
        card = tk.Frame(parent, bg=C["card"], cursor="hand2",
                        highlightbackground=C["border"], highlightthickness=1,
                        width=width, height=180)
        card.pack(side="left", padx=8, pady=6)
        card.pack_propagate(False)

        inner = tk.Frame(card, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Icon (big)
        icon_frame = tk.Frame(inner, bg=app["color"], width=56, height=56)
        icon_frame.pack(anchor="w", pady=(0, 10))
        icon_frame.pack_propagate(False)

        # Use a colored square with the emoji
        icon_lbl = tk.Label(icon_frame, text=app["icon"],
                            font=("Segoe UI Emoji", 22),
                            bg=app["color"], fg="white")
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # App name
        name_lbl = tk.Label(inner, text=app["name"],
                            font=("Segoe UI", 13, "bold"),
                            bg=C["card"], fg=C["text"], anchor="w")
        name_lbl.pack(anchor="w")

        # Description
        desc_lbl = tk.Label(inner, text=app["desc"],
                            font=("Segoe UI", 9),
                            bg=C["card"], fg=C["dim"], anchor="w")
        desc_lbl.pack(anchor="w", pady=(2, 0))

        # Status indicator
        if is_running:
            status_lbl = tk.Label(inner, text="● Running",
                                  font=("Segoe UI", 8, "bold"),
                                  bg=C["card"], fg=C["green"])
            status_lbl.pack(anchor="w", pady=(6, 0))

        # Hover effects
        all_widgets = [card, inner, icon_frame, icon_lbl, name_lbl, desc_lbl]

        def on_enter(e):
            card.configure(bg=C["card_hov"], highlightbackground=app["color"])
            for w in [inner, name_lbl, desc_lbl]:
                try:
                    w.configure(bg=C["card_hov"])
                except Exception:
                    pass

        def on_leave(e):
            card.configure(bg=C["card"], highlightbackground=C["border"])
            for w in [inner, name_lbl, desc_lbl]:
                try:
                    w.configure(bg=C["card"])
                except Exception:
                    pass

        def on_click(e):
            self._launch_app(app)

        for w in all_widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        self.app_cards.append(card)

    # ── LAUNCH APP ──────────────────────────────────────
    def _launch_app(self, app):
        folder = os.path.join(BASE_DIR, app["folder"])
        script = os.path.join(folder, app["script"])

        if not os.path.isfile(script):
            messagebox.showerror("File Not Found",
                                 f"Could not find:\n{script}\n\nMake sure the file exists.")
            return

        if app["folder"] in self.running:
            messagebox.showinfo("Already Running",
                                f"{app['name']} is already running!\n"
                                f"PID: {self.running[app['folder']].pid}")
            return

        self.status_var.set(f"⚡ Launching {app['name']}...")
        self.update_idletasks()

        def launch():
            try:
                # For Streamlit apps, use streamlit run
                if app.get("streamlit"):
                    cmd = [sys.executable, "-m", "streamlit", "run", script]
                else:
                    cmd = [sys.executable, script]

                cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                proc = subprocess.Popen(cmd, cwd=folder, creationflags=cf)
                self.running[app["folder"]] = proc

                self.after(0, lambda: self.status_var.set(
                    f"✅ {app['name']} launched (PID: {proc.pid})"))
                self.after(0, lambda: self._filter_apps())  # Refresh to show "Running"
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Launch Error", f"Failed to launch {app['name']}:\n{e}"))
                self.after(0, lambda: self.status_var.set("❌ Launch failed"))

        threading.Thread(target=launch, daemon=True).start()

    # ── FILTER ──────────────────────────────────────────
    def _filter_apps(self):
        self._render_grid(self.search_var.get())

    # ── STATUS BAR ──────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C["bg2"], height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=C["bg2"])
        inner.pack(fill="both", expand=True, padx=20)

        self.status_var = tk.StringVar(value="Ready — Click any app to launch")
        tk.Label(inner, textvariable=self.status_var,
                 font=("Segoe UI", 9), bg=C["bg2"], fg=C["dim"]).pack(side="left")

        self.running_count_var = tk.StringVar(value="0 running")
        tk.Label(inner, textvariable=self.running_count_var,
                 font=("Segoe UI", 9, "bold"), bg=C["bg2"], fg=C["accent"]).pack(side="right")

    # ── PROCESS CHECKER ─────────────────────────────────
    def _check_processes(self):
        finished = []
        for folder, proc in self.running.items():
            if proc.poll() is not None:
                finished.append(folder)

        for folder in finished:
            del self.running[folder]

        if finished:
            self._filter_apps()

        count = len(self.running)
        self.running_count_var.set(f"{count} running" if count else "0 running")

        self.after(2000, self._check_processes)


if __name__ == "__main__":
    app = AppLauncher()
    # Center on screen
    app.update_idletasks()
    x = (app.winfo_screenwidth() - 1100) // 2
    y = (app.winfo_screenheight() - 750) // 2
    app.geometry(f"1100x750+{x}+{y}")
    app.mainloop()
