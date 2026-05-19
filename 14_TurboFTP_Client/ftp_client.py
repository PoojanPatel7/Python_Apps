"""
TurboFTP - Professional Windows FTP Client
A full-featured, high-performance FTP desktop app using Python + tkinter.

Features:
- Premium Modern Dark UI (VS Code / Catppuccin inspired)
- Quick Connect with "Enter to Connect" binding
- Fast directory loading & batch rendering
- Live transfer speeds (MB/s) & Tabbed Logging
- Right-click context menus & Double-click transfers
- Anti-timeout keep-alive
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Menu
import ftplib
import os
import threading
import queue
import time
import json
import base64
from pathlib import Path

# ─────────────────────────────────────────────
#  CONSTANTS & COLORS (Premium Dark Theme)
# ─────────────────────────────────────────────
APP_TITLE   = "TurboFTP Professional"
APP_W, APP_H = 1200, 760

FONT_MAIN   = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_MONO   = ("Consolas", 9)

# Color Palette
C_BG        = "#181825" # Deep background
C_PANEL     = "#1e1e2e" # Lighter panel background
C_SURFACE   = "#313244" # Surface elements (inputs, headers)
C_BORDER    = "#45475a" # Borders and dividers
C_ACCENT    = "#89b4fa" # Primary Accent (Blue)
C_ACCENT_H  = "#b4befe" # Accent Hover
C_SUCCESS   = "#a6e3a1" # Green
C_ERROR     = "#f38ba8" # Red
C_WARN      = "#f9e2af" # Yellow
C_TEXT      = "#cdd6f4" # Primary Text
C_MUTED     = "#a6adc8" # Secondary Text
C_SEL       = "#585b70" # Selection background

CONFIG_FILE = "turboftp_config.json"


# ─────────────────────────────────────────────
#  FTP WORKER (Background Operations)
# ─────────────────────────────────────────────
class FTPWorker:
    def __init__(self, log_callback):
        self.ftp = None
        self.connected = False
        self.log = log_callback
        self.current_dir = "/"
        self.keep_alive_thread = None

    def connect(self, host, port, user, password, passive=True):
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(host, int(port), timeout=10)
            self.ftp.login(user, password)
            if passive:
                self.ftp.set_pasv(True)
            self.connected = True
            self.current_dir = self.ftp.pwd()
            self.log(f"✅ Connected to {host}:{port} as '{user}'", "success")
            self.log(f"ℹ️ Server: {self.ftp.getwelcome()}", "info")
            
            # Start Keep-Alive
            self.keep_alive_thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
            self.keep_alive_thread.start()
            return True
        except Exception as e:
            self.log(f"❌ Connection failed: {e}", "error")
            self.connected = False
            return False

    def _keep_alive_loop(self):
        while self.connected and self.ftp:
            time.sleep(30) # Ping every 30 seconds
            try:
                self.ftp.voidcmd("NOOP")
            except Exception:
                self.connected = False
                break

    def disconnect(self):
        if self.ftp and self.connected:
            try:
                self.ftp.quit()
            except Exception:
                pass
        self.connected = False
        self.ftp = None
        self.log("🔌 Disconnected from server.", "info")

    def list_dir(self, path=None):
        if not self.connected: return []
        try:
            target = path or self.current_dir
            items = []
            self.ftp.cwd(target)
            self.current_dir = self.ftp.pwd()

            raw_lines = []
            self.ftp.retrlines("LIST", raw_lines.append)

            for line in raw_lines:
                parts = line.split()
                if not parts: continue
                is_dir = line.startswith("d")
                name = " ".join(parts[8:]) if len(parts) >= 9 else parts[-1]
                if name in (".", ".."): continue
                
                size = parts[4] if len(parts) >= 5 else "0"
                date = " ".join(parts[5:8]) if len(parts) >= 8 else ""
                perms = parts[0] if parts else ""
                items.append({
                    "name": name, "is_dir": is_dir,
                    "size": int(size) if size.isdigit() else 0,
                    "date": date, "perms": perms,
                })
            return items
        except Exception as e:
            self.log(f"❌ Failed to retrieve directory list: {e}", "error")
            return []

    def download_file(self, remote_path, local_path, progress_cb=None):
        try:
            size = self.ftp.size(remote_path)
            downloaded = [0]
            start_time = time.time()
            
            def write_chunk(data):
                f.write(data)
                downloaded[0] += len(data)
                if progress_cb and size:
                    elapsed = time.time() - start_time
                    speed = (downloaded[0] / elapsed) if elapsed > 0 else 0
                    progress_cb(downloaded[0], size, speed)

            with open(local_path, "wb") as f:
                self.ftp.retrbinary(f"RETR {remote_path}", write_chunk, blocksize=8192)

            self.log(f"📥 Downloaded: {os.path.basename(remote_path)}", "success")
            return True
        except Exception as e:
            self.log(f"❌ Download failed: {e}", "error")
            return False

    def upload_file(self, local_path, remote_path, progress_cb=None):
        try:
            size = os.path.getsize(local_path)
            uploaded = [0]
            start_time = time.time()

            def read_chunk(data):
                uploaded[0] += len(data)
                if progress_cb and size:
                    elapsed = time.time() - start_time
                    speed = (uploaded[0] / elapsed) if elapsed > 0 else 0
                    progress_cb(uploaded[0], size, speed)
                return data

            with open(local_path, "rb") as f:
                self.ftp.storbinary(f"STOR {remote_path}", f, blocksize=8192,
                                    callback=lambda d: read_chunk(d))
            self.log(f"📤 Uploaded: {os.path.basename(local_path)}", "success")
            return True
        except Exception as e:
            self.log(f"❌ Upload failed: {e}", "error")
            return False

    def execute_cmd(self, cmd_func, success_msg, error_msg):
        try:
            cmd_func()
            self.log(success_msg, "success")
            return True
        except Exception as e:
            self.log(f"{error_msg}: {e}", "error")
            return False


# ─────────────────────────────────────────────
#  MAIN APPLICATION GUI
# ─────────────────────────────────────────────
class FTPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_W}x{APP_H}")
        self.minsize(1000, 650)
        self.configure(bg=C_BG)

        # Variables
        self.ftp_worker = FTPWorker(log_callback=self.log)
        self.task_queue  = queue.Queue()
        self.config = {"recent": [], "last_local": str(Path.home())}
        
        self.local_path  = tk.StringVar()
        self.remote_path = tk.StringVar(value="/")
        self.status_text = tk.StringVar(value="Ready - Not connected")
        self.progress_var = tk.DoubleVar(value=0)
        
        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar(value="21")
        self.user_var = tk.StringVar(value="anonymous")
        self.pass_var = tk.StringVar()
        self.passive_var = tk.BooleanVar(value=True)

        self._load_config()
        self._setup_styles()
        self._build_ui()
        self._build_context_menus()
        
        self.local_path.set(self.config.get("last_local", str(Path.home())))
        self._refresh_local()
        self.after(100, self._process_queue)

    # ── CONFIGURATION ────────────────────────
    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
        except Exception:
            pass

    def _save_config(self):
        self.config["last_local"] = self.local_path.get()
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.log(f"Failed to save config: {e}", "error")

    def _add_to_recent(self):
        entry = {
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "user": self.user_var.get(),
            "pass": base64.b64encode(self.pass_var.get().encode()).decode(), # Basic obfuscation
            "passive": self.passive_var.get()
        }
        # Remove duplicates
        self.config["recent"] = [r for r in self.config.get("recent", []) if r["host"] != entry["host"]]
        self.config["recent"].insert(0, entry)
        self.config["recent"] = self.config["recent"][:10] # Keep last 10
        self._save_config()
        self._update_recent_dropdown()

    # ── UI STYLING ──────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # General Frame/Label
        style.configure("TFrame", background=C_PANEL)
        style.configure("TLabel", background=C_PANEL, foreground=C_TEXT, font=FONT_MAIN)
        style.configure("Header.TLabel", font=FONT_TITLE, foreground=C_ACCENT, background=C_BG)
        
        # Treeview styling
        style.configure("Treeview", 
                        background=C_PANEL, 
                        foreground=C_TEXT,
                        fieldbackground=C_PANEL, 
                        rowheight=28, 
                        font=FONT_MAIN, 
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background=C_SURFACE, 
                        foreground=C_TEXT,
                        font=FONT_BOLD, 
                        borderwidth=0, 
                        relief="flat", 
                        padding=6)
        style.map("Treeview", 
                  background=[("selected", C_SEL)], 
                  foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", 
                  background=[("active", C_BORDER)],
                  foreground=[("active", "#ffffff")])
        
        # Scrollbar
        style.configure("Vertical.TScrollbar", 
                        background=C_SURFACE, 
                        troughcolor=C_PANEL,
                        arrowcolor=C_MUTED, 
                        borderwidth=0,
                        relief="flat")
        style.map("Vertical.TScrollbar", background=[("active", C_BORDER)])
        
        # Notebook (Tabs)
        style.configure("TNotebook", background=C_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=C_SURFACE, foreground=C_MUTED, padding=[15, 5], font=FONT_BOLD, borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", C_PANEL)], foreground=[("selected", C_ACCENT)])

        # Combobox
        style.map("TCombobox", 
                  fieldbackground=[("readonly", C_SURFACE)], 
                  selectbackground=[("readonly", C_SURFACE)], 
                  selectforeground=[("readonly", C_TEXT)])

        # Progressbar
        style.configure("Blue.Horizontal.TProgressbar", troughcolor=C_SURFACE, background=C_ACCENT, borderwidth=0, thickness=6)

    # ── UI BUILDER ──────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_quick_connect()
        self._build_main_split()
        self._build_bottom_panel()
        self._build_statusbar()

    def _build_header(self):
        header_frame = tk.Frame(self, bg=C_BG, height=50)
        header_frame.pack(fill="x", side="top", padx=15, pady=(10, 5))
        
        # Logo and Title
        tk.Label(header_frame, text="🚀", bg=C_BG, fg=C_ACCENT, font=("Segoe UI Emoji", 18)).pack(side="left", padx=(0, 5))
        tk.Label(header_frame, text="TurboFTP", bg=C_BG, fg=C_TEXT, font=("Segoe UI", 16, "bold")).pack(side="left")
        tk.Label(header_frame, text="Professional", bg=C_BG, fg=C_ACCENT, font=("Segoe UI", 16)).pack(side="left", padx=(5, 0))

        # Main Global Actions
        btn_cfg = [
            ("⚙ Settings", lambda: messagebox.showinfo("Settings", "Settings coming soon!"), C_SURFACE, C_TEXT),
            ("🔄 Refresh All", self._refresh_all, C_SURFACE, C_TEXT)
        ]
        for text, cmd, bg, fg in btn_cfg:
            b = tk.Button(header_frame, text=text, command=cmd, font=FONT_BOLD, bg=bg, fg=fg,
                          relief="flat", padx=15, pady=6, cursor="hand2", bd=0,
                          activebackground=C_BORDER, activeforeground="#fff")
            b.pack(side="right", padx=5)

    def _build_quick_connect(self):
        # Quick Connect Bar
        qc_frame = tk.Frame(self, bg=C_PANEL, bd=1, relief="flat")
        qc_frame.pack(fill="x", padx=15, pady=5)
        
        # Inner padding frame
        inner = tk.Frame(qc_frame, bg=C_PANEL)
        inner.pack(fill="x", padx=10, pady=10)

        # Profile Selector
        tk.Label(inner, text="⭐ Profile:", bg=C_PANEL, fg=C_MUTED, font=FONT_BOLD).pack(side="left", padx=(0, 5))
        self.recent_combo = ttk.Combobox(inner, state="readonly", width=18, font=FONT_MAIN)
        self.recent_combo.pack(side="left", padx=(0, 20))
        self.recent_combo.bind("<<ComboboxSelected>>", self._on_recent_selected)
        
        # Connection Fields
        fields = [
            ("🌐 Host", "host_var", 25), 
            ("👤 User", "user_var", 15), 
            ("🔑 Pass", "pass_var", 15),
            ("🔌 Port", "port_var", 6)
        ]
        
        for label, var_name, width in fields:
            tk.Label(inner, text=label, bg=C_PANEL, fg=C_MUTED, font=FONT_MAIN).pack(side="left", padx=(5, 2))
            e = tk.Entry(inner, textvariable=getattr(self, var_name), width=width, bg=C_SURFACE, fg=C_TEXT,
                         insertbackground=C_TEXT, relief="flat", font=FONT_MAIN, bd=6)
            if var_name == "pass_var": 
                e.config(show="●")
            e.pack(side="left", padx=(0, 10))
            
            # BIND ENTER KEY TO CONNECT
            e.bind("<Return>", lambda event: self._toggle_connect())

        # Passive Mode
        tk.Checkbutton(inner, text="PASV", variable=self.passive_var, bg=C_PANEL, fg=C_MUTED,
                       selectcolor=C_SURFACE, activebackground=C_PANEL, font=FONT_MAIN).pack(side="left", padx=(5, 15))

        # Connect Button
        self.connect_btn = tk.Button(inner, text="⚡ Quick Connect", command=self._toggle_connect, 
                                     bg=C_ACCENT, fg="#000", font=FONT_BOLD, relief="flat", 
                                     padx=20, pady=5, cursor="hand2", bd=0, activebackground=C_ACCENT_H)
        self.connect_btn.pack(side="right")
        
        self._update_recent_dropdown()

    def _update_recent_dropdown(self):
        recents = self.config.get("recent", [])
        values = [f"{r['user']}@{r['host']}" for r in recents]
        self.recent_combo['values'] = values
        if values:
            self.recent_combo.set(values[0])
            self._on_recent_selected(None, index=0)

    def _on_recent_selected(self, event, index=None):
        idx = self.recent_combo.current() if index is None else index
        if idx < 0: return
        recents = self.config.get("recent", [])
        if idx < len(recents):
            r = recents[idx]
            self.host_var.set(r.get("host", ""))
            self.port_var.set(r.get("port", "21"))
            self.user_var.set(r.get("user", ""))
            try:
                decoded_pass = base64.b64decode(r.get("pass", "")).decode()
            except:
                decoded_pass = ""
            self.pass_var.set(decoded_pass)
            self.passive_var.set(r.get("passive", True))

    def _build_main_split(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=C_BG, sashwidth=8, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=15, pady=5)

        # ─── LOCAL BROWSER ───
        local_frame = tk.Frame(paned, bg=C_PANEL)
        paned.add(local_frame, minsize=400)
        
        # Local Navigation Bar
        l_nav = tk.Frame(local_frame, bg=C_SURFACE, pady=6, padx=6)
        l_nav.pack(fill="x", side="top")
        tk.Label(l_nav, text="💻 Local:", bg=C_SURFACE, fg=C_ACCENT, font=FONT_BOLD).pack(side="left", padx=5)
        
        self._create_icon_btn(l_nav, "🏠", self._go_local_home).pack(side="left", padx=2)
        self._create_icon_btn(l_nav, "⤴", self._go_local_up).pack(side="left", padx=2)
        
        le = tk.Entry(l_nav, textvariable=self.local_path, bg=C_PANEL, fg=C_TEXT, relief="flat", font=FONT_MAIN, bd=6, insertbackground=C_TEXT)
        le.pack(side="left", fill="x", expand=True, padx=5)
        le.bind("<Return>", lambda e: self._refresh_local())
        
        tk.Button(l_nav, text="Browse", command=self._browse_local, bg=C_BORDER, fg=C_TEXT, relief="flat", cursor="hand2", bd=0, padx=10, font=FONT_BOLD).pack(side="left", padx=2)

        # Local Treeview
        cols = ("Name", "Size", "Type")
        self.local_tree = ttk.Treeview(local_frame, columns=cols, show="headings", selectmode="extended")
        self._style_tree(self.local_tree, cols, [220, 80, 80])
        self.local_tree.bind("<Double-1>", self._local_double_click)
        self.local_tree.bind("<Button-3>", self._show_local_menu)

        vsb_l = ttk.Scrollbar(local_frame, orient="vertical", command=self.local_tree.yview)
        self.local_tree.configure(yscrollcommand=vsb_l.set)
        self.local_tree.pack(side="left", fill="both", expand=True)
        vsb_l.pack(side="right", fill="y")


        # ─── REMOTE BROWSER ───
        remote_frame = tk.Frame(paned, bg=C_PANEL)
        paned.add(remote_frame, minsize=400)

        # Remote Navigation Bar
        r_nav = tk.Frame(remote_frame, bg=C_SURFACE, pady=6, padx=6)
        r_nav.pack(fill="x", side="top")
        tk.Label(r_nav, text="🌐 Remote:", bg=C_SURFACE, fg=C_ACCENT, font=FONT_BOLD).pack(side="left", padx=5)
        
        self._create_icon_btn(r_nav, "🏠", lambda: self._navigate_to("/")).pack(side="left", padx=2)
        self._create_icon_btn(r_nav, "⤴", self._go_remote_up).pack(side="left", padx=2)

        rpe = tk.Entry(r_nav, textvariable=self.remote_path, bg=C_PANEL, fg=C_TEXT, relief="flat", font=FONT_MAIN, bd=6, insertbackground=C_TEXT)
        rpe.pack(side="left", fill="x", expand=True, padx=5)
        rpe.bind("<Return>", lambda e: self._navigate_remote())
        
        tk.Button(r_nav, text="Go ▶", command=self._navigate_remote, bg=C_BORDER, fg=C_TEXT, relief="flat", cursor="hand2", bd=0, padx=10, font=FONT_BOLD).pack(side="left", padx=2)

        # Remote Treeview
        cols2 = ("Name", "Size", "Date", "Perms")
        self.remote_tree = ttk.Treeview(remote_frame, columns=cols2, show="headings", selectmode="extended")
        self._style_tree(self.remote_tree, cols2, [220, 80, 120, 70])
        self.remote_tree.bind("<Double-1>", self._remote_double_click)
        self.remote_tree.bind("<Button-3>", self._show_remote_menu)

        vsb_r = ttk.Scrollbar(remote_frame, orient="vertical", command=self.remote_tree.yview)
        self.remote_tree.configure(yscrollcommand=vsb_r.set)
        self.remote_tree.pack(side="left", fill="both", expand=True)
        vsb_r.pack(side="right", fill="y")

    def _create_icon_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=C_PANEL, fg=C_TEXT, 
                         relief="flat", cursor="hand2", bd=0, font=("Segoe UI Emoji", 10), 
                         padx=8, pady=2, activebackground=C_BORDER, activeforeground="#fff")

    def _style_tree(self, tree, cols, widths):
        for col, w in zip(cols, widths):
            tree.heading(col, text=col, command=lambda c=col, t=tree: self._sort_tree(t, c, False))
            tree.column(col, width=w, minwidth=50)

    def _build_bottom_panel(self):
        # Tabbed interface for Logs and Queue
        bottom_frame = tk.Frame(self, bg=C_BG, height=180)
        bottom_frame.pack(fill="x", side="bottom", padx=15, pady=(5, 5))
        bottom_frame.pack_propagate(False)
        
        self.notebook = ttk.Notebook(bottom_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # -- Log Tab --
        log_tab = tk.Frame(self.notebook, bg=C_PANEL)
        self.notebook.add(log_tab, text="🧾 Activity Log")
        
        btn_frame = tk.Frame(log_tab, bg=C_PANEL)
        btn_frame.pack(fill="x", padx=5, pady=2)
        tk.Button(btn_frame, text="🗑 Clear Log", command=self._clear_log, bg=C_SURFACE, fg=C_TEXT, relief="flat", bd=0, cursor="hand2", padx=10).pack(side="right")

        self.log_box = tk.Text(log_tab, bg=C_PANEL, fg=C_TEXT, font=FONT_MONO, relief="flat", bd=0, state="disabled", wrap="word", padx=10, pady=5)
        vsb = ttk.Scrollbar(log_tab, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=vsb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.log_box.tag_configure("success", foreground=C_SUCCESS)
        self.log_box.tag_configure("error",   foreground=C_ERROR)
        self.log_box.tag_configure("info",    foreground=C_ACCENT)
        self.log_box.tag_configure("normal",  foreground=C_TEXT)

        # -- Transfers Tab --
        transfer_tab = tk.Frame(self.notebook, bg=C_PANEL)
        self.notebook.add(transfer_tab, text="🔄 Active Transfers")
        
        t_inner = tk.Frame(transfer_tab, bg=C_PANEL)
        t_inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.transfer_label_big = tk.Label(t_inner, text="No active transfers.", bg=C_PANEL, fg=C_MUTED, font=FONT_TITLE)
        self.transfer_label_big.pack(anchor="w", pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(t_inner, variable=self.progress_var, maximum=100, style="Blue.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=5)
        
        self.transfer_speed_big = tk.Label(t_inner, text="", bg=C_PANEL, fg=C_ACCENT, font=FONT_BOLD)
        self.transfer_speed_big.pack(anchor="e")

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C_SURFACE, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_dot = tk.Label(bar, text="●", bg=C_SURFACE, fg=C_ERROR, font=("Segoe UI", 12))
        self.status_dot.pack(side="left", padx=(15, 5))
        tk.Label(bar, textvariable=self.status_text, bg=C_SURFACE, fg=C_TEXT, font=FONT_MAIN).pack(side="left")

        tk.Label(bar, text="TurboFTP v2.0", bg=C_SURFACE, fg=C_MUTED, font=FONT_MAIN).pack(side="right", padx=15)

    def _build_context_menus(self):
        # Local Menu
        self.local_menu = Menu(self, tearoff=0, bg=C_SURFACE, fg=C_TEXT, activebackground=C_ACCENT, activeforeground="#000", font=FONT_MAIN, bd=0)
        self.local_menu.add_command(label="📤 Upload Selected", command=self._upload_selected)
        self.local_menu.add_separator()
        self.local_menu.add_command(label="❌ Delete", command=self._delete_local)
        self.local_menu.add_command(label="⟳ Refresh", command=self._refresh_local)

        # Remote Menu
        self.remote_menu = Menu(self, tearoff=0, bg=C_SURFACE, fg=C_TEXT, activebackground=C_ACCENT, activeforeground="#000", font=FONT_MAIN, bd=0)
        self.remote_menu.add_command(label="📥 Download Selected", command=self._download_selected)
        self.remote_menu.add_separator()
        self.remote_menu.add_command(label="➕ New Folder", command=self._new_folder)
        self.remote_menu.add_command(label="✏ Rename", command=self._rename_selected)
        self.remote_menu.add_command(label="❌ Delete", command=self._delete_selected)
        self.remote_menu.add_separator()
        self.remote_menu.add_command(label="⟳ Refresh", command=self._refresh_remote)

    def _show_local_menu(self, event):
        if self.local_tree.selection():
            self.local_menu.post(event.x_root, event.y_root)

    def _show_remote_menu(self, event):
        if self.remote_tree.selection() and self.ftp_worker.connected:
            self.remote_menu.post(event.x_root, event.y_root)

    # ── LOGGING ─────────────────────────────
    def log(self, msg, level="normal"):
        def _write():
            ts = time.strftime("%H:%M:%S")
            self.log_box.config(state="normal")
            self.log_box.insert("end", f"[{ts}] {msg}\n", level)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _write)

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    # ── CONNECTION ───────────────────────────
    def _toggle_connect(self):
        if self.ftp_worker.connected:
            self._run_async(self._do_disconnect)
        else:
            self._run_async(self._do_connect)

    def _do_connect(self):
        host = self.host_var.get().strip()
        if not host:
            self.log("❌ Enter a host address first.", "error")
            return
        self.after(0, lambda: self._set_ui_state("Connecting..."))
        ok = self.ftp_worker.connect(host, self.port_var.get(), self.user_var.get(), self.pass_var.get(), self.passive_var.get())
        if ok:
            self._add_to_recent()
            self.after(0, self._on_connected)
        else:
            self.after(0, self._on_disconnected)

    def _do_disconnect(self):
        self.ftp_worker.disconnect()
        self.after(0, self._on_disconnected)

    def _set_ui_state(self, status):
        self.status_text.set(status)
        self.connect_btn.config(state="disabled", text="Connecting...", bg=C_MUTED)

    def _on_connected(self):
        self.connect_btn.config(text="■ Disconnect", bg=C_ERROR, fg="#fff", state="normal")
        self.status_text.set(f"Connected to {self.host_var.get()}")
        self.status_dot.config(fg=C_SUCCESS)
        self._refresh_remote()

    def _on_disconnected(self):
        self.connect_btn.config(text="⚡ Quick Connect", bg=C_ACCENT, fg="#000", state="normal")
        self.status_text.set("Ready - Not connected")
        self.status_dot.config(fg=C_ERROR)
        self.remote_tree.delete(*self.remote_tree.get_children())
        self.remote_path.set("/")

    # ── LOCAL FILE PANEL ─────────────────────
    def _go_local_home(self):
        self.local_path.set(str(Path.home()))
        self._refresh_local()

    def _go_local_up(self):
        parent = str(Path(self.local_path.get()).parent)
        self.local_path.set(parent)
        self._refresh_local()

    def _refresh_local(self):
        path = self.local_path.get()
        if not os.path.exists(path):
            path = str(Path.home())
            self.local_path.set(path)
            
        self._save_config()
        
        # Batch UI update for speed
        self.local_tree.delete(*self.local_tree.get_children())
        try:
            entries = list(os.scandir(path))
        except PermissionError:
            self.log(f"❌ Cannot access: {path}", "error")
            return

        dirs  = sorted([e for e in entries if e.is_dir()],  key=lambda e: e.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda e: e.name.lower())

        for entry in dirs:
            self.local_tree.insert("", "end", iid=entry.path, values=(f"📁 {entry.name}", "", "DIR"))
            
        for entry in files:
            size = self._fmt_size(entry.stat().st_size)
            ext  = Path(entry.name).suffix.lstrip(".").upper() or "FILE"
            self.local_tree.insert("", "end", iid=entry.path, values=(f"📄 {entry.name}", size, ext))

    def _local_double_click(self, event):
        sel = self.local_tree.selection()
        if not sel: return
        iid = sel[0]
        if os.path.isdir(iid):
            self.local_path.set(iid)
            self._refresh_local()
        elif os.path.isfile(iid) and self.ftp_worker.connected:
            self._do_upload([iid])

    def _browse_local(self):
        d = filedialog.askdirectory(initialdir=self.local_path.get())
        if d:
            self.local_path.set(d)
            self._refresh_local()

    def _delete_local(self):
        sel = self.local_tree.selection()
        if not sel: return
        files_to_delete = [iid for iid in sel if iid != "__up__"]
        if not files_to_delete: return
        
        if messagebox.askyesno("Confirm", f"Delete {len(files_to_delete)} local file(s)?"):
            for f in files_to_delete:
                try:
                    if os.path.isdir(f): os.rmdir(f) # Only empty dirs for safety
                    else: os.remove(f)
                except Exception as e:
                    self.log(f"❌ Failed to delete local {f}: {e}", "error")
            self._refresh_local()

    # ── REMOTE FILE PANEL ────────────────────
    def _go_remote_up(self):
        if not self.ftp_worker.connected: return
        parent = str(Path(self.ftp_worker.current_dir).parent).replace("\\", "/")
        if not parent: parent = "/"
        self._run_async(lambda: self._navigate_to(parent))

    def _refresh_remote(self):
        if not self.ftp_worker.connected: return
        self._run_async(self._do_refresh_remote)

    def _do_refresh_remote(self):
        items = self.ftp_worker.list_dir(self.ftp_worker.current_dir)
        self.after(0, lambda: self._populate_remote(items))
        self.after(0, lambda: self.remote_path.set(self.ftp_worker.current_dir))

    def _populate_remote(self, items):
        self.remote_tree.delete(*self.remote_tree.get_children())
        dirs  = [i for i in items if i["is_dir"]]
        files = [i for i in items if not i["is_dir"]]

        for item in sorted(dirs, key=lambda x: x["name"].lower()):
            self.remote_tree.insert("", "end", iid=f"dir::{item['name']}",
                                    values=(f"📁 {item['name']}", "", item["date"], item["perms"]))
                                     
        for item in sorted(files, key=lambda x: x["name"].lower()):
            size_str = self._fmt_size(item["size"])
            self.remote_tree.insert("", "end", iid=f"file::{item['name']}",
                                    values=(f"📄 {item['name']}", size_str, item["date"], item["perms"]))

    def _remote_double_click(self, event):
        sel = self.remote_tree.selection()
        if not sel: return
        iid = sel[0]
        if iid.startswith("dir::"):
            name = iid[5:]
            new_path = self.ftp_worker.current_dir.rstrip("/") + "/" + name
            self._run_async(lambda p=new_path: self._navigate_to(p))
        elif iid.startswith("file::"):
            name = iid[6:]
            local_dir = self.local_path.get()
            self._run_async(lambda: self._do_download([name], local_dir))

    def _navigate_to(self, path):
        self.after(0, lambda: self.remote_path.set("Loading..."))
        items = self.ftp_worker.list_dir(path)
        self.after(0, lambda: self._populate_remote(items))
        self.after(0, lambda: self.remote_path.set(self.ftp_worker.current_dir))

    def _navigate_remote(self):
        if not self.ftp_worker.connected:
            self.log("❌ Not connected.", "error")
            return
        path = self.remote_path.get()
        self._run_async(lambda: self._navigate_to(path))

    def _refresh_all(self):
        self._refresh_local()
        self._refresh_remote()

    # ── TRANSFERS ────────────────────────────
    def _update_progress(self, done, total, speed, fname, prefix="⬇"):
        pct = (done / total) * 100 if total else 0
        speed_str = self._fmt_size(speed) + "/s"
        self.after(0, lambda: (
            self.progress_var.set(pct),
            self.transfer_label_big.config(text=f"{prefix} Transferring: {fname} ({pct:.1f}%)", fg=C_TEXT),
            self.transfer_speed_big.config(text=f"Speed: {speed_str}")
        ))

    def _reset_progress(self):
        self.after(0, lambda: (
            self.progress_var.set(0),
            self.transfer_label_big.config(text="No active transfers.", fg=C_MUTED),
            self.transfer_speed_big.config(text="")
        ))

    def _download_selected(self):
        if not self.ftp_worker.connected: return
        sel = self.remote_tree.selection()
        files = [iid[6:] for iid in sel if iid.startswith("file::")]
        if not files: return
        
        self.notebook.select(1) # Switch to transfers tab
        local_dir = self.local_path.get()
        self._run_async(lambda: self._do_download(files, local_dir))

    def _do_download(self, filenames, local_dir):
        for name in filenames:
            remote_full = self.ftp_worker.current_dir.rstrip("/") + "/" + name
            local_full  = os.path.join(local_dir, name)
            self.ftp_worker.download_file(remote_full, local_full, 
                                          progress_cb=lambda d, t, s, n=name: self._update_progress(d, t, s, n, "📥"))
        self._reset_progress()
        self.after(0, self._refresh_local)

    def _upload_selected(self):
        if not self.ftp_worker.connected: return
        sel = self.local_tree.selection()
        files = [iid for iid in sel if os.path.isfile(iid)]
        if not files:
            files = filedialog.askopenfilenames(initialdir=self.local_path.get(), title="Select files to upload")
            if not files: return
            
        self.notebook.select(1) # Switch to transfers tab
        self._run_async(lambda: self._do_upload(list(files)))

    def _do_upload(self, local_files):
        for local_full in local_files:
            name = os.path.basename(local_full)
            remote_full = self.ftp_worker.current_dir.rstrip("/") + "/" + name
            self.ftp_worker.upload_file(local_full, remote_full, 
                                        progress_cb=lambda d, t, s, n=name: self._update_progress(d, t, s, n, "📤"))
        self._reset_progress()
        self.after(0, self._refresh_remote)

    # ── REMOTE OPERATIONS ────────────────────
    def _delete_selected(self):
        if not self.ftp_worker.connected: return
        sel = self.remote_tree.selection()
        if not sel: return

        names = []
        for iid in sel:
            if iid.startswith("file::"): names.append(("file", iid[6:]))
            elif iid.startswith("dir::"): names.append(("dir", iid[5:]))

        if not names: return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(names)} item(s) from server?"): return

        def _do():
            for kind, name in names:
                full = self.ftp_worker.current_dir.rstrip("/") + "/" + name
                if kind == "file":
                    self.ftp_worker.execute_cmd(lambda: self.ftp_worker.ftp.delete(full), f"❌ Deleted: {name}", "Delete failed")
                else:
                    self.ftp_worker.execute_cmd(lambda: self.ftp_worker.ftp.rmd(full), f"❌ Removed dir: {name}", "Remove dir failed")
            self.after(0, self._refresh_remote)
        self._run_async(_do)

    def _new_folder(self):
        if not self.ftp_worker.connected: return
        name = simpledialog.askstring("New Folder", "Enter folder name:", parent=self)
        if name:
            full = self.ftp_worker.current_dir.rstrip("/") + "/" + name
            self._run_async(lambda: (
                self.ftp_worker.execute_cmd(lambda: self.ftp_worker.ftp.mkd(full), f"➕ Created dir: {name}", "MkDir failed"),
                self.after(0, self._refresh_remote)
            ))

    def _rename_selected(self):
        if not self.ftp_worker.connected: return
        sel = self.remote_tree.selection()
        if not sel: return
        iid = sel[0]
        old_name = iid[6:] if iid.startswith("file::") else iid[5:] if iid.startswith("dir::") else None
        if not old_name: return

        new_name = simpledialog.askstring("Rename", f"Rename '{old_name}' to:", initialvalue=old_name, parent=self)
        if new_name and new_name != old_name:
            base = self.ftp_worker.current_dir.rstrip("/")
            self._run_async(lambda: (
                self.ftp_worker.execute_cmd(lambda: self.ftp_worker.ftp.rename(f"{base}/{old_name}", f"{base}/{new_name}"), 
                                            f"✏️ Renamed: {old_name} → {new_name}", "Rename failed"),
                self.after(0, self._refresh_remote)
            ))

    # ── SORTING & UTILS ──────────────────────
    def _sort_tree(self, tree, col, descending):
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        if col == "Size":
            def sort_key(val):
                text = val[0]
                if not text: return 0
                multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
                try:
                    num, unit = text.split()
                    return float(num) * multipliers.get(unit, 1)
                except: return 0
            data.sort(key=sort_key, reverse=descending)
        else:
            data.sort(reverse=descending)

        for index, item in enumerate(data):
            tree.move(item[1], '', index)
        tree.heading(col, command=lambda c=col: self._sort_tree(tree, c, not descending))

    @staticmethod
    def _fmt_size(n):
        if n == 0: return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024: return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    def _run_async(self, func):
        threading.Thread(target=func, daemon=True).start()

    def _process_queue(self):
        try:
            while True:
                cb = self.task_queue.get_nowait()
                cb()
        except queue.Empty:
            pass
        self.after(50, self._process_queue)

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = FTPApp()
    app.mainloop()