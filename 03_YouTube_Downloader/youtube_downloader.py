"""
YTDROP PRO — Premium YouTube Downloader

INSTALL:
    pip install customtkinter yt-dlp Pillow requests

FOR 1080p/4K:
    winget install ffmpeg   (restart app after install)

RUN:
    python youtube_downloader.py
"""

import customtkinter as ctk
import yt_dlp
import threading
import os
import re
import ssl
import sys
import time
import shutil
import subprocess
import requests
import urllib3
from PIL import Image
from io import BytesIO
from tkinter import filedialog, messagebox

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# LUXURY OBSIDIAN PALETTE
# ---------------------------------------------------------------------------
P = {
    "bg":           "#050505",      # Pitch sleek black
    "bg2":          "#0a0a0a",      # Slightly lighter back
    "card":         "#121212",      # Metal slate card
    "card2":        "#181818",
    "surface":      "#1f1f1f",      # Surface interactions
    "hover":        "#2c2c2e",      # Hover slate
    "border":       "#2c2c2e",      # Subtle borders 
    "border_hi":    "#3a3a3c",
    "accent":       "#0a84ff",      # Apple System Blue
    "accent_hi":    "#409cff",
    "accent_dim":   "#002A5A",
    "accent2":      "#5e5ce6",      # System indigo
    "success":      "#32d74b",      # Emerald
    "success_dim":  "#0f3d1b",
    "warn":         "#ff9f0a",
    "warn_dim":     "#3b2300",
    "error":        "#ff453a",
    "error_dim":    "#4a0e0b",
    "cyan":         "#64d2ff",
    "pink":         "#ff375f",
    "white":        "#ffffff",
    "text":         "#ebebf5",
    "text2":        "#c7c7cc",      # Standard secondary
    "text3":        "#8e8e93",      # Frosted grey
    "dim":          "#636366",
}

