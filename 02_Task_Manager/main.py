"""
TaskPulse - Premium Process Manager
Real-time system monitoring with one-click process control.
"""

import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk
import psutil
import time
import os
import sys
import threading


# ══════════════════════════════════════════════════════════════
#  THEME CONSTANTS
# ══════════════════════════════════════════════════════════════

BG           = "#08080e"
BG_SURFACE   = "#0e0e18"
BG_CARD      = "#131320"
BG_ELEVATED  = "#1a1a2e"
BG_HOVER     = "#22223a"
BG_SELECTED  = "#1c1c3a"
BORDER       = "#1e1e35"
BORDER_LIGHT = "#2a2a48"

BLUE         = "#4d8dff"
BLUE_BRIGHT  = "#6aa3ff"
BLUE_DIM     = "#2a4a8a"
PURPLE       = "#8855ff"
PURPLE_DIM   = "#4a2e8a"
CYAN         = "#00d4e5"
MAGENTA      = "#e040a0"
GREEN        = "#00e876"
GREEN_DIM    = "#00803a"
RED          = "#ff3355"
RED_DIM      = "#8a1a2e"
RED_HOVER    = "#ff5577"
YELLOW       = "#ffc800"
ORANGE       = "#ff8833"

TEXT         = "#e4e4f0"
TEXT_SEC     = "#8888a8"
TEXT_DIM     = "#555575"

# Process type color coding
APP_COLORS = {
    "high_cpu":  RED,
    "high_mem":  ORANGE,
    "normal":    TEXT,
    "low":       TEXT_DIM,
    "system":    PURPLE,
}


