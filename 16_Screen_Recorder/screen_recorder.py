"""
ScreenForge Pro v4.0 — Premium Screen Recorder
Fixes: frame-time sync, floating stop widget, no self-recording
"""
import cv2, numpy as np, pyautogui, threading, time, os, tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

pyautogui.FAILSAFE = False

# ── Region Selector ──
class RegionSelector:
    def __init__(self, parent):
        self.result = None
        self.sx = self.sy = 0
        self.top = tk.Toplevel(parent)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        self.top.configure(bg="black")
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self._p)
        self.canvas.bind("<B1-Motion>", self._d)
        self.canvas.bind("<ButtonRelease-1>", self._r)
        self.top.bind("<Escape>", lambda e: self.top.destroy())
        self.canvas.create_text(self.top.winfo_screenwidth()//2, 50,
            text="Drag to select • ESC cancel", fill="white", font=("Segoe UI", 16))
    def _p(self, e):
        self.sx, self.sy = e.x, e.y
        if self.rect: self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.sx,self.sy,self.sx,self.sy,outline="cyan",width=2)
    def _d(self, e): self.canvas.coords(self.rect, self.sx, self.sy, e.x, e.y)
    def _r(self, e):
        x1,y1 = min(self.sx,e.x), min(self.sy,e.y)
        x2,y2 = max(self.sx,e.x), max(self.sy,e.y)
        w,h = x2-x1, y2-y1
        if w>20 and h>20:
            self.result = (x1, y1, w - w%2, h - h%2)
        self.top.destroy()

# ── Floating Stop Widget (hidden during capture) ──
class FloatingStop:
    def __init__(self, parent, on_stop, on_pause):
        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.85)
        self.win.configure(bg="#1a1a2e")

        f = tk.Frame(self.win, bg="#1a1a2e", padx=4, pady=4)
        f.pack()

        self.time_lbl = tk.Label(f, text="00:00", fg="#ff4757", bg="#1a1a2e",
                                  font=("Consolas", 11, "bold"))
        self.time_lbl.pack(side="left", padx=(6,8))

        self.pause_btn = tk.Button(f, text="⏸", bg="#2a2a44", fg="white",
            font=("Segoe UI", 11), bd=0, width=3, cursor="hand2",
            activebackground="#3a3a55", command=on_pause)
        self.pause_btn.pack(side="left", padx=2)

        tk.Button(f, text="⏹", bg="#e74c3c", fg="white",
            font=("Segoe UI", 11), bd=0, width=3, cursor="hand2",
            activebackground="#ff5e50", command=on_stop).pack(side="left", padx=2)

        # Position bottom-center
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        ww = self.win.winfo_reqwidth()
        self.win.geometry(f"+{(sw-ww)//2}+8")

        # Track position for masking
        self.win.update_idletasks()

    def get_rect(self):
        """Return (x, y, w, h) of this widget on screen."""
        self.win.update_idletasks()
        return (self.win.winfo_x(), self.win.winfo_y(),
                self.win.winfo_width(), self.win.winfo_height())

    def update_time(self, text):
        try: self.time_lbl.config(text=text)
        except: pass

    def set_paused(self, paused):
        try: self.pause_btn.config(text="▶" if paused else "⏸")
        except: pass

    def hide(self):
        try: self.win.withdraw()
        except: pass

    def show(self):
        try: self.win.deiconify()
        except: pass

    def destroy(self):
        try: self.win.destroy()
        except: pass