# ---------------------------------------------------------------------------
# FFmpeg
# ---------------------------------------------------------------------------
def _find_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    local = os.environ.get("LOCALAPPDATA", "")
    user  = os.path.expanduser("~")
    cf    = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # winget packages
    wr = os.path.join(local, "Microsoft", "WinGet", "Packages")
    if os.path.isdir(wr):
        for dp, dn, fn in os.walk(wr):
            if dp[len(wr):].count(os.sep) > 5:
                dn.clear(); continue
            if "ffmpeg.exe" in fn:
                c = os.path.join(dp, "ffmpeg.exe")
                try:
                    if subprocess.run([c, "-version"], capture_output=True, timeout=5,
                                      creationflags=cf).returncode == 0:
                        return c
                except Exception:
                    pass

    # WindowsApps
    wa = os.path.join(local, "Microsoft", "WindowsApps", "ffmpeg.exe")
    if os.path.isfile(wa):
        try:
            if subprocess.run([wa, "-version"], capture_output=True, timeout=5,
                              creationflags=cf).returncode == 0:
                return wa
        except Exception:
            pass

    # common paths
    for c in [
        os.path.join("C:\\", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join("C:\\", "Program Files", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(user, "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(user, "scoop", "apps", "ffmpeg", "current", "bin", "ffmpeg.exe"),
        os.path.join("C:\\", "ProgramData", "chocolatey", "bin", "ffmpeg.exe"),
    ]:
        if os.path.isfile(c):
            try:
                if subprocess.run([c, "-version"], capture_output=True, timeout=5,
                                  creationflags=cf).returncode == 0:
                    return c
            except Exception:
                pass
    return None

FFMPEG_PATH = _find_ffmpeg()
FFMPEG_OK   = FFMPEG_PATH is not None

CLIENTS = [["tv_embedded"], ["web_embedded"], ["ios"], ["android"], ["mweb"], ["web"]]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt_bytes(b):
    if not b:
        return "—"
    if b >= 1_073_741_824:
        return f"{b / 1_073_741_824:.2f} GB"
    if b >= 1_048_576:
        return f"{b / 1_048_576:.1f} MB"
    return f"{b / 1024:.0f} KB"


def fmt_dur(s):
    if not s:
        return "0:00"
    s = int(s)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def clean(n):
    return re.sub(r'[\\/*?:"<>|]', "_", n)[:80]


def drive_info(path):
    try:
        t, u, f = shutil.disk_usage(path)
        return t, u, f
    except Exception:
        return None, None, None


def base_opts(extra=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "color": "no_color",
        "socket_timeout": 30,
        "retries": 5,
        "abort_on_unavailable_fragments": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if FFMPEG_PATH:
        opts["ffmpeg_location"] = os.path.dirname(FFMPEG_PATH)
    if extra:
        opts.update(extra)
    return opts


def fetch_robust(url):
    last = None
    for client in CLIENTS:
        opts = base_opts({"extractor_args": {"youtube": {"player_client": client}}})
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info and info.get("title"):
                return info, client[0]
        except Exception as e:
            last = e
    try:
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
        if info and info.get("title"):
            return info, "default"
    except Exception as e:
        last = e
    raise last or Exception("All extraction strategies failed.")


QUAL = {
    2160: ("4K Ultra HD",   "4K",  P["warn"]),
    1440: ("2K QHD",        "2K",  P["warn"]),
    1080: ("1080p Full HD", "FHD", P["accent"]),
    720:  ("720p HD",       "HD",  P["cyan"]),
    480:  ("480p SD",       "SD",  P["text2"]),
    360:  ("360p",          "360", P["text3"]),
    240:  ("240p",          "240", P["dim"]),
    144:  ("144p",          "144", P["dim"]),
}


def extract_formats(info):
    """
    Build downloadable format list.

    KEY FIX FOR 1080p+ BLACK SCREEN:
    ─────────────────────────────────
    YouTube serves 1080p+ as VIDEO-ONLY (no audio).
    They MUST be merged with a separate audio stream via FFmpeg.

    With FFmpeg: use  bestvideo+bestaudio  →  merge into MP4
    Without FFmpeg: ONLY offer combined streams (video+audio in one file)
                    to prevent broken/black-screen downloads.
    """
    out, seen = [], set()
    fmts = info.get("formats", [])

    all_video  = [f for f in fmts if f.get("vcodec", "none") != "none" and f.get("height")]
    combined   = [f for f in all_video if f.get("acodec", "none") != "none"]
    video_only = [f for f in all_video if f.get("acodec", "none") == "none"]
    audio_only = sorted(
        [f for f in fmts
         if f.get("vcodec", "none") == "none"
         and f.get("acodec", "none") != "none"],
        key=lambda x: x.get("abr", 0) or 0, reverse=True,
    )
    best_audio_id = audio_only[0]["format_id"] if audio_only else "bestaudio"

    # Group best streams per resolution
    combined_by_h = {}
    for f in sorted(combined, key=lambda x: (x.get("height", 0), x.get("tbr", 0) or 0), reverse=True):
        h = f.get("height", 0)
        if h not in combined_by_h:
            combined_by_h[h] = f

    vidonly_by_h = {}
    for f in sorted(video_only, key=lambda x: (x.get("height", 0), x.get("tbr", 0) or 0), reverse=True):
        h = f.get("height", 0)
        if h not in vidonly_by_h:
            vidonly_by_h[h] = f

    all_heights = sorted(set(list(combined_by_h) + list(vidonly_by_h)), reverse=True)

    for h in all_heights:
        if h not in QUAL or h in seen:
            continue
        label, badge, color = QUAL[h]
        cf = combined_by_h.get(h)
        vf = vidonly_by_h.get(h)

        if FFMPEG_OK:
            # ── WITH FFMPEG: prefer video-only + best audio (higher quality) ──
            # Use yt-dlp's built-in merge to combine them into mp4
            if vf:
                best_f = vf
                # The format string tells yt-dlp to:
                # 1. Try specific video + best audio
                # 2. Fall back to best video at this height + best audio
                # 3. Final fallback to best combined stream
                fmt_str = (
                    f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                    f"/bestvideo[height<={h}]+bestaudio"
                    f"/best[height<={h}]"
                )
            elif cf:
                best_f = cf
                fmt_str = f"best[height<={h}][ext=mp4]/best[height<={h}]"
            else:
                continue
        else:
            # ── WITHOUT FFMPEG: ONLY combined streams ──
            # Video-only streams produce BLACK SCREEN without merge
            if cf:
                best_f = cf
                fmt_str = (
                    f"best[height<={h}][ext=mp4]"
                    f"/best[height<={h}]"
                )
            else:
                continue  # skip — no usable stream without ffmpeg

        fps    = best_f.get("fps", 0) or 0
        vcodec = (best_f.get("vcodec") or "")[:12]
        size   = fmt_bytes(best_f.get("filesize") or best_f.get("filesize_approx"))
        tbr    = best_f.get("tbr", 0) or 0

        seen.add(h)
        out.append({
            "type": "video", "label": label, "badge": badge, "color": color,
            "fps": f"{fps:.0f} fps" if fps else "",
            "bitrate": f"{tbr:.0f} kbps" if tbr else "",
            "size": size, "format_str": fmt_str, "height": h,
            "vcodec": vcodec,
        })

    # Audio formats
    seen_ext = set()
    for f in audio_only:
        ext = f.get("ext", "m4a")
        if ext in seen_ext:
            continue
        seen_ext.add(ext)
        out.append({
            "type": "audio", "label": f"Audio · {ext.upper()}", "badge": ext.upper(),
            "color": P["pink"], "fps": "",
            "bitrate": f"{f.get('abr', 0) or 0:.0f} kbps" if f.get("abr") else "",
            "size": fmt_bytes(f.get("filesize") or f.get("filesize_approx")),
            "format_str": f.get("format_id", "bestaudio"), "height": 0,
            "mp3": False,
        })

    # Best audio
    if FFMPEG_OK:
        out.append({
            "type": "audio", "label": "Audio · MP3 (Best)", "badge": "MP3",
            "color": P["pink"], "fps": "", "bitrate": "Best",
            "size": "~varies", "format_str": "bestaudio/best",
            "height": 0, "mp3": True,
        })
    else:
        out.append({
            "type": "audio", "label": "Audio · M4A (Best)", "badge": "M4A",
            "color": P["pink"], "fps": "", "bitrate": "Best",
            "size": "~varies", "format_str": "bestaudio[ext=m4a]/bestaudio",
            "height": 0, "mp3": False,
        })
    return out


def friendly(raw):
    r = raw.lower()
    if "ffmpeg" in r:
        return "FFmpeg is required for this format. Install: winget install ffmpeg"
    if "ssl" in r or "certificate" in r:
        return "SSL error — update yt-dlp: pip install -U yt-dlp"
    if "sign in" in r or "age" in r:
        return "Age-restricted content requires authentication"
    if "private" in r:
        return "This video is private"
    if "playback on other websites" in r:
        return "Video owner disabled external playback"
    if "unavailable" in r or "removed" in r:
        return "Video is unavailable or has been removed"
    if "requested format is not available" in r:
        return "Selected format unavailable — try a different quality"
    if "403" in r or "forbidden" in r:
        return "Request blocked by YouTube — update: pip install -U yt-dlp"
    return f"Error: {raw[:180]}"


# ===========================================================================
# MAIN APP — YTDROP PRO
# ===========================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YTDROP PRO — YouTube Downloader")
        self.geometry("820x720")
        self.minsize(700, 560)
        self.configure(fg_color=P["bg"])

        self._info       = None
        self._formats    = []
        self._sel        = None
        self._save_dir   = os.path.expanduser("~/Downloads")
        self._dl_active  = False
        self._fmt_btns   = []
        self._ci         = None  # thumbnail ref
        self._dl_start   = 0

        self._build()

    # ===================================================================
    # BUILD UI
    # ===================================================================
    def _build(self):
        # ── HEADER ──
        hdr = ctk.CTkFrame(self, fg_color=P["bg2"], corner_radius=0, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        hi = ctk.CTkFrame(hdr, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=20)

        # Logo
        ctk.CTkLabel(
            hi, text="▶ YTDROP",
            font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=P["accent_hi"],
        ).pack(side="left", pady=10)
        ctk.CTkLabel(
            hi, text=" PRO",
            font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=P["text3"],
        ).pack(side="left", pady=14)

        # FFmpeg badge
        if FFMPEG_OK:
            ft, fc, fb = "✓ FFmpeg", P["success"], P["success_dim"]
        else:
            ft, fc, fb = "✗ FFmpeg", P["warn"], P["warn_dim"]
        ff = ctk.CTkFrame(hi, fg_color=fb, corner_radius=6)
        ff.pack(side="right", pady=14)
        ctk.CTkLabel(ff, text=ft, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=fc).pack(padx=10, pady=3)

        self._status = ctk.CTkLabel(
            hi, text="Ready", font=ctk.CTkFont("Segoe UI", 11),
            text_color=P["text3"],
        )
        self._status.pack(side="right", padx=16)

        # Accent line
        ctk.CTkFrame(self, fg_color=P["accent"], height=2, corner_radius=0).pack(fill="x")

        # ── SCROLLABLE BODY ──
        self._body = ctk.CTkScrollableFrame(
            self, fg_color=P["bg"], corner_radius=0,
            scrollbar_fg_color=P["bg2"], scrollbar_button_color=P["dim"],
        )
        self._body.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_url_input()

        # Stable wrappers for ordered sections
        self._info_wrap = ctk.CTkFrame(self._body, fg_color="transparent")
        self._fmt_wrap  = ctk.CTkFrame(self._body, fg_color="transparent")
        self._dl_wrap   = ctk.CTkFrame(self._body, fg_color="transparent")
        self._info_wrap.pack(fill="x")
        self._fmt_wrap.pack(fill="x")
        self._dl_wrap.pack(fill="x")

    # ── Card helper ──
    def _card(self, parent, pad=(0, 10)):
        outer = ctk.CTkFrame(
            parent, fg_color=P["card"], corner_radius=12,
            border_width=1, border_color=P["border"],
        )
        outer.pack(fill="x", padx=16, pady=pad)
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)
        return inner

    def _section(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=P["text3"],
        ).pack(anchor="w", pady=(0, 8))

    # ===================================================================
    # URL INPUT
    # ===================================================================
    def _build_url_input(self):
        card = self._card(self._body, pad=(14, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x")

        self._url_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            row, textvariable=self._url_var,
            placeholder_text="Paste YouTube URL here...",
            height=46, corner_radius=10,
            fg_color=P["surface"], border_color=P["border"], border_width=1,
            text_color=P["white"], placeholder_text_color=P["dim"],
            font=ctk.CTkFont("Segoe UI", 13),
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._entry.bind("<Return>", lambda e: self._do_fetch())

        self._fbtn = ctk.CTkButton(
            row, text="Download", width=120, height=46, corner_radius=10,
            fg_color=P["accent"], hover_color=P["accent2"],
            text_color="white", font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._do_fetch,
        )
        self._fbtn.pack(side="right")

        # Utility
        brow = ctk.CTkFrame(card, fg_color="transparent")
        brow.pack(fill="x", pady=(8, 0))

        for text, cmd in [("📋  Paste", self._paste), ("✕  Clear", self._clear)]:
            ctk.CTkButton(
                brow, text=text, height=28, corner_radius=8,
                fg_color="transparent", hover_color=P["hover"],
                text_color=P["text3"], font=ctk.CTkFont("Segoe UI", 11),
                border_width=1, border_color=P["border"], command=cmd,
            ).pack(side="left", padx=(0, 6))

        self._msg = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont("Segoe UI", 11),
            text_color=P["text3"], wraplength=700, justify="left", anchor="w",
        )
        self._msg.pack(anchor="w", pady=(6, 0))

    def _paste(self):
        try:
            self._url_var.set(self.clipboard_get().strip())
        except Exception:
            pass

    def _clear(self):
        self._url_var.set("")
        self._msg.configure(text="")
        for wrap in (self._info_wrap, self._fmt_wrap, self._dl_wrap):
            for c in wrap.winfo_children():
                c.pack_forget()
        self._info = None
        self._formats = []
        self._sel = None
        self._status.configure(text="Ready", text_color=P["text3"])

    def _set_msg(self, txt, color=None):
        self._msg.configure(text=txt, text_color=color or P["text3"])

    # ===================================================================
    # FETCH
    # ===================================================================
    def _do_fetch(self):
        url = self._url_var.get().strip()
        if not url:
            self._set_msg("Please paste a YouTube URL", P["warn"])
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            self._set_msg("Please enter a valid YouTube URL", P["warn"])
            return

        self._fbtn.configure(text="Loading...", state="disabled", fg_color=P["surface"])
        self._status.configure(text="Fetching...", text_color=P["warn"])
        self._set_msg("Connecting to YouTube...", P["text3"])

        for wrap in (self._info_wrap, self._fmt_wrap, self._dl_wrap):
            for c in wrap.winfo_children():
                c.pack_forget()

        threading.Thread(target=self._fetch_th, args=(url,), daemon=True).start()

    def _fetch_th(self, url):
        try:
            info, client = fetch_robust(url)
            self._info = info
            self._formats = extract_formats(info)
            self.after(0, lambda: self._fetch_ok(client))
        except Exception as e:
            msg = friendly(str(e))
            self.after(0, lambda m=msg: self._fetch_fail(m))

    def _fetch_ok(self, client):
        self._fbtn.configure(text="Download", state="normal", fg_color=P["accent"])
        n = len(self._formats)
        self._status.configure(text=f"{n} formats found", text_color=P["success"])
        self._set_msg(f"✓  Video loaded — {n} download options available", P["success"])
        self._show_info()

    def _fetch_fail(self, msg):
        self._fbtn.configure(text="Download", state="normal", fg_color=P["accent"])
        self._status.configure(text="Failed", text_color=P["error"])
        self._set_msg(msg, P["error"])

    # ===================================================================
    # VIDEO INFO
    # ===================================================================
    def _show_info(self):
        # Clear old
        for c in self._info_wrap.winfo_children():
            c.pack_forget()

        card = self._card(self._info_wrap)
        info = self._info

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x")

        # Thumbnail
        thumb = ctk.CTkFrame(
            row, fg_color=P["surface"], corner_radius=10,
            width=192, height=108,
        )
        thumb.pack(side="left", padx=(0, 14))
        thumb.pack_propagate(False)
        ctk.CTkLabel(
            thumb, text="▶", font=ctk.CTkFont(size=28), text_color=P["dim"],
        ).place(relx=0.5, rely=0.5, anchor="center")

        t_url = info.get("thumbnail", "")
        if t_url:
            threading.Thread(target=self._load_thumb, args=(t_url, thumb), daemon=True).start()

        # Meta info
        meta = ctk.CTkFrame(row, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            meta, text=info.get("title", "Unknown"),
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=P["white"], wraplength=500, justify="left", anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        # Compact meta line
        dur = fmt_dur(info.get("duration"))
        uploader = info.get("uploader") or info.get("channel", "")
        views = info.get("view_count", 0)
        parts = [dur]
        if uploader:
            parts.append(uploader)
        if views:
            parts.append(f"{views:,} views")

        ctk.CTkLabel(
            meta, text="  ·  ".join(parts),
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["text2"],
        ).pack(anchor="w")

        self._show_formats()

    def _load_thumb(self, url, frame):
        try:
            r = requests.get(url, timeout=8, verify=False)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).resize((192, 108), Image.LANCZOS)
            ci = ctk.CTkImage(img, size=(192, 108))
            self._ci = ci
            lbl = ctk.CTkLabel(frame, image=ci, text="", corner_radius=10)
            self.after(0, lambda: lbl.place(relx=0, rely=0, relwidth=1, relheight=1))
        except Exception:
            pass

    # ===================================================================
    # FORMAT LIST
    # ===================================================================
    def _show_formats(self):
        for c in self._fmt_wrap.winfo_children():
            c.pack_forget()

        card = self._card(self._fmt_wrap)
        self._fmt_btns = []
        self._sel = None

        self._section(card, "SELECT QUALITY")

        if not FFMPEG_OK:
            warn = ctk.CTkFrame(card, fg_color=P["warn_dim"], corner_radius=8)
            warn.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                warn,
                text="⚠  FFmpeg not installed — 1080p+ may be limited. Install: winget install ffmpeg",
                font=ctk.CTkFont("Segoe UI", 10), text_color=P["warn"],
                wraplength=680, justify="left",
            ).pack(padx=12, pady=6, anchor="w")

        vfmts = [x for x in self._formats if x["type"] == "video"]
        afmts = [x for x in self._formats if x["type"] == "audio"]

        cols = 3

        if vfmts:
            vgrid = ctk.CTkFrame(card, fg_color="transparent")
            vgrid.pack(fill="x", pady=(4, 10))
            for i in range(cols):
                vgrid.grid_columnconfigure(i, weight=1)
            for i, fmt in enumerate(vfmts):
                self._fmt_box(vgrid, fmt, i // cols, i % cols)

        if afmts:
            self._section(card, "AUDIO ONLY")
            agrid = ctk.CTkFrame(card, fg_color="transparent")
            agrid.pack(fill="x", pady=(4, 10))
            for i in range(cols):
                agrid.grid_columnconfigure(i, weight=1)
            for i, fmt in enumerate(afmts):
                self._fmt_box(agrid, fmt, i // cols, i % cols)

        self._build_download()

    def _fmt_box(self, parent, fmt, r, c):
        fr = ctk.CTkFrame(
            parent, fg_color=P["surface"], corner_radius=10,
            border_width=1, border_color=P["border"], height=130
        )
        fr.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
        fr.grid_propagate(False)

        top_row = ctk.CTkFrame(fr, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(12, 0))

        badge = ctk.CTkLabel(
            top_row, text=f" {fmt['badge']} ",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color="white", fg_color=fmt["color"],
            corner_radius=4, height=22,
        )
        badge.pack(side="left")

        if fmt.get("vcodec"):
            ctk.CTkLabel(
                top_row, text=fmt["vcodec"],
                font=ctk.CTkFont("Segoe UI", 9), text_color=P["dim"],
            ).pack(side="right")

        ctk.CTkLabel(
            fr, text=fmt["label"],
            font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=P["white"],
        ).pack(anchor="w", padx=12, pady=(8, 2))

        parts = [p for p in [fmt.get("fps"), fmt.get("bitrate"), fmt.get("size")] if p and p != "—"]
        if parts:
            ctk.CTkLabel(
                fr, text=" • ".join(parts),
                font=ctk.CTkFont("Segoe UI", 11), text_color=P["text3"],
            ).pack(anchor="w", padx=12)

        btn = ctk.CTkButton(
            fr, text="Select", corner_radius=6,
            fg_color="transparent", border_width=1, border_color=P["border"],
            hover_color=P["hover"], text_color=P["text"],
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            height=28,
        )
        btn.pack(side="bottom", fill="x", padx=12, pady=12)
        btn.configure(command=lambda _f=fmt, _b=btn, _fr=fr: self._pick(_f, _b, _fr))
        self._fmt_btns.append((btn, fr))

    def _pick(self, f, b, fr):
        for btn, frame in self._fmt_btns:
            btn.configure(text="Select", fg_color="transparent",
                          text_color=P["text2"], border_color=P["border"])
            frame.configure(border_color=P["border"])

        self._sel = f
        b.configure(text="✓ Selected", fg_color=P["accent_dim"],
                    text_color=P["accent_hi"], border_color=P["accent"])
        fr.configure(border_color=P["accent"])

        ext = "MP4" if f["type"] == "video" else f.get("badge", "")
        self._dl_btn.configure(
            text=f"⬇  Download  ·  {f['label']}  [{ext}]",
            fg_color=P["accent"], hover_color=P["accent2"],
            text_color="white", state="normal",
        )

    # ===================================================================
    # DOWNLOAD PANEL
    # ===================================================================
    def _build_download(self):
        for c in self._dl_wrap.winfo_children():
            c.pack_forget()

        card = self._card(self._dl_wrap)
        self._section(card, "DOWNLOAD")

        # ── Save location row ──
        loc = ctk.CTkFrame(card, fg_color="transparent")
        loc.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            loc, text="Save to:",
            font=ctk.CTkFont("Segoe UI", 11), text_color=P["text2"],
        ).pack(side="left", padx=(0, 8))

        self._dir_var = ctk.StringVar(value=self._save_dir)
        ctk.CTkEntry(
            loc, textvariable=self._dir_var, height=32, corner_radius=8,
            fg_color=P["surface"], border_color=P["border"],
            text_color=P["text"], font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            loc, text="Browse", width=80, height=32, corner_radius=8,
            fg_color=P["surface"], hover_color=P["hover"],
            border_width=1, border_color=P["border"],
            text_color=P["text2"], font=ctk.CTkFont("Segoe UI", 10, "bold"),
            command=self._browse,
        ).pack(side="right")

        # Quick dirs
        qr = ctk.CTkFrame(card, fg_color="transparent")
        qr.pack(fill="x", pady=(0, 6))
        for label, path in [
            ("Downloads", os.path.expanduser("~/Downloads")),
            ("Desktop", os.path.expanduser("~/Desktop")),
            ("Videos", os.path.expanduser("~/Videos")),
        ]:
            if os.path.isdir(path):
                ctk.CTkButton(
                    qr, text=label, height=24, corner_radius=6,
                    fg_color="transparent", border_width=1, border_color=P["border"],
                    hover_color=P["hover"], text_color=P["text3"],
                    font=ctk.CTkFont("Segoe UI", 10),
                    command=lambda p=path: self._set_dir(p),
                ).pack(side="left", padx=(0, 4))

        # Drive info
        self._drive_lbl = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont("Segoe UI", 10), text_color=P["text3"],
        )
        self._drive_lbl.pack(anchor="w", pady=(0, 6))
        self._update_drive()

        # ── Progress area (hidden until download starts) ──
        self._prog_frame = ctk.CTkFrame(card, fg_color=P["surface"], corner_radius=10)

        # Download button
        self._dl_btn = ctk.CTkButton(
            card, text="⬇  Select a quality first",
            height=48, corner_radius=10,
            fg_color=P["surface"], hover_color=P["hover"],
            border_width=1, border_color=P["border"],
            text_color=P["dim"], state="disabled",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._start_dl,
        )
        self._dl_btn.pack(fill="x")

        # Open folder (hidden)
        self._open_btn = ctk.CTkButton(
            card, text="📂  Open folder", height=36, corner_radius=8,
            fg_color="transparent", hover_color=P["hover"],
            border_width=1, border_color=P["success"],
            text_color=P["success"], font=ctk.CTkFont("Segoe UI", 11, "bold"),
            command=self._open_folder,
        )

    def _update_drive(self):
        path = self._dir_var.get().strip() if hasattr(self, "_dir_var") else self._save_dir
        total, used, free = drive_info(path)
        if total:
            tg = total / (1024 ** 3)
            fg = free / (1024 ** 3)
            drive = os.path.splitdrive(path)[0] or path[:3]
            pct = (used / total * 100)
            c = P["success"] if fg > 5 else (P["warn"] if fg > 1 else P["error"])
            self._drive_lbl.configure(
                text=f"💾  {drive}  —  {fg:.1f} GB free of {tg:.0f} GB  ({100 - pct:.0f}% available)",
                text_color=c,
            )
        else:
            self._drive_lbl.configure(text="")

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._save_dir)
        if d:
            self._save_dir = d
            self._dir_var.set(d)
            self._update_drive()

    def _set_dir(self, path):
        self._save_dir = path
        self._dir_var.set(path)
        self._update_drive()

    def _open_folder(self):
        path = self._dir_var.get().strip() or self._save_dir
        if os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])

    # ===================================================================
    # DOWNLOAD ENGINE
    # ===================================================================
    def _start_dl(self):
        if self._dl_active or not self._sel:
            return
        save = self._dir_var.get().strip() or os.path.expanduser("~/Downloads")
        os.makedirs(save, exist_ok=True)
        self._dl_active = True
        self._open_btn.pack_forget()

        self._dl_btn.configure(
            text="Downloading...", state="disabled",
            fg_color=P["surface"], text_color=P["text3"],
        )
        self._status.configure(text="Downloading", text_color=P["warn"])

        # Build progress UI
        self._prog_frame.pack(fill="x", pady=(0, 8))
        for w in self._prog_frame.winfo_children():
            w.destroy()
        pi = ctk.CTkFrame(self._prog_frame, fg_color="transparent")
        pi.pack(fill="x", padx=14, pady=12)

        # ── Progress row 1: bar + percentage ──
        r1 = ctk.CTkFrame(pi, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 4))

        self._pct_lbl = ctk.CTkLabel(
            r1, text="0%",
            font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=P["accent_hi"],
        )
        self._pct_lbl.pack(side="left")

        self._eta_lbl = ctk.CTkLabel(
            r1, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=P["text3"],
        )
        self._eta_lbl.pack(side="right")

        self._prog = ctk.CTkProgressBar(
            pi, height=6, corner_radius=3,
            fg_color=P["bg"], progress_color=P["accent"],
        )
        self._prog.pack(fill="x", pady=(0, 8))
        self._prog.set(0)

        # ── Stats grid ──
        stats = ctk.CTkFrame(pi, fg_color="transparent")
        stats.pack(fill="x")
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._stat_labels = {}
        stat_items = [
            ("Downloaded", "—"),
            ("Total", "—"),
            ("Speed", "—"),
            ("Elapsed", "0:00"),
        ]
        for i, (key, val) in enumerate(stat_items):
            cell = ctk.CTkFrame(stats, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="w", padx=(0, 12))

            ctk.CTkLabel(
                cell, text=key,
                font=ctk.CTkFont("Segoe UI", 9), text_color=P["dim"],
            ).pack(anchor="w")

            vlbl = ctk.CTkLabel(
                cell, text=val,
                font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=P["white"],
            )
            vlbl.pack(anchor="w")
            self._stat_labels[key] = vlbl

        # ── Action row ──
        self._act_row = ctk.CTkFrame(pi, fg_color="transparent")
        self._act_row.pack(fill="x", pady=(12, 0))

        self._pause_btn = ctk.CTkButton(
            self._act_row, text="⏸ Pause", width=100, height=32, corner_radius=6,
            fg_color=P["surface"], hover_color=P["hover"], text_color=P["white"],
            border_width=1, border_color=P["border"],
            command=self._toggle_pause,
        )
        self._pause_btn.pack(side="left", padx=(0, 10))

        self._cancel_btn = ctk.CTkButton(
            self._act_row, text="✕ Cancel", width=100, height=32, corner_radius=6,
            fg_color=P["error_dim"], hover_color=P["error_dim"], text_color=P["error"],
            border_width=1, border_color=P["error"],
            command=self._cancel_dl,
        )
        self._cancel_btn.pack(side="left")

        self._cancel_flag = False
        self._pause_flag = False
        self._dl_start = time.time()
        self._tick_elapsed()
        threading.Thread(target=self._dl_th, args=(self._sel, save), daemon=True).start()

    def _tick_elapsed(self):
        if not self._dl_active:
            return
        elapsed = time.time() - self._dl_start
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        if h:
            self._stat_labels["Elapsed"].configure(text=f"{h}:{m:02d}:{s:02d}")
        else:
            self._stat_labels["Elapsed"].configure(text=f"{m}:{s:02d}")
        self.after(1000, self._tick_elapsed)

    def _dl_th(self, fmt, save):
        url   = self._url_var.get().strip()
        title = clean(self._info.get("title", "video"))

        def hook(d):
            if self._cancel_flag:
                raise ValueError("Download cancelled by user")

            while self._pause_flag and not self._cancel_flag:
                time.sleep(0.5)

            if self._cancel_flag:
                raise ValueError("Download cancelled by user")

            if d["status"] == "downloading":
                dl_bytes = d.get("downloaded_bytes")
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")

                if dl_bytes and total_bytes and total_bytes > 0:
                    pct = dl_bytes / total_bytes
                else:
                    try:
                        pct_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get("_percent_str", "0%"))
                        pct = float(pct_str.strip().rstrip("%")) / 100
                    except (ValueError, TypeError):
                        pct = 0

                downloaded = d.get("_downloaded_bytes_str", "").strip()
                total      = (d.get("_total_bytes_str", "") or d.get("_total_bytes_estimate_str", "")).strip()
                speed      = d.get("_speed_str", "").strip() or "—"
                eta        = d.get("_eta_str", "").strip() or ""

                downloaded = re.sub(r'\x1b\[[0-9;]*m', '', downloaded)
                total = re.sub(r'\x1b\[[0-9;]*m', '', total)
                speed = re.sub(r'\x1b\[[0-9;]*m', '', speed)
                eta = re.sub(r'\x1b\[[0-9;]*m', '', eta)

                pct_display = f"{pct * 100:.1f}%"

                def upd(p=pct, pd=pct_display, dl=downloaded, tt=total, sp=speed, et=eta):
                    self._prog.set(p)
                    self._pct_lbl.configure(text=pd)
                    self._stat_labels["Downloaded"].configure(text=dl or "—")
                    self._stat_labels["Total"].configure(text=tt or "—")
                    self._stat_labels["Speed"].configure(text=sp)
                    if et:
                        self._eta_lbl.configure(text=f"ETA {et}")
                self.after(0, upd)

            elif d["status"] == "finished":
                def fin():
                    self._prog.set(1.0)
                    self._pct_lbl.configure(text="100.0%")
                    self._stat_labels["Speed"].configure(text="Processing")
                    self._eta_lbl.configure(text="Almost done")
                self.after(0, fin)

        opts = base_opts({"progress_hooks": [hook]})
        opts["outtmpl"] = os.path.join(save, f"{title}.%(ext)s")

        if fmt.get("mp3"):
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        elif fmt["type"] == "audio":
            opts["format"] = fmt["format_str"]
        else:
            # ── VIDEO: critical merge settings ──
            opts["format"] = fmt["format_str"]
            if FFMPEG_OK:
                # Force MP4 output container — ensures video+audio merge
                opts["merge_output_format"] = "mp4"
                # Ensure proper merging with these postprocessor args
                opts["postprocessor_args"] = {
                    "merger": ["-c:v", "copy", "-c:a", "aac", "-strict", "experimental"],
                }

        success, last_err = False, Exception("unknown")
        for client in CLIENTS:
            if self._cancel_flag:
                break
            o = dict(opts)
            o["extractor_args"] = {"youtube": {"player_client": client}}
            try:
                with yt_dlp.YoutubeDL(o) as ydl:
                    ydl.download([url])
                success = True
                break
            except Exception as e:
                last_err = e
                if self._cancel_flag or "cancelled" in str(e).lower():
                    break
                if "ffmpeg" in str(e).lower():
                    break
                continue

        if not success and not self._cancel_flag and "ffmpeg" not in str(last_err).lower():
            if not self._cancel_flag:
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    success = True
                except Exception as e:
                    last_err = e

        if success:
            self.after(0, lambda: self._dl_done(save))
        elif self._cancel_flag or "cancelled" in str(last_err).lower():
            self.after(0, lambda: self._dl_fail("Download was successfully cancelled."))
        else:
            msg = friendly(str(last_err))
            self.after(0, lambda m=msg: self._dl_fail(m))

    def _dl_done(self, save):
        self._dl_active = False
        elapsed = time.time() - self._dl_start
        m, s = divmod(int(elapsed), 60)

        self._prog.configure(progress_color=P["success"])
        self._pct_lbl.configure(text="✓ Complete", text_color=P["success"])
        self._eta_lbl.configure(text=f"{m}m {s}s")
        self._stat_labels["Speed"].configure(text="Done")

        self._status.configure(text="Complete", text_color=P["success"])

        self._dl_btn.configure(
            text="✓  Download complete  ·  Click to download again",
            fg_color=P["success_dim"], hover_color=P["hover"],
            text_color=P["success"], state="normal",
            command=self._reset_dl,
        )
        self._open_btn.pack(fill="x", pady=(6, 0))
        self._update_drive()

        messagebox.showinfo(
            "Download Complete",
            f"✓ Saved successfully!\n\nLocation: {save}\nTime: {m}m {s}s",
        )

    def _reset_dl(self):
        self._prog_frame.pack_forget()
        self._open_btn.pack_forget()
        if self._sel:
            ext = "MP4" if self._sel["type"] == "video" else self._sel.get("badge", "")
            self._dl_btn.configure(
                text=f"⬇  Download  ·  {self._sel['label']}  [{ext}]",
                fg_color=P["accent"], hover_color=P["accent2"],
                text_color="white", state="normal", command=self._start_dl,
            )
        else:
            self._dl_btn.configure(
                text="⬇  Select a quality first",
                fg_color=P["surface"], text_color=P["dim"],
                state="disabled", command=self._start_dl,
            )
        self._status.configure(text="Ready", text_color=P["text3"])

    def _cancel_dl(self):
        if not self._dl_active:
            return
        self._cancel_flag = True
        if hasattr(self, '_cancel_btn'):
            self._cancel_btn.configure(text="Cancelling...", state="disabled")
        if hasattr(self, '_pause_btn'):
            self._pause_btn.configure(state="disabled")

    def _toggle_pause(self):
        if not self._dl_active:
            return
        self._pause_flag = not self._pause_flag
        if self._pause_flag:
            self._pause_btn.configure(
                text="▶ Resume", fg_color=P["accent"], border_color=P["accent"]
            )
            self._stat_labels["Speed"].configure(text="Paused")
            self._status.configure(text="Paused", text_color=P["warn"])
        else:
            self._pause_btn.configure(
                text="⏸ Pause", fg_color=P["surface"], border_color=P["border"]
            )
            self._status.configure(text="Downloading...", text_color=P["warn"])

    def _dl_fail(self, msg):
        self._dl_active = False
        self._prog.configure(progress_color=P["error"])
        self._pct_lbl.configure(text="✗ Cancelled" if "cancel" in msg.lower() else "✗ Failed", text_color=P["error"])
        self._eta_lbl.configure(text="")
        self._stat_labels["Speed"].configure(text="Stopped")
        self._status.configure(text="Stopped", text_color=P["error"])

        self._dl_btn.configure(
            text="↻  Restart download" if "cancel" in msg.lower() else "✗  Failed — Click to retry",
            fg_color=P["error_dim"], hover_color=P["hover"],
            text_color=P["error"], state="normal", command=self._start_dl,
        )
        if "cancel" not in msg.lower():
            messagebox.showerror("Download Failed", msg)


# ===========================================================================
if __name__ == "__main__":
    App().mainloop()