class TaskPulseApp:
    """Premium dark-themed process manager."""

    REFRESH_MS = 2000  # Refresh every 2 seconds

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TaskPulse")
        self.root.configure(bg=BG)

        # Window
        w, h = 900, 700
        sw = root.winfo_screenwidth()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+60")
        root.minsize(760, 550)

        # State
        self.sort_col = "cpu"
        self.sort_reverse = True
        self.search_text = ""
        self.selected_pid = None
        self.processes = []
        self.is_refreshing = False

        # Fonts
        self.f_title  = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.f_head   = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        self.f_body   = tkfont.Font(family="Consolas", size=10)
        self.f_small  = tkfont.Font(family="Segoe UI", size=9)
        self.f_tiny   = tkfont.Font(family="Consolas", size=8)
        self.f_btn    = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_stat_n = tkfont.Font(family="Consolas", size=20, weight="bold")
        self.f_stat_l = tkfont.Font(family="Segoe UI", size=8)
        self.f_search = tkfont.Font(family="Segoe UI", size=11)

        self._build_ui()
        self._refresh_data()

    # ══════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=14, pady=10)

        # ── Header Row ───────────────────────────────────────
        hdr = tk.Frame(main, bg=BG)
        hdr.pack(fill="x", pady=(0, 8))

        tk.Label(hdr, text="⚙ TASKPULSE", font=self.f_title,
                 fg=BLUE_BRIGHT, bg=BG).pack(side="left")

        self.status_dot = tk.Label(hdr, text="● LIVE", font=self.f_tiny,
                                   fg=GREEN, bg=BG)
        self.status_dot.pack(side="right")

        self.proc_count_label = tk.Label(hdr, text="", font=self.f_tiny,
                                          fg=TEXT_DIM, bg=BG)
        self.proc_count_label.pack(side="right", padx=(0, 12))

        # ── System Stats Row ─────────────────────────────────
        stats_row = tk.Frame(main, bg=BG)
        stats_row.pack(fill="x", pady=(0, 8))
        for i in range(4):
            stats_row.columnconfigure(i, weight=1)

        self.cpu_stat = self._make_stat_card(stats_row, "CPU", CYAN, 0)
        self.ram_stat = self._make_stat_card(stats_row, "RAM", PURPLE, 1)
        self.disk_stat = self._make_stat_card(stats_row, "DISK", MAGENTA, 2)
        self.net_stat = self._make_stat_card(stats_row, "NET ↓", BLUE, 3)

        # ── Search + Action Bar ──────────────────────────────
        bar = tk.Frame(main, bg=BG_SURFACE, highlightbackground=BORDER,
                       highlightthickness=1)
        bar.pack(fill="x", pady=(0, 6))
        bar_inner = tk.Frame(bar, bg=BG_SURFACE)
        bar_inner.pack(fill="x", padx=10, pady=8)

        tk.Label(bar_inner, text="🔍", font=self.f_search,
                 fg=TEXT_DIM, bg=BG_SURFACE).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = tk.Entry(
            bar_inner, textvariable=self.search_var,
            font=self.f_search, bg=BG_ELEVATED, fg=TEXT,
            insertbackground=BLUE_BRIGHT, relief="flat",
            highlightbackground=BORDER, highlightthickness=1,
            highlightcolor=BLUE
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(6, 10))
        self.search_entry.insert(0, "")
        self.search_entry.bind("<FocusIn>", lambda e: None)

        # Kill button
        self.kill_btn = tk.Label(
            bar_inner, text="  ✕  END TASK  ", font=self.f_btn,
            fg="#ffffff", bg=RED_DIM, cursor="hand2",
            relief="flat", padx=12, pady=4
        )
        self.kill_btn.pack(side="right")
        self.kill_btn.bind("<Button-1>", self._on_kill_click)
        self.kill_btn.bind("<Enter>", lambda e: self.kill_btn.configure(bg=RED))
        self.kill_btn.bind("<Leave>", lambda e: self.kill_btn.configure(bg=RED_DIM))

        # Refresh button
        ref_btn = tk.Label(
            bar_inner, text="  ↻  REFRESH  ", font=self.f_btn,
            fg=TEXT, bg=BG_ELEVATED, cursor="hand2",
            relief="flat", padx=8, pady=4
        )
        ref_btn.pack(side="right", padx=(0, 6))
        ref_btn.bind("<Button-1>", lambda e: self._refresh_data())
        ref_btn.bind("<Enter>", lambda e: ref_btn.configure(bg=BG_HOVER))
        ref_btn.bind("<Leave>", lambda e: ref_btn.configure(bg=BG_ELEVATED))

        # ── Process List ─────────────────────────────────────
        list_frame = tk.Frame(main, bg=BG_SURFACE, highlightbackground=BORDER,
                              highlightthickness=1)
        list_frame.pack(fill="both", expand=True)

        # Column Headers
        col_hdr = tk.Frame(list_frame, bg=BG_ELEVATED)
        col_hdr.pack(fill="x")

        self.columns = [
            ("name",   "PROCESS NAME",    0.32),
            ("pid",    "PID",             0.08),
            ("cpu",    "CPU %",           0.10),
            ("mem",    "MEMORY",          0.14),
            ("mem_pct","MEM %",           0.08),
            ("status", "STATUS",          0.10),
            ("user",   "USER",            0.18),
        ]

        for col_id, col_title, weight in self.columns:
            btn = tk.Label(
                col_hdr, text=f" {col_title} ▾" if col_id == self.sort_col else f" {col_title}",
                font=self.f_head, fg=BLUE_BRIGHT if col_id == self.sort_col else TEXT_SEC,
                bg=BG_ELEVATED, anchor="w", padx=8, pady=6, cursor="hand2"
            )
            btn.pack(side="left", fill="both", expand=True)
            btn.col_id = col_id
            btn.bind("<Button-1>", self._on_col_click)

        self.col_header_frame = col_hdr

        # Scrollable list
        scroll_container = tk.Frame(list_frame, bg=BG_SURFACE)
        scroll_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(scroll_container, bg=BG_SURFACE,
                                highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(scroll_container, orient="vertical",
                                       command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.list_frame_inner = tk.Frame(self.canvas, bg=BG_SURFACE)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.list_frame_inner, anchor="nw"
        )

        self.list_frame_inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Footer ───────────────────────────────────────────
        tk.Label(main, text="click a process → END TASK  |  auto-refresh every 2s",
                 font=self.f_tiny, fg=TEXT_DIM, bg=BG).pack(pady=(4, 0))

    def _make_stat_card(self, parent, label, color, col):
        """Create a system stat card."""
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        px = (0 if col == 0 else 3, 3 if col < 3 else 0)
        card.grid(row=0, column=col, sticky="nsew", padx=px)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(padx=10, pady=8)

        tk.Label(inner, text=label, font=self.f_stat_l, fg=TEXT_DIM,
                 bg=BG_CARD).pack(anchor="w")

        val_var = tk.StringVar(value="--")
        val_lbl = tk.Label(inner, textvariable=val_var, font=self.f_stat_n,
                           fg=color, bg=BG_CARD)
        val_lbl.pack(anchor="w")

        sub_var = tk.StringVar(value="")
        tk.Label(inner, textvariable=sub_var, font=self.f_tiny,
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w")

        # Usage bar
        bar = tk.Canvas(inner, height=3, bg=BG, highlightthickness=0, width=120)
        bar.pack(fill="x", pady=(4, 0))

        return {"val": val_var, "sub": sub_var, "bar": bar, "color": color}

    # ══════════════════════════════════════════════════════════
    #  DATA REFRESH
    # ══════════════════════════════════════════════════════════

    def _refresh_data(self):
        """Kick off a background refresh."""
        if self.is_refreshing:
            return
        self.is_refreshing = True
        t = threading.Thread(target=self._collect_data, daemon=True)
        t.start()

    def _collect_data(self):
        """Collect process + system data in background thread."""
        try:
            procs = []
            for p in psutil.process_iter(
                    ['pid', 'name', 'cpu_percent', 'memory_info',
                     'memory_percent', 'status', 'username']):
                try:
                    info = p.info
                    mem = info.get('memory_info')
                    procs.append({
                        "pid":     info['pid'],
                        "name":    info['name'] or "System",
                        "cpu":     info.get('cpu_percent', 0) or 0,
                        "mem_bytes": mem.rss if mem else 0,
                        "mem_pct": info.get('memory_percent', 0) or 0,
                        "status":  info.get('status', 'unknown'),
                        "user":    (info.get('username') or '').split('\\')[-1] or "SYSTEM",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            cpu_pct = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = psutil.net_io_counters()

            self.root.after(0, self._apply_data, procs, cpu_pct, ram, disk, net)
        except Exception:
            self.root.after(0, self._schedule_next)

    def _apply_data(self, procs, cpu_pct, ram, disk, net):
        """Apply collected data to UI (main thread)."""
        self.processes = procs
        self._update_stats(cpu_pct, ram, disk, net)
        self._render_list()
        self.proc_count_label.configure(text=f"{len(procs)} processes")
        self.is_refreshing = False
        self._schedule_next()

    def _schedule_next(self):
        self.is_refreshing = False
        self.root.after(self.REFRESH_MS, self._refresh_data)

    def _update_stats(self, cpu, ram, disk, net):
        """Update the 4 stat cards."""
        # CPU
        self.cpu_stat["val"].set(f"{cpu:.0f}%")
        cores = psutil.cpu_count()
        self.cpu_stat["sub"].set(f"{cores} cores")
        self._draw_bar(self.cpu_stat["bar"], cpu / 100, self.cpu_stat["color"])

        # RAM
        used_gb = ram.used / (1024 ** 3)
        total_gb = ram.total / (1024 ** 3)
        self.ram_stat["val"].set(f"{ram.percent:.0f}%")
        self.ram_stat["sub"].set(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self._draw_bar(self.ram_stat["bar"], ram.percent / 100, self.ram_stat["color"])

        # Disk
        self.disk_stat["val"].set(f"{disk.percent:.0f}%")
        free_gb = disk.free / (1024 ** 3)
        self.disk_stat["sub"].set(f"{free_gb:.0f} GB free")
        self._draw_bar(self.disk_stat["bar"], disk.percent / 100, self.disk_stat["color"])

        # Net
        dl_mb = net.bytes_recv / (1024 ** 2)
        if dl_mb >= 1024:
            self.net_stat["val"].set(f"{dl_mb/1024:.1f}G")
        else:
            self.net_stat["val"].set(f"{dl_mb:.0f}M")
        ul_mb = net.bytes_sent / (1024 ** 2)
        self.net_stat["sub"].set(f"↑ {ul_mb:.0f} MB")
        self._draw_bar(self.net_stat["bar"], min(dl_mb / 10000, 1.0), self.net_stat["color"])

    def _draw_bar(self, canvas, ratio, color):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1:
            w = 120
        ratio = max(0, min(ratio, 1))
        canvas.create_rectangle(0, 0, w, 3, fill=BG, outline="")
        canvas.create_rectangle(0, 0, int(w * ratio), 3, fill=color, outline="")

    # ══════════════════════════════════════════════════════════
    #  PROCESS LIST RENDERING
    # ══════════════════════════════════════════════════════════

    def _get_filtered_sorted(self):
        """Filter and sort processes."""
        data = self.processes
        q = self.search_text.lower().strip()
        if q:
            data = [p for p in data if q in p["name"].lower()
                    or q in str(p["pid"]) or q in p["user"].lower()]

        key_map = {
            "name":    lambda p: p["name"].lower(),
            "pid":     lambda p: p["pid"],
            "cpu":     lambda p: p["cpu"],
            "mem":     lambda p: p["mem_bytes"],
            "mem_pct": lambda p: p["mem_pct"],
            "status":  lambda p: p["status"],
            "user":    lambda p: p["user"].lower(),
        }
        key_fn = key_map.get(self.sort_col, key_map["cpu"])
        data.sort(key=key_fn, reverse=self.sort_reverse)
        return data

    def _format_mem(self, b):
        if b >= 1073741824:
            return f"{b / 1073741824:.1f} GB"
        elif b >= 1048576:
            return f"{b / 1048576:.1f} MB"
        elif b >= 1024:
            return f"{b / 1024:.0f} KB"
        return f"{b} B"

    def _render_list(self):
        """Render process rows."""
        for w in self.list_frame_inner.winfo_children():
            w.destroy()

        data = self._get_filtered_sorted()

        for idx, p in enumerate(data):
            is_sel = (p["pid"] == self.selected_pid)
            bg = BG_SELECTED if is_sel else (BG_ELEVATED if idx % 2 else BG_SURFACE)

            row = tk.Frame(self.list_frame_inner, bg=bg, cursor="hand2")
            row.pack(fill="x")
            row.pid = p["pid"]
            row.bind("<Button-1>", self._on_row_click)

            # Color based on resource usage
            if p["cpu"] > 20:
                name_fg = RED
            elif p["cpu"] > 5:
                name_fg = ORANGE
            elif p["mem_pct"] > 10:
                name_fg = YELLOW
            else:
                name_fg = TEXT

            # Status color
            st = p["status"]
            if st == "running":
                st_fg = GREEN
            elif st == "sleeping":
                st_fg = TEXT_DIM
            elif st == "stopped":
                st_fg = RED
            else:
                st_fg = TEXT_SEC

            vals = [
                (p["name"][:32],               name_fg),
                (str(p["pid"]),                 TEXT_SEC),
                (f"{p['cpu']:.1f}",            RED if p["cpu"] > 20 else CYAN),
                (self._format_mem(p["mem_bytes"]), TEXT),
                (f"{p['mem_pct']:.1f}",        ORANGE if p["mem_pct"] > 10 else TEXT_SEC),
                (st[:10],                       st_fg),
                (p["user"][:16],               TEXT_DIM),
            ]

            for (val, fg) in vals:
                lbl = tk.Label(row, text=f" {val}", font=self.f_body,
                               fg=fg, bg=bg, anchor="w", pady=4)
                lbl.pack(side="left", fill="both", expand=True)
                lbl.bind("<Button-1>", self._on_row_click)
                lbl.pid = p["pid"]

            # Highlight border for selected
            if is_sel:
                sel_mark = tk.Frame(row, bg=BLUE, width=3)
                sel_mark.pack(side="left", fill="y")

    # ══════════════════════════════════════════════════════════
    #  EVENT HANDLERS
    # ══════════════════════════════════════════════════════════

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_search(self, *_):
        self.search_text = self.search_var.get()
        self._render_list()

    def _on_col_click(self, event):
        w = event.widget
        col_id = getattr(w, 'col_id', None)
        if not col_id:
            return
        if col_id == self.sort_col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col_id
            self.sort_reverse = True

        # Update header labels
        for child in self.col_header_frame.winfo_children():
            cid = getattr(child, 'col_id', None)
            if cid:
                title = [t for c, t, _ in self.columns if c == cid][0]
                if cid == self.sort_col:
                    arrow = " ▴" if not self.sort_reverse else " ▾"
                    child.configure(text=f" {title}{arrow}", fg=BLUE_BRIGHT)
                else:
                    child.configure(text=f" {title}", fg=TEXT_SEC)

        self._render_list()

    def _on_row_click(self, event):
        w = event.widget
        pid = getattr(w, 'pid', None)
        if pid is None:
            pid = getattr(w.master, 'pid', None)
        if pid is not None:
            self.selected_pid = pid
            self._render_list()

    def _on_kill_click(self, event):
        if self.selected_pid is None:
            messagebox.showinfo("TaskPulse", "Select a process first.",
                                parent=self.root)
            return

        # Find process name
        name = "Unknown"
        for p in self.processes:
            if p["pid"] == self.selected_pid:
                name = p["name"]
                break

        confirm = messagebox.askyesno(
            "End Task — Confirm",
            f"Are you sure you want to end this process?\n\n"
            f"  Name:  {name}\n"
            f"  PID:     {self.selected_pid}\n\n"
            f"Unsaved data in this program may be lost.",
            icon="warning",
            parent=self.root
        )

        if confirm:
            try:
                proc = psutil.Process(self.selected_pid)
                proc.terminate()
                proc.wait(timeout=3)
                messagebox.showinfo(
                    "TaskPulse",
                    f"✓ Process '{name}' (PID {self.selected_pid}) terminated.",
                    parent=self.root
                )
            except psutil.NoSuchProcess:
                messagebox.showinfo("TaskPulse", "Process already ended.",
                                    parent=self.root)
            except psutil.AccessDenied:
                messagebox.showerror(
                    "TaskPulse",
                    f"Access denied. Try running as Administrator.",
                    parent=self.root
                )
            except Exception as ex:
                messagebox.showerror("TaskPulse", f"Error: {ex}",
                                     parent=self.root)

            self.selected_pid = None
            self._refresh_data()


# ══════════════════════════════════════════════════════════════
#  ENTRY
# ══════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    ico = os.path.join(script_dir, "icon.ico")
    try:
        if os.path.exists(ico):
            root.iconbitmap(default=ico)
    except Exception:
        pass

    # Dark title bar
    try:
        from ctypes import windll, c_int, byref, sizeof
        HWND = windll.user32.GetParent(root.winfo_id())
        windll.dwmapi.DwmSetWindowAttribute(
            HWND, 20, byref(c_int(1)), sizeof(c_int))
    except Exception:
        pass

    app = TaskPulseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