# ── Main App ──
class ScreenForgeApp:
    C = {"bg":"#0b0b14","card":"#12121f","border":"#1f1f35","accent":"#6c5ce7",
         "red":"#e74c3c","red_h":"#ff5e50","green":"#2ecc71","yellow":"#f1c40f",
         "text":"#e0e0ec","dim":"#6b6b8a","input":"#181828"}

    def __init__(self, root):
        self.root = root
        self.root.title("ScreenForge Pro")
        self.root.geometry("480x660")
        self.root.resizable(False, False)
        self.root.configure(bg=self.C["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.recording = self.paused = False
        self.start_time = self.pause_start = None
        self.pause_offset = 0.0
        self.frame_count = self.frames_written = 0
        self.out = None
        self.record_thread = None
        self.timer_id = None
        self.region = None
        self.current_file = ""
        self.float_widget = None
        self.save_dir = os.path.join(os.path.expanduser("~"), "Videos", "ScreenForge")
        os.makedirs(self.save_dir, exist_ok=True)

        self._build_ui()
        self.root.bind("<F9>", lambda e: self._toggle_rec())
        self.root.bind("<F10>", lambda e: self._toggle_pause())
        self.root.bind("<F11>", lambda e: self._select_region())

    def _build_ui(self):
        C = self.C

        # Header
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill="x", padx=24, pady=(20,0))
        tk.Label(hdr, text="⬤", fg=C["red"], bg=C["bg"], font=("Segoe UI",12)).pack(side="left")
        tk.Label(hdr, text="  ScreenForge Pro", fg=C["text"], bg=C["bg"],
                 font=("Segoe UI",18,"bold")).pack(side="left")
        tk.Label(hdr, text="v4", fg=C["dim"], bg=C["bg"],
                 font=("Segoe UI",9)).pack(side="left", padx=(6,0), pady=(6,0))

        # Timer Card
        tc = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        tc.pack(fill="x", padx=24, pady=(18,0))
        ti = tk.Frame(tc, bg=C["card"])
        ti.pack(pady=16)
        self.timer_lbl = tk.Label(ti, text="00 : 00 : 00", fg=C["text"], bg=C["card"],
                                   font=("Consolas",36,"bold"))
        self.timer_lbl.pack()
        self.status_lbl = tk.Label(ti, text="READY", fg=C["dim"], bg=C["card"],
                                    font=("Segoe UI",10,"bold"))
        self.status_lbl.pack(pady=(4,0))

        # Settings Card
        sc = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        sc.pack(fill="x", padx=24, pady=(12,0))
        si = tk.Frame(sc, bg=C["card"])
        si.pack(fill="x", padx=16, pady=14)

        # Row 1
        r1 = tk.Frame(si, bg=C["card"]); r1.pack(fill="x")
        for lbl, var_name, vals, w in [("FPS","fps_var",["15","24","30","60"],5),
                                        ("Format","fmt_var",["mp4","avi","mkv"],5),
                                        ("Delay","cd_var",["0","3","5","10"],4)]:
            tk.Label(r1, text=lbl, fg=C["dim"], bg=C["card"], font=("Segoe UI",9)).pack(side="left")
            sv = tk.StringVar(value=vals[2] if lbl=="FPS" else vals[0])
            setattr(self, var_name, sv)
            ttk.Style().theme_use("clam")
            ttk.Combobox(r1, textvariable=sv, values=vals, width=w, state="readonly").pack(
                side="left", padx=(4,16))

        # Row 2: Region
        r2 = tk.Frame(si, bg=C["card"]); r2.pack(fill="x", pady=(10,0))
        tk.Label(r2, text="Region", fg=C["dim"], bg=C["card"], font=("Segoe UI",9)).pack(side="left")
        self.region_lbl = tk.Label(r2, text="Fullscreen", fg=C["green"], bg=C["input"],
                                    font=("Consolas",9), padx=8, pady=3)
        self.region_lbl.pack(side="left", padx=(6,0), fill="x", expand=True)
        for txt, cmd in [("Select", self._select_region), ("Reset", self._reset_region)]:
            tk.Button(r2, text=txt, bg=C["accent"], fg="white", font=("Segoe UI",8,"bold"),
                      bd=0, padx=10, pady=2, cursor="hand2", command=cmd).pack(side="left", padx=(4,0))

        # Row 3: Toggles
        r3 = tk.Frame(si, bg=C["card"]); r3.pack(fill="x", pady=(10,0))
        self.cursor_var = tk.BooleanVar(value=True)
        tk.Checkbutton(r3, text="Cursor dot", variable=self.cursor_var, bg=C["card"],
                       fg=C["dim"], selectcolor=C["input"], activebackground=C["card"],
                       font=("Segoe UI",9)).pack(side="left")

        # Save Location Card
        lc = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        lc.pack(fill="x", padx=24, pady=(12,0))
        li = tk.Frame(lc, bg=C["card"]); li.pack(fill="x", padx=16, pady=12)
        lr = tk.Frame(li, bg=C["card"]); lr.pack(fill="x")
        tk.Label(lr, text="📂", fg=C["dim"], bg=C["card"], font=("Segoe UI",9)).pack(side="left")
        self.path_lbl = tk.Label(lr, text=self._t(self.save_dir,38), fg=C["dim"], bg=C["input"],
                                  font=("Consolas",9), padx=8, pady=3, anchor="w")
        self.path_lbl.pack(side="left", padx=(6,0), fill="x", expand=True)
        tk.Button(lr, text="Browse", bg=C["accent"], fg="white", font=("Segoe UI",8,"bold"),
                  bd=0, padx=10, pady=2, cursor="hand2",
                  command=self._browse).pack(side="left", padx=(8,0))

        # Buttons
        self.rec_btn = tk.Button(self.root, text="⏺   Start Recording", bg=C["red"], fg="white",
                                  activebackground=C["red_h"], activeforeground="white",
                                  font=("Segoe UI",14,"bold"), bd=0, pady=12, cursor="hand2",
                                  command=self._toggle_rec)
        self.rec_btn.pack(fill="x", padx=24, pady=(18,0))

        br = tk.Frame(self.root, bg=C["bg"]); br.pack(fill="x", padx=24, pady=(8,0))
        self.pause_btn = tk.Button(br, text="⏸  Pause", bg=C["card"], fg=C["text"],
                                    activebackground=C["border"], font=("Segoe UI",10),
                                    bd=0, pady=8, state="disabled", cursor="hand2",
                                    command=self._toggle_pause)
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(br, text="📁  Open Folder", bg=C["card"], fg=C["text"],
                  activebackground=C["border"], font=("Segoe UI",10), bd=0, pady=8,
                  cursor="hand2", command=lambda: os.startfile(self.save_dir)).pack(
            side="right", fill="x", expand=True, padx=(4,0))

        tk.Label(self.root, text="F9 Start/Stop  •  F10 Pause  •  F11 Region",
                 fg=C["dim"], bg=C["bg"], font=("Segoe UI",8)).pack(pady=(12,0))

        # Stats bar
        sb = tk.Frame(self.root, bg=C["border"]); sb.pack(fill="x", side="bottom")
        sbi = tk.Frame(sb, bg=C["card"]); sbi.pack(fill="x", padx=1, pady=1)
        scr = pyautogui.size()
        self.stats_lbl = tk.Label(sbi, text=f"{scr[0]}×{scr[1]}  •  0 frames  •  0.0 MB",
                                   fg=C["dim"], bg=C["card"], font=("Consolas",8), pady=5)
        self.stats_lbl.pack()

    def _t(self, p, n=40): return ("..."+p[-(n-3):]) if len(p)>n else p

    def _select_region(self):
        self.root.withdraw(); time.sleep(0.3)
        sel = RegionSelector(self.root)
        self.root.wait_window(sel.top); self.root.deiconify()
        if sel.result:
            x,y,w,h = sel.result; self.region = sel.result
            self.region_lbl.config(text=f"{w}×{h} @ ({x},{y})", fg=self.C["yellow"])
        else: self._reset_region()

    def _reset_region(self):
        self.region = None; self.region_lbl.config(text="Fullscreen", fg=self.C["green"])

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.save_dir)
        if d: self.save_dir = d; self.path_lbl.config(text=self._t(d,38))

    def _toggle_rec(self):
        if not self.recording:
            cd = int(self.cd_var.get())
            if cd > 0: self._countdown(cd)
            else: self._begin()
        else: self._stop()

    def _countdown(self, n):
        if n > 0:
            self.timer_lbl.config(text=str(n), fg=self.C["yellow"])
            self.status_lbl.config(text="STARTING...", fg=self.C["yellow"])
            self.root.after(1000, self._countdown, n-1)
        else: self._begin()

    def _begin(self):
        fps = float(self.fps_var.get())
        fmt = self.fmt_var.get()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = os.path.join(self.save_dir, f"rec_{ts}.{fmt}")

        size = (self.region[2], self.region[3]) if self.region else tuple(pyautogui.size())
        codecs = {"mp4":"mp4v","avi":"XVID","mkv":"mp4v"}
        fourcc = cv2.VideoWriter_fourcc(*codecs.get(fmt,"mp4v"))
        self.out = cv2.VideoWriter(self.current_file, fourcc, fps, size)

        self.recording = True; self.paused = False
        self.frame_count = self.frames_written = 0
        self.start_time = time.perf_counter()
        self.pause_offset = 0.0
        self.target_fps = fps

        # Minimize main window, show floating stop widget
        self.root.iconify()
        time.sleep(0.15)
        self.float_widget = FloatingStop(self.root, self._stop, self._toggle_pause)

        self.rec_btn.config(text="⏹   Stop Recording", bg=self.C["border"])
        self.pause_btn.config(state="normal")
        self.status_lbl.config(text="● REC", fg=self.C["red"])
        self.timer_lbl.config(fg=self.C["red"])

        self.record_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.record_thread.start()
        self._tick()

    def _capture_loop(self):
        """
        Frame-time-synced capture loop.
        Duplicates frames when capture is slower than target FPS
        so playback speed always matches real time.
        """
        fps = self.target_fps
        real_start = time.perf_counter()
        total_pause = 0.0
        pause_mark = None

        while self.recording:
            if self.paused:
                if pause_mark is None:
                    pause_mark = time.perf_counter()
                time.sleep(0.05)
                continue
            else:
                if pause_mark is not None:
                    total_pause += time.perf_counter() - pause_mark
                    pause_mark = None

            t0 = time.perf_counter()

            try:
                # Capture screen (widget stays visible — no blinking)
                if self.region:
                    img = pyautogui.screenshot(region=self.region)
                else:
                    img = pyautogui.screenshot()

                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Paint over the floating widget area so it doesn't
                # appear in the recording (use nearby pixels to blend)
                if self.float_widget:
                    try:
                        wx, wy, ww, wh = self.float_widget.get_rect()
                        ox, oy = 0, 0
                        if self.region:
                            ox, oy = self.region[0], self.region[1]
                        # Widget coords relative to captured frame
                        rx, ry = wx - ox, wy - oy
                        rx2, ry2 = rx + ww, ry + wh
                        fh, fw = frame.shape[:2]
                        # Clamp to frame bounds
                        rx, ry = max(0, rx), max(0, ry)
                        rx2, ry2 = min(fw, rx2), min(fh, ry2)
                        if rx < rx2 and ry < ry2:
                            # Sample color from row just below widget
                            sample_y = min(ry2 + 2, fh - 1)
                            fill = frame[sample_y, rx:rx2].copy()
                            for row in range(ry, ry2):
                                frame[row, rx:rx2] = fill
                    except Exception:
                        pass

                if self.cursor_var.get():
                    try:
                        mx, my = pyautogui.position()
                        if self.region:
                            mx -= self.region[0]; my -= self.region[1]
                        cv2.circle(frame, (mx,my), 7, (0,200,255), -1)
                        cv2.circle(frame, (mx,my), 9, (0,140,200), 2)
                    except: pass

                # Calculate how many frames should exist by now
                active_time = time.perf_counter() - real_start - total_pause
                target_total = int(active_time * fps)
                frames_needed = max(1, target_total - self.frames_written)

                # Write frame (duplicate if capture was slow)
                for _ in range(frames_needed):
                    self.out.write(frame)
                    self.frames_written += 1

                self.frame_count += 1
            except: pass

            # Sleep remaining interval time
            elapsed = time.perf_counter() - t0
            sleep = (1.0/fps) - elapsed
            if sleep > 0:
                time.sleep(sleep)

    def _stop(self):
        self.recording = False
        if self.record_thread: self.record_thread.join(timeout=3)
        if self.out: self.out.release(); self.out = None
        if self.timer_id: self.root.after_cancel(self.timer_id); self.timer_id = None
        if self.float_widget: self.float_widget.destroy(); self.float_widget = None

        self.root.deiconify(); self.root.lift()
        self.rec_btn.config(text="⏺   Start Recording", bg=self.C["red"])
        self.pause_btn.config(state="disabled", text="⏸  Pause")
        self.status_lbl.config(text="✔ SAVED", fg=self.C["green"])
        self.timer_lbl.config(fg=self.C["green"])
        try:
            mb = os.path.getsize(self.current_file)/(1024*1024)
            self.stats_lbl.config(text=f"{os.path.basename(self.current_file)}  •  "
                                       f"{self.frames_written} frames  •  {mb:.1f} MB")
        except: pass

    def _toggle_pause(self):
        if not self.recording: return
        self.paused = not self.paused
        if self.paused:
            self.pause_start = time.time()
            self.pause_btn.config(text="▶  Resume")
            self.status_lbl.config(text="⏸ PAUSED", fg=self.C["yellow"])
            self.timer_lbl.config(fg=self.C["yellow"])
            if self.float_widget: self.float_widget.set_paused(True)
        else:
            self.pause_offset += time.time() - self.pause_start
            self.pause_btn.config(text="⏸  Pause")
            self.status_lbl.config(text="● REC", fg=self.C["red"])
            self.timer_lbl.config(fg=self.C["red"])
            if self.float_widget: self.float_widget.set_paused(False)

    def _tick(self):
        if not self.recording: return
        elapsed = time.time() - (self.start_time if not self.pause_start or not self.paused
                                  else self.start_time) - self.pause_offset
        # Use wall clock for display
        if self.start_time:
            wall = time.perf_counter() - self.start_time - self.pause_offset
            h,rem = divmod(int(max(0,wall)), 3600); m,s = divmod(rem, 60)
            txt = f"{h:02d} : {m:02d} : {s:02d}"
            self.timer_lbl.config(text=txt)
            if self.float_widget:
                self.float_widget.update_time(f"{m:02d}:{s:02d}")
        try:
            if self.current_file and os.path.exists(self.current_file):
                mb = os.path.getsize(self.current_file)/(1024*1024)
                self.stats_lbl.config(text=f"{self.frames_written} written  •  {mb:.1f} MB")
        except: pass
        self.timer_id = self.root.after(500, self._tick)

    def _on_close(self):
        if self.recording: self._stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.update_idletasks()
    x = (root.winfo_screenwidth()-480)//2
    y = (root.winfo_screenheight()-660)//2
    root.geometry(f"480x660+{x}+{y}")
    ScreenForgeApp(root)
    root.mainloop()