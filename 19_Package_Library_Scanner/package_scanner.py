"""
╔══════════════════════════════════════════════════════════╗
║        PYTHON PACKAGE & LIBRARY SCANNER v2.0             ║
║  Shows ALL pip packages, stdlib, builtins, executables   ║
║  with file locations, sizes, summaries, and export.      ║
║                                                          ║
║  Run:  python library_scanner.py                         ║
║  Needs: only built-in Python libs (tkinter, etc.)        ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess, sys, os, importlib, importlib.util
import pkgutil, site, threading, json, csv, shutil, platform
from pathlib import Path
from datetime import datetime


# ═══════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════

C = {
    "bg0":       "#070B10",   # deepest background
    "bg1":       "#0E1520",   # main background
    "bg2":       "#131C2E",   # panel background
    "bg3":       "#192236",   # card / row background
    "bg4":       "#1E2A42",   # hover / selected
    "border":    "#243050",   # borders
    "border2":   "#2E3D60",   # stronger border
    "blue":      "#4D9EFF",   # primary accent
    "blue_dim":  "#1A3A6E",   # accent dim
    "green":     "#3FD68F",   # success / stdlib
    "green_dim": "#0E3D26",
    "amber":     "#F5A623",   # warning / builtin
    "amber_dim": "#3D2800",
    "pink":      "#FF6B9D",   # special
    "pink_dim":  "#3D1030",
    "teal":      "#2DD4BF",   # executable
    "teal_dim":  "#0A2E2B",
    "red":       "#FF5370",
    "text0":     "#E8F0FF",   # primary text
    "text1":     "#8BA3CC",   # secondary text
    "text2":     "#4A6080",   # muted text
    "text3":     "#2A3A55",   # very muted
}

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

FONT_MONO  = ("Consolas", 10)    if IS_WIN else ("Menlo", 10)
FONT_MONO2 = ("Consolas", 11)    if IS_WIN else ("Menlo", 11)
FONT_MONO3 = ("Consolas", 9)     if IS_WIN else ("Menlo", 9)
FONT_UI    = ("Segoe UI", 10)    if IS_WIN else ("Helvetica Neue", 10)
FONT_UI_B  = ("Segoe UI", 10, "bold") if IS_WIN else ("Helvetica Neue", 10, "bold")
FONT_LG    = ("Segoe UI", 14, "bold") if IS_WIN else ("Helvetica Neue", 14, "bold")
FONT_XL    = ("Segoe UI", 18, "bold") if IS_WIN else ("Helvetica Neue", 18, "bold")
FONT_SM    = ("Segoe UI", 8)     if IS_WIN else ("Helvetica Neue", 8)


# ═══════════════════════════════════════════════════════════
#  DATA COLLECTION
# ═══════════════════════════════════════════════════════════

def fmt_size(path):
    """Format file/folder size nicely."""
    try:
        if os.path.isfile(path):
            b = os.path.getsize(path)
        elif os.path.isdir(path):
            b = sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
        else:
            return ""
        for unit in ["B","KB","MB","GB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"
    except Exception:
        return ""


def get_pip_packages():
    packages = []
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"],
                           capture_output=True, text=True, timeout=30)
        raw = json.loads(r.stdout)
    except Exception as e:
        return [{"name": f"pip error: {e}", "version":"","type":"pip",
                 "location":"","folder":"","size":"","summary":"","homepage":"","requires":""}]

    # Batch pip show
    names = [p["name"] for p in raw]
    batch_size = 50
    pkg_info = {}
    for i in range(0, len(names), batch_size):
        try:
            r2 = subprocess.run(
                [sys.executable, "-m", "pip", "show"] + names[i:i+batch_size],
                capture_output=True, text=True, timeout=60)
            cur = {}
            for line in r2.stdout.splitlines():
                if line.startswith("Name:"):
                    if cur: pkg_info[cur.get("name","").lower()] = cur
                    cur = {"name": line.split(":",1)[1].strip()}
                elif ":" in line:
                    k, v = line.split(":",1)
                    cur[k.strip().lower()] = v.strip()
            if cur: pkg_info[cur.get("name","").lower()] = cur
        except Exception:
            pass

    for p in raw:
        info = pkg_info.get(p["name"].lower(), {})
        loc  = info.get("location", "")
        nm   = p["name"]

        # Find actual folder
        folder = ""
        if loc:
            for variant in [nm, nm.replace("-","_"), nm.lower(), nm.replace("-","_").lower()]:
                cand = os.path.join(loc, variant)
                if os.path.exists(cand):
                    folder = cand
                    break
        if not folder:
            # Try .dist-info
            dist = nm.replace("-","_") + "-" + p["version"] + ".dist-info"
            dp = os.path.join(loc, dist) if loc else ""
            if dp and os.path.exists(dp):
                folder = dp
            elif loc:
                folder = loc

        packages.append({
            "name":     nm,
            "version":  p["version"],
            "type":     "pip",
            "location": loc or "—",
            "folder":   folder or loc or "—",
            "size":     fmt_size(folder) if folder and os.path.exists(folder) else "",
            "summary":  info.get("summary", ""),
            "homepage": info.get("home-page", ""),
            "requires": info.get("requires", ""),
        })
    return packages


def get_stdlib_modules():
    modules = []
    stdlib_path = os.path.dirname(os.__file__)
    scan_dirs   = [p for p in [stdlib_path] + sys.path
                   if p and os.path.isdir(p)
                   and "site-packages" not in p
                   and p != ""]
    seen = set()
    for finder, name, ispkg in pkgutil.iter_modules(scan_dirs):
        if name in seen: continue
        seen.add(name)
        try:
            spec = importlib.util.find_spec(name)
            loc  = spec.origin if spec and spec.origin else "built-in"
        except Exception:
            loc = "built-in"
        folder = os.path.dirname(loc) if loc not in ("built-in", None) else "built-in"
        modules.append({
            "name":     name,
            "version":  platform.python_version(),
            "type":     "stdlib",
            "location": loc,
            "folder":   folder,
            "size":     fmt_size(loc) if loc and loc != "built-in" and os.path.exists(loc) else "",
            "summary":  "Python standard library",
            "homepage": f"https://docs.python.org/3/library/{name}.html",
            "requires": "",
        })

    for name in sys.builtin_module_names:
        if name in seen: continue
        seen.add(name)
        modules.append({
            "name":     name,
            "version":  platform.python_version(),
            "type":     "builtin",
            "location": "C extension (built-in)",
            "folder":   os.path.dirname(sys.executable),
            "size":     "",
            "summary":  "Built-in C extension module",
            "homepage": "",
            "requires": "",
        })
    return sorted(modules, key=lambda x: x["name"].lower())


def get_executables():
    """Find Python-related executables (pip, pytest, black, etc.) in PATH."""
    execs = []
    seen  = set()
    script_dirs = set()
    for sp in site.getsitepackages():
        # Scripts usually one level up or in Scripts/bin sibling
        script_dirs.add(sp)
        parent = os.path.dirname(sp)
        for sub in ["Scripts", "bin"]:
            script_dirs.add(os.path.join(parent, sub))
    script_dirs.add(os.path.dirname(sys.executable))

    for d in script_dirs:
        if not os.path.isdir(d): continue
        try:
            for f in os.listdir(d):
                fpath = os.path.join(d, f)
                if not os.path.isfile(fpath): continue
                if f in seen: continue
                if not (f.endswith(".exe") or f.endswith(".cmd") or
                        os.access(fpath, os.X_OK) or
                        f.endswith(".py")):
                    continue
                seen.add(f)
                execs.append({
                    "name":     f,
                    "version":  "",
                    "type":     "executable",
                    "location": fpath,
                    "folder":   d,
                    "size":     fmt_size(fpath),
                    "summary":  "Executable / script in Python environment",
                    "homepage": "",
                    "requires": "",
                })
        except Exception:
            pass
    return sorted(execs, key=lambda x: x["name"].lower())


def get_site_info():
    info = {
        "Python Version":    platform.python_version(),
        "Python Build":      " ".join(platform.python_build()),
        "Python Compiler":   platform.python_compiler(),
        "Python Executable": sys.executable,
        "Platform":          platform.platform(),
        "Architecture":      platform.architecture()[0],
        "Machine":           platform.machine(),
        "Processor":         platform.processor() or "—",
    }
    # Site packages
    sp_list = []
    try:
        sp_list = site.getsitepackages()
    except Exception:
        pass
    try:
        sp_list.append(site.getusersitepackages())
    except Exception:
        pass
    info["Site-packages dirs"] = "\n   ".join(sp_list) if sp_list else "—"

    # pip version
    try:
        r = subprocess.run([sys.executable,"-m","pip","--version"],
                           capture_output=True, text=True, timeout=10)
        info["Pip version"] = r.stdout.strip()
    except Exception:
        info["Pip version"] = "—"

    # sys.path
    info["sys.path"] = "\n   ".join(p for p in sys.path if p)

    # env vars
    for ev in ["PYTHONPATH","VIRTUAL_ENV","CONDA_DEFAULT_ENV","PYTHONHOME"]:
        v = os.environ.get(ev)
        if v:
            info[ev] = v
    return info


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

TYPE_COLOR = {
    "pip":        C["blue"],
    "stdlib":     C["green"],
    "builtin":    C["amber"],
    "executable": C["teal"],
}
TYPE_BG = {
    "pip":        C["blue_dim"],
    "stdlib":     C["green_dim"],
    "builtin":    C["amber_dim"],
    "executable": C["teal_dim"],
}


def open_path(path):
    if not path or path in ("—","built-in","C extension (built-in)"): return
    target = path if os.path.isdir(path) else os.path.dirname(path)
    if not os.path.isdir(target):
        messagebox.showinfo("Not found", f"Path does not exist:\n{target}")
        return
    try:
        if IS_WIN:   os.startfile(target)
        elif IS_MAC: subprocess.run(["open", target])
        else:        subprocess.run(["xdg-open", target])
    except Exception as e:
        messagebox.showerror("Error", str(e))


# ═══════════════════════════════════════════════════════════
#  CUSTOM WIDGETS
# ═══════════════════════════════════════════════════════════

class DarkButton(tk.Label):
    def __init__(self, parent, text, command=None, color=None, small=False, **kw):
        self._color   = color or C["blue"]
        self._command = command
        bg = kw.pop("bg", C["bg3"])
        font = FONT_SM if small else FONT_UI
        super().__init__(parent, text=text, font=font,
                         fg=self._color, bg=bg,
                         cursor="hand2",
                         padx=kw.pop("padx",10), pady=kw.pop("pady",5),
                         relief="flat", bd=0, **kw)
        self.bind("<Enter>",    self._hover_on)
        self.bind("<Leave>",    self._hover_off)
        self.bind("<Button-1>", self._click)

    def _hover_on(self, e):  self.config(bg=C["bg4"])
    def _hover_off(self, e): self.config(bg=self.master.cget("bg") if hasattr(self.master,"cget") else C["bg3"])
    def _click(self, e):
        if self._command: self._command()


class SearchEntry(tk.Frame):
    def __init__(self, parent, textvariable, **kw):
        super().__init__(parent, bg=C["bg2"],
                         highlightbackground=C["border"], highlightthickness=1,
                         **kw)
        self._icon = tk.Label(self, text="⌕", font=("Consolas",14),
                              fg=C["text2"], bg=C["bg2"])
        self._icon.pack(side="left", padx=(8,2))
        self._entry = tk.Entry(self, textvariable=textvariable,
                               font=FONT_MONO2, fg=C["text0"], bg=C["bg2"],
                               insertbackground=C["blue"],
                               relief="flat", bd=0)
        self._entry.pack(side="left", fill="x", expand=True, pady=7, padx=(0,8))
        self._entry.bind("<FocusIn>",  lambda e: self.config(highlightbackground=C["blue"]))
        self._entry.bind("<FocusOut>", lambda e: self.config(highlightbackground=C["border"]))


# ═══════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Package & Library Scanner")
        self.geometry("1340x820")
        self.minsize(950, 600)
        self.configure(bg=C["bg0"])

        # Data
        self.pip_data   = []
        self.stdlib_data= []
        self.exec_data  = []
        self._all_data  = []
        self._sorted    = []
        self._sel_item  = None
        self._tab       = "pip"
        self._sort_col  = "name"
        self._sort_asc  = True
        self._loading   = False

        self._build()
        self._start_scan()

    # ──────────────────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────────────────

    def _build(self):
        self._build_topbar()
        self._build_tabbar()
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        self._build_toolbar()
        self._build_body()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=C["bg2"], height=56)
        bar.pack(fill="x"); bar.pack_propagate(False)

        # Logo + title
        logo_frame = tk.Frame(bar, bg=C["bg2"])
        logo_frame.pack(side="left", padx=(18,0))
        tk.Label(logo_frame, text="◈", font=("Consolas",22),
                 fg=C["blue"], bg=C["bg2"]).pack(side="left")
        tk.Label(logo_frame, text=" Python Package Scanner",
                 font=FONT_LG, fg=C["text0"], bg=C["bg2"]).pack(side="left", padx=6)

        self._status = tk.Label(bar, text="Initializing…",
                                font=FONT_MONO3, fg=C["text2"], bg=C["bg2"])
        self._status.pack(side="left", padx=20)

        # Right buttons
        right = tk.Frame(bar, bg=C["bg2"])
        right.pack(side="right", padx=12)
        for label, cmd in [("↺ Refresh", self._start_scan),
                            ("⬇ CSV",    self._export_csv),
                            ("⬇ JSON",   self._export_json)]:
            DarkButton(right, label, cmd, bg=C["bg2"],
                       color=C["blue"] if "Refresh" in label else C["text1"],
                       padx=14, pady=8).pack(side="left", padx=3)

    def _build_tabbar(self):
        bar = tk.Frame(self, bg=C["bg2"], height=38)
        bar.pack(fill="x"); bar.pack_propagate(False)

        self._tab_btns = {}
        tabs = [
            ("pip",        "Pip Packages",   C["blue"]),
            ("stdlib",     "Stdlib Modules", C["green"]),
            ("builtin",    "Built-ins",      C["amber"]),
            ("executable", "Executables",    C["teal"]),
            ("all",        "All",            C["pink"]),
            ("info",       "Environment",    C["text1"]),
        ]
        for key, label, color in tabs:
            btn = tk.Label(bar, text=label, font=FONT_UI_B if key==self._tab else FONT_UI,
                           fg=color if key==self._tab else C["text2"],
                           bg=C["bg2"], cursor="hand2",
                           padx=16, pady=0)
            btn.pack(side="left", fill="y")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            btn.bind("<Enter>",    lambda e, b=btn, c=color: b.config(fg=c))
            btn.bind("<Leave>",    lambda e, b=btn, k=key, c=color: b.config(
                fg=c if k==self._tab else C["text2"]))
            self._tab_btns[key] = (btn, color)

        # Active underline
        self._tab_line = tk.Frame(bar, bg=C["blue"], height=2, width=80)
        self._tab_line.place(x=0, y=36)

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=C["bg1"], pady=6)
        bar.pack(fill="x", padx=0)

        inner = tk.Frame(bar, bg=C["bg1"])
        inner.pack(fill="x", padx=16)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        SearchEntry(inner, self._search_var).pack(side="left", fill="x", expand=True)

        # Field filter
        tk.Label(inner, text="in", font=FONT_UI, fg=C["text2"], bg=C["bg1"]).pack(side="left", padx=(8,4))
        self._field_var = tk.StringVar(value="name")
        field_menu = tk.OptionMenu(inner, self._field_var,
                                   "name", "version", "location", "summary",
                                   command=lambda *_: self._filter())
        field_menu.config(font=FONT_UI, fg=C["text1"], bg=C["bg3"],
                          activebackground=C["bg4"], activeforeground=C["text0"],
                          relief="flat", bd=0, highlightthickness=0, padx=8)
        field_menu["menu"].config(bg=C["bg3"], fg=C["text0"],
                                  activebackground=C["bg4"], font=FONT_UI)
        field_menu.pack(side="left", padx=4)

        tk.Frame(inner, bg=C["border"], width=1, height=24).pack(side="left", padx=8)

        self._match_lbl = tk.Label(inner, text="", font=FONT_MONO3,
                                    fg=C["text2"], bg=C["bg1"])
        self._match_lbl.pack(side="left")

        self._count_lbl = tk.Label(inner, text="", font=FONT_UI_B,
                                    fg=C["blue"], bg=C["bg1"])
        self._count_lbl.pack(side="right")

    def _build_body(self):
        # Stats row
        self._stats_frame = tk.Frame(self, bg=C["bg0"])
        self._stats_frame.pack(fill="x", padx=16, pady=(8,4))
        self._stat_cards = {}
        for key, label, color in [
            ("pip",   "Pip",        C["blue"]),
            ("stdlib","Stdlib",     C["green"]),
            ("builtin","Built-ins", C["amber"]),
            ("executable","Execs",  C["teal"]),
        ]:
            f = tk.Frame(self._stats_frame, bg=C["bg2"],
                         highlightbackground=color, highlightthickness=1)
            f.pack(side="left", padx=(0,8), ipadx=16, ipady=8)
            tk.Label(f, text=label, font=FONT_SM, fg=color, bg=C["bg2"]).pack()
            n = tk.Label(f, text="—", font=FONT_XL, fg=C["text0"], bg=C["bg2"])
            n.pack()
            self._stat_cards[key] = n

        # Main pane
        pane = tk.PanedWindow(self, orient="horizontal", bg=C["bg0"],
                               sashwidth=5, sashrelief="flat",
                               sashpad=0, handlesize=0)
        pane.pack(fill="both", expand=True, padx=0, pady=(4,0))

        # Left: table
        left = tk.Frame(pane, bg=C["bg1"])
        pane.add(left, minsize=550, width=900)

        # Column headers
        self._hdr = tk.Frame(left, bg=C["bg2"])
        self._hdr.pack(fill="x")

        cols_def = [
            ("name",    "Package / Module",  26),
            ("version", "Version",            9),
            ("type",    "Type",               8),
            ("size",    "Size",               7),
            ("location","Location / Path",    0),   # 0 = expand
        ]
        self._col_frames = {}
        for col, label, w in cols_def:
            f = tk.Frame(self._hdr, bg=C["bg2"])
            if w == 0:
                f.pack(side="left", fill="both", expand=True)
            else:
                f.pack(side="left", fill="y")
                f.config(width=w*8); f.pack_propagate(False)
            btn = tk.Label(f, text=label+" ↕", font=FONT_MONO3,
                           fg=C["text2"], bg=C["bg2"],
                           cursor="hand2", padx=8, pady=7, anchor="w")
            btn.pack(fill="both", expand=True)
            btn.bind("<Button-1>", lambda e, c=col: self._sort(c))
            btn.bind("<Enter>",    lambda e, b=btn: b.config(fg=C["text1"]))
            btn.bind("<Leave>",    lambda e, b=btn: b.config(fg=C["text2"]))
            self._col_frames[col] = btn

        tk.Frame(left, bg=C["border"], height=1).pack(fill="x")

        # Treeview
        style = ttk.Style()
        style.theme_use("default")
        for s in ["Dark.Treeview", "Dark.Treeview.Heading"]:
            style.configure(s, background=C["bg1"], fieldbackground=C["bg1"],
                            foreground=C["text0"], rowheight=30,
                            borderwidth=0, relief="flat", font=FONT_MONO)
        style.configure("Dark.Treeview.Heading",
                        background=C["bg2"], foreground=C["text2"],
                        font=FONT_MONO3)
        style.map("Dark.Treeview",
                  background=[("selected", C["bg4"])],
                  foreground=[("selected", C["text0"])])
        style.layout("Dark.Treeview",
                     [("Dark.Treeview.treearea", {"sticky":"nswe"})])

        tw = tk.Frame(left, bg=C["bg1"])
        tw.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tw,
            columns=("version","type","size","location"),
            show="tree headings",
            style="Dark.Treeview",
            selectmode="browse")
        self.tree.heading("#0",       text="Name",     anchor="w")
        self.tree.heading("version",  text="Version",  anchor="w")
        self.tree.heading("type",     text="Type",     anchor="w")
        self.tree.heading("size",     text="Size",     anchor="w")
        self.tree.heading("location", text="Location", anchor="w")
        self.tree.column("#0",       width=220, minwidth=120, stretch=False)
        self.tree.column("version",  width=90,  minwidth=60,  stretch=False)
        self.tree.column("type",     width=80,  minwidth=60,  stretch=False)
        self.tree.column("size",     width=70,  minwidth=50,  stretch=False)
        self.tree.column("location", width=400, minwidth=200, stretch=True)

        for t in TYPE_COLOR:
            self.tree.tag_configure(t, foreground=TYPE_COLOR[t])
        self.tree.tag_configure("row_odd",  background="#0A1018")
        self.tree.tag_configure("row_even", background=C["bg1"])

        vsb = ttk.Scrollbar(tw, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tw, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",          self._on_double_click)

        # Right: detail panel
        right = tk.Frame(pane, bg=C["bg2"])
        pane.add(right, minsize=260, width=340)
        self._build_detail(right)

        # Info tab (hidden layer)
        self._info_outer = tk.Frame(self, bg=C["bg1"])
        self._info_text  = tk.Text(self._info_outer, font=FONT_MONO,
                                    fg=C["text0"], bg=C["bg1"],
                                    insertbackground=C["blue"],
                                    relief="flat", bd=0,
                                    padx=20, pady=16, state="disabled")
        info_vsb = ttk.Scrollbar(self._info_outer, orient="vertical",
                                  command=self._info_text.yview)
        self._info_text.configure(yscrollcommand=info_vsb.set)
        info_vsb.pack(side="right", fill="y")
        self._info_text.pack(fill="both", expand=True)

        # Loading overlay
        self._loading_frame = tk.Frame(self, bg=C["bg1"])
        tk.Label(self._loading_frame, text="◈", font=("Consolas",48),
                 fg=C["blue"], bg=C["bg1"]).pack(expand=True)
        self._loading_lbl = tk.Label(self._loading_frame,
                                      text="Scanning packages…",
                                      font=FONT_LG, fg=C["text1"], bg=C["bg1"])
        self._loading_lbl.pack()
        tk.Label(self._loading_frame,
                 text="This may take a few seconds",
                 font=FONT_UI, fg=C["text2"], bg=C["bg1"]).pack(pady=4)
        self._loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _build_detail(self, parent):
        parent.config(highlightbackground=C["border"], highlightthickness=1)

        # Scrollable content
        canvas = tk.Canvas(parent, bg=C["bg2"], bd=0,
                           highlightthickness=0)
        vsb    = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = tk.Frame(canvas, bg=C["bg2"])
        win_id = canvas.create_window((0,0), window=scroll_frame, anchor="nw")
        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win_id, width=e.width))

        p = scroll_frame  # shorthand

        # Section header
        tk.Label(p, text="PACKAGE DETAILS", font=FONT_SM,
                 fg=C["text3"], bg=C["bg2"]).pack(anchor="w", padx=16, pady=(14,4))
        tk.Frame(p, bg=C["border"], height=1).pack(fill="x", padx=16)

        # Name + badge
        name_row = tk.Frame(p, bg=C["bg2"])
        name_row.pack(fill="x", padx=16, pady=(14,0))
        self._d_name  = tk.Label(name_row, text="Select a package",
                                  font=FONT_LG, fg=C["text1"], bg=C["bg2"],
                                  wraplength=220, justify="left", anchor="w")
        self._d_name.pack(side="left")
        self._d_type_badge = tk.Label(name_row, text="", font=FONT_SM,
                                       fg=C["bg0"], bg=C["bg3"],
                                       padx=6, pady=2)
        self._d_type_badge.pack(side="right", anchor="n", pady=4)

        self._d_ver = tk.Label(p, text="", font=FONT_MONO2,
                                fg=C["green"], bg=C["bg2"])
        self._d_ver.pack(anchor="w", padx=16, pady=(2,0))

        self._d_summary = tk.Label(p, text="", font=FONT_UI,
                                    fg=C["text1"], bg=C["bg2"],
                                    wraplength=270, justify="left")
        self._d_summary.pack(anchor="w", padx=16, pady=(6,0))

        tk.Frame(p, bg=C["border"], height=1).pack(fill="x", padx=16, pady=12)

        # Detail rows
        self._d_fields = {}
        fields = [
            ("Location", "Install path (.py / .so file)"),
            ("Folder",   "Package folder"),
            ("Size",     "Disk usage"),
            ("Requires", "Dependencies"),
            ("Homepage", "Homepage URL"),
        ]
        for key, hint in fields:
            tk.Label(p, text=key.upper(), font=FONT_SM,
                     fg=C["text3"], bg=C["bg2"]).pack(anchor="w", padx=16, pady=(8,0))
            lbl = tk.Label(p, text="—", font=FONT_MONO3,
                           fg=C["text1"], bg=C["bg2"],
                           wraplength=260, justify="left", anchor="w")
            lbl.pack(anchor="w", padx=16)
            self._d_fields[key] = lbl

        tk.Frame(p, bg=C["border"], height=1).pack(fill="x", padx=16, pady=12)

        # Action buttons
        btn_frame = tk.Frame(p, bg=C["bg2"])
        btn_frame.pack(fill="x", padx=16)
        self._btn_open = tk.Button(btn_frame, text="📂  Open Folder",
                                    font=FONT_UI, fg=C["text0"], bg=C["bg3"],
                                    activebackground=C["bg4"],
                                    activeforeground=C["text0"],
                                    relief="flat", bd=0, padx=12, pady=8,
                                    cursor="hand2",
                                    command=lambda: open_path(
                                        self._sel_item.get("folder","") if self._sel_item else ""))
        self._btn_open.pack(fill="x", pady=(0,4))

        self._btn_copy = tk.Button(btn_frame, text="⎘  Copy Path",
                                    font=FONT_UI, fg=C["text1"], bg=C["bg2"],
                                    activebackground=C["bg3"],
                                    activeforeground=C["text0"],
                                    relief="flat", bd=0, padx=12, pady=8,
                                    cursor="hand2",
                                    command=self._copy_path)
        self._btn_copy.pack(fill="x", pady=(0,4))

        self._btn_pip  = tk.Button(btn_frame, text="⬆  pip show (terminal)",
                                    font=FONT_UI, fg=C["text1"], bg=C["bg2"],
                                    activebackground=C["bg3"],
                                    activeforeground=C["text0"],
                                    relief="flat", bd=0, padx=12, pady=8,
                                    cursor="hand2",
                                    command=self._run_pip_show)
        self._btn_pip.pack(fill="x")

    # ──────────────────────────────────────────────────────
    # SCANNING
    # ──────────────────────────────────────────────────────

    def _start_scan(self):
        if self._loading: return
        self._loading = True
        self._loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._loading_frame.lift()
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        self.after(0, lambda: self._loading_lbl.config(text="Scanning pip packages…"))
        self.pip_data    = get_pip_packages()
        self.after(0, lambda: self._loading_lbl.config(text="Scanning stdlib modules…"))
        self.stdlib_data = get_stdlib_modules()
        self.after(0, lambda: self._loading_lbl.config(text="Scanning executables…"))
        self.exec_data   = get_executables()
        self._all_data   = self.pip_data + self.stdlib_data + self.exec_data
        self.after(0, self._scan_done)

    def _scan_done(self):
        self._loading = False
        self._loading_frame.place_forget()
        # Update stat cards
        self._stat_cards["pip"].config(text=str(len(self.pip_data)))
        stdlib_count = len([d for d in self.stdlib_data if d["type"]=="stdlib"])
        self._stat_cards["stdlib"].config(text=str(stdlib_count))
        builtin_count= len([d for d in self.stdlib_data if d["type"]=="builtin"])
        self._stat_cards["builtin"].config(text=str(builtin_count))
        self._stat_cards["executable"].config(text=str(len(self.exec_data)))

        ts = f"{len(self._all_data)} total items scanned at {datetime.now().strftime('%H:%M:%S')}"
        self._status.config(text=ts)
        self._switch_tab(self._tab)

    # ──────────────────────────────────────────────────────
    # TABS
    # ──────────────────────────────────────────────────────

    def _switch_tab(self, tab):
        self._tab = tab
        # Update tab labels
        for k, (btn, color) in self._tab_btns.items():
            if k == tab:
                btn.config(fg=color, font=FONT_UI_B)
            else:
                btn.config(fg=C["text2"], font=FONT_UI)

        self._info_outer.pack_forget()

        if tab == "info":
            self._info_outer.pack(fill="both", expand=True)
            self._render_info()
            return

        if tab == "pip":        data = self.pip_data
        elif tab == "stdlib":   data = [d for d in self.stdlib_data if d["type"]=="stdlib"]
        elif tab == "builtin":  data = [d for d in self.stdlib_data if d["type"]=="builtin"]
        elif tab == "executable": data = self.exec_data
        else:                   data = self._all_data

        self._current_data = data
        self._filter()

    def _render_info(self):
        info = get_site_info()
        self._info_text.config(state="normal")
        self._info_text.delete("1.0", "end")
        for k, v in info.items():
            self._info_text.insert("end", f"\n{k}\n", "key")
            self._info_text.insert("end", f"   {v}\n", "val")
            self._info_text.insert("end", "─"*60 + "\n", "dim")
        self._info_text.tag_configure("key",
            foreground=C["blue"],
            font=("Consolas",11,"bold") if IS_WIN else ("Menlo",11,"bold"))
        self._info_text.tag_configure("val",  foreground=C["text0"])
        self._info_text.tag_configure("dim",  foreground=C["text3"])
        self._info_text.config(state="disabled")

    # ──────────────────────────────────────────────────────
    # FILTER / SORT / POPULATE
    # ──────────────────────────────────────────────────────

    def _filter(self):
        if not hasattr(self, "_current_data"): return
        q     = self._search_var.get().strip().lower()
        field = self._field_var.get()
        data  = self._current_data

        if q:
            if field == "name":
                data = [d for d in data if q in d["name"].lower()]
            elif field == "version":
                data = [d for d in data if q in d["version"].lower()]
            elif field == "location":
                data = [d for d in data if q in d["location"].lower()]
            elif field == "summary":
                data = [d for d in data if q in d["summary"].lower()]

        if q:
            self._match_lbl.config(
                text=f"{len(data)} match{'es' if len(data)!=1 else ''} · ")
        else:
            self._match_lbl.config(text="")

        self._count_lbl.config(text=f"{len(data)} items")
        self._populate(data)

    def _sort(self, col):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        arrow = " ↑" if self._sort_asc else " ↓"
        for c, btn in self._col_frames.items():
            base = btn.cget("text").rstrip("↑↓↕ ")
            btn.config(text=base + (arrow if c == col else " ↕"))
        self._filter()

    def _populate(self, data):
        self.tree.delete(*self.tree.get_children())
        sorted_data = sorted(data,
                             key=lambda x: (x.get(self._sort_col) or "").lower(),
                             reverse=not self._sort_asc)
        self._sorted = sorted_data
        for i, d in enumerate(sorted_data):
            tag  = d["type"]
            row  = "row_odd" if i % 2 else "row_even"
            self.tree.insert("", "end", iid=str(i),
                              text=d["name"],
                              values=(d["version"], d["type"],
                                      d["size"], d["location"]),
                              tags=(tag, row))

    # ──────────────────────────────────────────────────────
    # SELECTION
    # ──────────────────────────────────────────────────────

    def _on_select(self, e):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        if idx < len(self._sorted):
            d = self._sorted[idx]
            self._sel_item = d
            self._d_name.config(text=d["name"], fg=TYPE_COLOR.get(d["type"], C["text0"]))
            self._d_ver.config(text=f"v{d['version']}" if d["version"] else "")
            tc = TYPE_COLOR.get(d["type"], C["text1"])
            self._d_type_badge.config(text=d["type"].upper(), fg=C["bg0"], bg=tc)
            self._d_summary.config(text=d["summary"] or "No description available.")
            self._d_fields["Location"].config(text=d["location"] or "—")
            self._d_fields["Folder"].config(text=d["folder"] or "—")
            self._d_fields["Size"].config(text=d["size"] or "—")
            self._d_fields["Requires"].config(text=d["requires"] or "—")
            self._d_fields["Homepage"].config(text=d["homepage"] or "—")

    def _on_double_click(self, e):
        if self._sel_item:
            open_path(self._sel_item.get("folder",""))

    # ──────────────────────────────────────────────────────
    # ACTIONS
    # ──────────────────────────────────────────────────────

    def _copy_path(self):
        if not self._sel_item: return
        path = self._sel_item.get("folder") or self._sel_item.get("location","")
        self.clipboard_clear()
        self.clipboard_append(path)
        self._btn_copy.config(text="✓  Copied!", fg=C["green"])
        self.after(1800, lambda: self._btn_copy.config(text="⎘  Copy Path", fg=C["text1"]))

    def _run_pip_show(self):
        if not self._sel_item: return
        name = self._sel_item["name"]
        try:
            r = subprocess.run([sys.executable,"-m","pip","show",name],
                               capture_output=True, text=True, timeout=10)
            win = tk.Toplevel(self)
            win.title(f"pip show {name}")
            win.configure(bg=C["bg1"])
            win.geometry("600x400")
            t = tk.Text(win, font=FONT_MONO2, fg=C["text0"], bg=C["bg1"],
                        relief="flat", bd=0, padx=16, pady=12)
            t.pack(fill="both", expand=True)
            t.insert("end", r.stdout or r.stderr or "No output")
            t.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ──────────────────────────────────────────────────────
    # EXPORT
    # ──────────────────────────────────────────────────────

    def _get_data(self):
        return getattr(self, "_current_data", self._all_data)

    def _export_csv(self):
        data = self._get_data()
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")],
            initialfile=f"python_packages_{ts}.csv")
        if not path: return
        fields = ["name","version","type","location","folder","size","summary","homepage","requires"]
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
        messagebox.showinfo("Exported", f"Saved {len(data)} rows to:\n{path}")

    def _export_json(self):
        data = self._get_data()
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files","*.json")],
            initialfile=f"python_packages_{ts}.json")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exported", f"Saved {len(data)} entries to:\n{path}")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()