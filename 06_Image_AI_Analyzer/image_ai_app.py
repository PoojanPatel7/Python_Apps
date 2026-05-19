"""
╔══════════════════════════════════════════════════════════════════╗
║         VisionMind — Local AI Image Intelligence                 ║
║         100% Offline · No API Key · Built From Scratch           ║
║                                                                  ║
║  AI Engine Features (all hand-coded):                            ║
║   • Color analysis & dominant palette extraction                 ║
║   • Edge detection (Sobel filter from scratch)                   ║
║   • Object/region segmentation                                   ║
║   • Brightness, contrast, saturation analysis                    ║
║   • Texture & pattern detection                                  ║
║   • Face-region detection (brightness heuristic)                 ║
║   • Scene type classification                                    ║
║   • Binary / pixel map representation                            ║
║   • Natural language Q&A engine (rule-based NLP)                 ║
║   • Per-image memory & conversation history                      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import time
import re
import math
import json
import struct
import hashlib
import colorsys
from pathlib import Path
from datetime import datetime
from io import BytesIO
import collections

# ─── PIL & NumPy ─────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("Install Pillow: pip install Pillow")

try:
    import numpy as np
    NP_OK = True
except ImportError:
    NP_OK = False
    print("Install numpy: pip install numpy")


# ═══════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════
C = {
    "bg":       "#0c0c14",
    "panel":    "#12121e",
    "card":     "#1a1a2e",
    "hover":    "#22223a",
    "input":    "#0f0f1a",
    "border":   "#2a2845",
    "border2":  "#3d3a70",
    "accent":   "#00d4aa",
    "accent2":  "#00ffcc",
    "purple":   "#9b59f5",
    "blue":     "#4ea8de",
    "yellow":   "#f5c518",
    "red":      "#ff5e57",
    "green":    "#2ecc71",
    "text":     "#e8f4f0",
    "muted":    "#7a8a8e",
    "dim":      "#445055",
    "user_bg":  "#0d2a22",
    "ai_bg":    "#0e0e20",
    "sep":      "#1a1a2e",
}

F = {
    "title":   ("Consolas", 20, "bold"),
    "head":    ("Consolas", 12, "bold"),
    "body":    ("Segoe UI", 11),
    "small":   ("Segoe UI", 9),
    "tiny":    ("Segoe UI", 8),
    "mono":    ("Consolas", 9),
    "input":   ("Segoe UI", 11),
    "tag":     ("Consolas", 8, "bold"),
}


# ═══════════════════════════════════════════════════════════════
#  LOCAL AI ENGINE — Built From Scratch
# ═══════════════════════════════════════════════════════════════

class ImageAnalyzer:
    """
    Performs deep local analysis of images using hand-coded algorithms.
    No external AI/API required — everything computed from pixel data.
    """

    # ── Named color table ──────────────────────────────────────
    COLOR_NAMES = {
        (255,0,0):"red",(220,20,60):"crimson",(139,0,0):"dark red",
        (255,165,0):"orange",(255,140,0):"dark orange",(255,69,0):"red-orange",
        (255,255,0):"yellow",(240,230,140):"khaki",(189,183,107):"dark khaki",
        (0,128,0):"green",(0,255,0):"lime",(34,139,34):"forest green",
        (0,100,0):"dark green",(144,238,144):"light green",(50,205,50):"lime green",
        (0,0,255):"blue",(0,0,139):"dark blue",(173,216,230):"light blue",
        (135,206,235):"sky blue",(70,130,180):"steel blue",(100,149,237):"cornflower blue",
        (0,255,255):"cyan",(0,139,139):"dark cyan",(32,178,170):"light sea green",
        (255,0,255):"magenta",(128,0,128):"purple",(148,0,211):"dark violet",
        (238,130,238):"violet",(255,20,147):"deep pink",(255,105,180):"hot pink",
        (255,192,203):"pink",(255,182,193):"light pink",
        (255,255,255):"white",(245,245,245):"off-white",(220,220,220):"gainsboro",
        (192,192,192):"silver",(169,169,169):"dark gray",(128,128,128):"gray",
        (105,105,105):"dim gray",(70,70,70):"very dark gray",(0,0,0):"black",
        (139,69,19):"saddle brown",(160,82,45):"sienna",(210,180,140):"tan",
        (245,222,179):"wheat",(222,184,135):"burlywood",(205,133,63):"peru",
        (255,228,196):"bisque",(255,235,205):"blanched almond",(255,250,205):"lemon chiffon",
        (255,248,220):"cornsilk",(250,235,215):"antique white",
        (64,224,208):"turquoise",(127,255,212):"aquamarine",(0,206,209):"dark turquoise",
        (72,61,139):"dark slate blue",(106,90,205):"slate blue",(123,104,238):"medium slate blue",
        (230,230,250):"lavender",(216,191,216):"thistle",(221,160,221):"plum",
        (218,112,214):"orchid",(199,21,133):"medium violet red",
        (255,127,80):"coral",(240,128,128):"light coral",(250,128,114):"salmon",
        (233,150,122):"dark salmon",(250,160,120):"light salmon",
    }

    SCENE_KEYWORDS = {
        "nature":     ["green", "blue", "sky blue", "forest green", "dark green", "lime green", "turquoise"],
        "urban":      ["gray", "dark gray", "silver", "dim gray", "very dark gray"],
        "sunset":     ["orange", "red-orange", "coral", "salmon", "hot pink", "dark orange"],
        "ocean":      ["blue", "cyan", "dark cyan", "turquoise", "aquamarine", "steel blue"],
        "night":      ["black", "very dark gray", "dark gray", "dark blue", "dark slate blue"],
        "food":       ["red", "orange", "yellow", "wheat", "tan", "burlywood", "saddle brown"],
        "portrait":   ["tan", "wheat", "bisque", "blanched almond", "antique white", "light pink"],
        "indoor":     ["white", "off-white", "gainsboro", "silver", "light blue", "lavender"],
        "snow":       ["white", "off-white", "lavender", "light blue"],
        "forest":     ["dark green", "forest green", "green", "dark cyan", "saddle brown"],
    }

    def __init__(self, path: str):
        self.path = path
        self.name = Path(path).name
        self.size_bytes = os.path.getsize(path)
        self.analysis: dict = {}
        self._pil_img: Image.Image | None = None
        self._arr: "np.ndarray | None" = None

    def analyze(self) -> dict:
        """Run full analysis pipeline. Returns rich analysis dict."""
        img = Image.open(self.path).convert("RGB")
        self._pil_img = img
        w, h = img.size

        # Resize to working size for speed
        work = img.copy()
        work.thumbnail((400, 400))
        arr = np.array(work, dtype=np.float32)
        self._arr = arr

        self.analysis = {
            "filename":     self.name,
            "filepath":     self.path,
            "width":        w,
            "height":       h,
            "megapixels":   round(w * h / 1_000_000, 2),
            "aspect":       self._aspect(w, h),
            "orientation":  "landscape" if w > h else ("portrait" if h > w else "square"),
            "file_size_kb": round(self.size_bytes / 1024, 1),
            "format":       Path(self.path).suffix.upper().strip("."),
            "binary_header": self._binary_header(),
            "colors":       self._color_analysis(arr),
            "brightness":   self._brightness(arr),
            "contrast":     self._contrast(arr),
            "saturation":   self._saturation(arr),
            "sharpness":    self._sharpness(arr),
            "edges":        self._edge_density(arr),
            "texture":      self._texture(arr),
            "regions":      self._region_map(arr),
            "dominant_palette": self._dominant_palette(arr),
            "scene":        self._scene_classify(arr),
            "has_text_regions": self._detect_text_regions(arr),
            "complexity":   self._complexity(arr),
            "histogram":    self._histogram_desc(arr),
        }
        return self.analysis

    # ── Binary Header ────────────────────────────────────
    def _binary_header(self) -> str:
        with open(self.path, "rb") as f:
            raw = f.read(32)
        bits = " ".join(f"{b:08b}" for b in raw[:8])
        hex_h = " ".join(f"{b:02X}" for b in raw[:16])
        return f"bits: {bits}\nhex:  {hex_h}"

    # ── Aspect Ratio ─────────────────────────────────────
    def _aspect(self, w, h) -> str:
        def gcd(a, b): return a if b == 0 else gcd(b, a % b)
        g = gcd(w, h)
        rw, rh = w // g, h // g
        common = {(16,9):"16:9",(4,3):"4:3",(1,1):"1:1",(3,2):"3:2",
                  (21,9):"21:9",(9,16):"9:16",(2,3):"2:3",(3,4):"3:4"}
        for ratio, name in common.items():
            if abs(rw/rh - ratio[0]/ratio[1]) < 0.05:
                return name
        return f"{rw}:{rh}"

    # ── Color Analysis ────────────────────────────────────
    def _color_analysis(self, arr: "np.ndarray") -> dict:
        r = arr[:,:,0]; g = arr[:,:,1]; b = arr[:,:,2]
        return {
            "mean_r": float(np.mean(r)),
            "mean_g": float(np.mean(g)),
            "mean_b": float(np.mean(b)),
            "warmth": "warm" if np.mean(r) > np.mean(b) + 15 else
                      ("cool" if np.mean(b) > np.mean(r) + 15 else "neutral"),
        }

    # ── Brightness ────────────────────────────────────────
    def _brightness(self, arr: "np.ndarray") -> dict:
        gray = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        mean = float(np.mean(gray))
        label = ("very dark" if mean < 40 else "dark" if mean < 80 else
                 "slightly dark" if mean < 110 else "moderate" if mean < 145 else
                 "slightly bright" if mean < 180 else "bright" if mean < 220 else "very bright")
        return {"value": round(mean, 1), "label": label, "percent": round(mean/255*100, 1)}

    # ── Contrast ──────────────────────────────────────────
    def _contrast(self, arr: "np.ndarray") -> dict:
        gray = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        std = float(np.std(gray))
        label = ("very low" if std < 20 else "low" if std < 40 else
                 "moderate" if std < 60 else "high" if std < 80 else "very high")
        return {"value": round(std, 1), "label": label}

    # ── Saturation ────────────────────────────────────────
    def _saturation(self, arr: "np.ndarray") -> dict:
        r,g,b = arr[:,:,0]/255, arr[:,:,1]/255, arr[:,:,2]/255
        cmax = np.maximum(np.maximum(r,g),b)
        cmin = np.minimum(np.minimum(r,g),b)
        sat = np.where(cmax == 0, 0, (cmax-cmin)/cmax)
        mean = float(np.mean(sat))
        label = ("grayscale" if mean < 0.05 else "muted" if mean < 0.15 else
                 "low" if mean < 0.30 else "moderate" if mean < 0.50 else
                 "vibrant" if mean < 0.70 else "very vibrant")
        return {"value": round(mean, 3), "label": label, "percent": round(mean*100,1)}

    # ── Sharpness (Laplacian variance) ───────────────────
    def _sharpness(self, arr: "np.ndarray") -> dict:
        gray = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]).astype(np.float32)
        # Laplacian kernel
        lap = (np.roll(gray,-1,0) + np.roll(gray,1,0) +
               np.roll(gray,-1,1) + np.roll(gray,1,1) - 4*gray)
        var = float(np.var(lap))
        label = ("blurry" if var < 50 else "slightly soft" if var < 200 else
                 "moderate" if var < 800 else "sharp" if var < 2000 else "very sharp")
        return {"value": round(var, 1), "label": label}

    # ── Sobel Edge Detection ──────────────────────────────
    def _edge_density(self, arr: "np.ndarray") -> dict:
        gray = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2])
        # Sobel X
        sx = (np.roll(gray,-1,1) - np.roll(gray,1,1))
        # Sobel Y
        sy = (np.roll(gray,-1,0) - np.roll(gray,1,0))
        mag = np.sqrt(sx**2 + sy**2)
        edge_px = float(np.mean(mag > 30))
        label = ("minimal" if edge_px < 0.05 else "low" if edge_px < 0.12 else
                 "moderate" if edge_px < 0.22 else "high" if edge_px < 0.35 else "very high")
        return {"density": round(edge_px, 3), "label": label,
                "percent": round(edge_px*100, 1)}

    # ── Texture (local std) ───────────────────────────────
    def _texture(self, arr: "np.ndarray") -> dict:
        gray = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2])
        h, w = gray.shape
        block = 16
        stds = []
        for y in range(0, h-block, block):
            for x in range(0, w-block, block):
                stds.append(float(np.std(gray[y:y+block, x:x+block])))
        mean_std = float(np.mean(stds)) if stds else 0
        label = ("smooth" if mean_std < 8 else "slightly textured" if mean_std < 16 else
                 "moderately textured" if mean_std < 28 else "highly textured" if mean_std < 45
                 else "very rough")
        return {"value": round(mean_std, 2), "label": label}

    # ── Dominant Color Palette ────────────────────────────
    def _dominant_palette(self, arr: "np.ndarray", k: int = 6) -> list:
        h, w = arr.shape[:2]
        pixels = arr.reshape(-1, 3)
        # Simple k-means from scratch
        idx = np.random.choice(len(pixels), k, replace=False)
        centers = pixels[idx].copy()
        for _ in range(12):
            dists = np.array([np.sum((pixels - c)**2, axis=1) for c in centers])
            labels = np.argmin(dists, axis=0)
            new_centers = np.array([
                pixels[labels == i].mean(axis=0) if np.sum(labels == i) > 0 else centers[i]
                for i in range(k)
            ])
            if np.allclose(centers, new_centers, atol=1):
                break
            centers = new_centers
        counts = [int(np.sum(labels == i)) for i in range(k)]
        total = sum(counts)
        palette = []
        for i in np.argsort(counts)[::-1]:
            r, g, b = [int(v) for v in centers[i]]
            name = self._nearest_color(r, g, b)
            pct = round(counts[i]/total*100, 1)
            palette.append({"rgb": (r,g,b), "hex": f"#{r:02X}{g:02X}{b:02X}",
                            "name": name, "percent": pct})
        return palette

    def _nearest_color(self, r, g, b) -> str:
        best, bdist = "unknown", 1e18
        for (cr,cg,cb), name in self.COLOR_NAMES.items():
            d = (r-cr)**2 + (g-cg)**2 + (b-cb)**2
            if d < bdist:
                bdist, best = d, name
        return best

    # ── Region Map ────────────────────────────────────────
    def _region_map(self, arr: "np.ndarray") -> dict:
        h, w = arr.shape[:2]
        def avg_bright(patch):
            return float(np.mean(0.299*patch[:,:,0]+0.587*patch[:,:,1]+0.114*patch[:,:,2]))
        thirds_h = [arr[:h//3], arr[h//3:2*h//3], arr[2*h//3:]]
        thirds_w = [arr[:,:w//3], arr[:,w//3:2*w//3], arr[:,2*w//3:]]
        return {
            "top":    round(avg_bright(thirds_h[0]), 1),
            "middle": round(avg_bright(thirds_h[1]), 1),
            "bottom": round(avg_bright(thirds_h[2]), 1),
            "left":   round(avg_bright(thirds_w[0]), 1),
            "center": round(avg_bright(thirds_w[1]), 1),
            "right":  round(avg_bright(thirds_w[2]), 1),
        }

    # ── Scene Classification ──────────────────────────────
    def _scene_classify(self, arr: "np.ndarray") -> dict:
        palette = self._dominant_palette(arr, k=5)
        color_names = [p["name"] for p in palette]
        scores = {}
        for scene, keywords in self.SCENE_KEYWORDS.items():
            score = sum(1 for c in color_names if any(k in c for k in keywords))
            scores[scene] = score

        # Brightness-based hints
        bright = self._brightness(arr)
        bval = bright["value"]
        if bval < 50:   scores["night"] = scores.get("night",0) + 2
        if bval > 200:  scores["snow"] = scores.get("snow",0) + 1

        # Edge hints
        edges = self._edge_density(arr)
        if edges["density"] > 0.25: scores["urban"] = scores.get("urban",0) + 1

        best = max(scores, key=lambda k: scores[k]) if scores else "unknown"
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:3]
        return {"primary": best, "confidence": scores.get(best,0),
                "top3": [{"scene": s, "score": sc} for s, sc in ranked]}

    # ── Text Region Detection ─────────────────────────────
    def _detect_text_regions(self, arr: "np.ndarray") -> dict:
        gray = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2])
        # High-freq variance in rows indicates text
        row_var = np.var(np.diff(gray, axis=1), axis=1)
        high = float(np.mean(row_var > np.percentile(row_var, 80)))
        likely = high > 0.25
        return {"likely": likely, "confidence": round(high, 3),
                "description": "possible text regions detected" if likely else "no obvious text"}

    # ── Image Complexity ──────────────────────────────────
    def _complexity(self, arr: "np.ndarray") -> dict:
        edges = self._edge_density(arr)
        texture = self._texture(arr)
        palette = self._dominant_palette(arr, k=8)
        unique_colors = len(set(p["name"] for p in palette))
        score = edges["density"]*40 + texture["value"]*0.5 + unique_colors*5
        label = ("minimal" if score < 15 else "simple" if score < 30 else
                 "moderate" if score < 55 else "complex" if score < 80 else "very complex")
        return {"score": round(score, 1), "label": label}

    # ── Histogram Description ─────────────────────────────
    def _histogram_desc(self, arr: "np.ndarray") -> dict:
        gray = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]).astype(np.uint8)
        hist = np.bincount(gray.flatten(), minlength=256)
        shadow = int(np.sum(hist[:86]))
        midtone = int(np.sum(hist[86:170]))
        highlight = int(np.sum(hist[170:]))
        total = shadow + midtone + highlight
        dom = ("shadows" if shadow > highlight and shadow > midtone else
               "highlights" if highlight > shadow and highlight > midtone else "midtones")
        return {
            "shadows_pct":    round(shadow/total*100, 1),
            "midtones_pct":   round(midtone/total*100, 1),
            "highlights_pct": round(highlight/total*100, 1),
            "dominant_range": dom,
        }


# ═══════════════════════════════════════════════════════════════
#  NLP Q&A ENGINE — Rule-based, from scratch
# ═══════════════════════════════════════════════════════════════

class ImageQAEngine:
    """
    Answers natural language questions about an image
    using the pre-computed analysis. No ML/API required.
    """

    def __init__(self, analysis: dict):
        self.a = analysis

    def answer(self, question: str) -> str:
        q = question.lower().strip()
        q = re.sub(r'[?!.,]', '', q)

        # Route to the best handler
        handlers = [
            (["color", "colour", "hue", "tint", "shade", "palette", "dominant color",
              "main color", "what color", "which color"], self._colors),
            (["bright", "dark", "light", "luminance", "exposure", "lighting"], self._brightness),
            (["contrast", "dynamic range", "tonal"], self._contrast),
            (["sharp", "blur", "focus", "crisp", "soft", "clarity", "blurry"], self._sharpness),
            (["saturat", "vivid", "vibrant", "colorful", "grey", "gray", "mono",
              "dull", "muted"], self._saturation),
            (["edge", "outline", "border", "line", "shape", "structure", "boundary"], self._edges),
            (["texture", "rough", "smooth", "surface", "grain", "pattern"], self._texture),
            (["scene", "type", "category", "kind", "genre", "what kind", "what type",
              "nature", "outdoor", "indoor", "landscape", "portrait"], self._scene),
            (["size", "dimension", "resolution", "pixel", "width", "height",
              "megapixel", "large", "small"], self._dimensions),
            (["aspect", "ratio", "format", "orientation", "landscape", "portrait",
              "square"], self._orientation),
            (["file", "format", "extension", "jpg", "png", "size", "kb", "mb",
              "how big"], self._file_info),
            (["text", "word", "letter", "writing", "caption", "label",
              "number", "sign"], self._text),
            (["complex", "simple", "detail", "busy", "minimal",
              "complicated"], self._complexity),
            (["histogram", "tonal", "shadow", "midtone", "highlight",
              "exposure range"], self._histogram),
            (["region", "area", "section", "part", "top", "bottom", "left",
              "right", "center", "middle", "corner"], self._regions),
            (["warm", "cool", "temperature", "tone", "cold"], self._warmth),
            (["binary", "bits", "bytes", "hex", "raw", "data", "encode",
              "base64"], self._binary),
            (["describe", "tell me about", "explain", "what is", "what do you see",
              "analyze", "overview", "summary", "summarize", "everything",
              "details", "all about", "what can you tell"], self._full_description),
            (["face", "person", "people", "human", "portrait",
              "who", "subject"], self._faces),
            (["background", "backdrop", "behind"], self._background),
            (["mood", "feel", "atmosphere", "emotion", "vibe",
              "impression"], self._mood),
            (["composition", "rule of thirds", "framing",
              "balance", "symmetr"], self._composition),
        ]

        for keywords, handler in handlers:
            if any(kw in q for kw in keywords):
                return handler()

        return self._full_description()

    # ─── Handlers ─────────────────────────────────────────

    def _colors(self) -> str:
        p = self.a["dominant_palette"]
        c = self.a["colors"]
        lines = [f"🎨 **Color Analysis of '{self.a['filename']}'**\n"]
        lines.append(f"Color temperature: **{c['warmth']}** (R avg:{c['mean_r']:.0f}, G avg:{c['mean_g']:.0f}, B avg:{c['mean_b']:.0f})\n")
        lines.append("Dominant color palette:")
        for i, col in enumerate(p[:5], 1):
            bar = "█" * max(1, int(col["percent"] / 5))
            lines.append(f"  {i}. {col['name']:22s} {bar}  {col['percent']}%  ({col['hex']})")
        return "\n".join(lines)

    def _brightness(self) -> str:
        b = self.a["brightness"]
        h = self.a["histogram"]
        return (
            f"☀️ **Brightness Analysis**\n\n"
            f"Overall brightness: **{b['label']}** ({b['value']:.0f}/255 = {b['percent']}%)\n\n"
            f"Tonal distribution:\n"
            f"  Shadows:    {h['shadows_pct']}%\n"
            f"  Midtones:   {h['midtones_pct']}%\n"
            f"  Highlights: {h['highlights_pct']}%\n\n"
            f"The image is dominated by **{h['dominant_range']}**."
        )

    def _contrast(self) -> str:
        c = self.a["contrast"]
        return (
            f"⚡ **Contrast Analysis**\n\n"
            f"Contrast level: **{c['label']}**\n"
            f"Standard deviation of pixel luminance: {c['value']:.1f}\n\n"
            f"{'High contrast images have strong light/dark separation. This image has well-separated tones.' if c['label'] in ['high','very high'] else 'This image has relatively uniform tonal values, giving it a flat or misty look.'}"
        )

    def _sharpness(self) -> str:
        s = self.a["sharpness"]
        return (
            f"🔍 **Sharpness / Focus Analysis**\n\n"
            f"Focus quality: **{s['label']}**\n"
            f"Laplacian variance score: {s['value']:.1f}\n\n"
            f"{'The image appears well-focused with clear detail.' if s['label'] in ['sharp','very sharp'] else 'The image shows some softness or motion blur in areas.'}"
        )

    def _saturation(self) -> str:
        s = self.a["saturation"]
        return (
            f"🌈 **Color Saturation**\n\n"
            f"Saturation level: **{s['label']}** ({s['percent']}%)\n\n"
            f"{'This image is rich with vivid, punchy colors.' if s['percent'] > 50 else 'This image has subdued or desaturated colors, giving it a muted or artistic feel.' if s['percent'] < 20 else 'This image has balanced color saturation.'}"
        )

    def _edges(self) -> str:
        e = self.a["edges"]
        return (
            f"📐 **Edge & Structure Analysis** (Sobel filter)\n\n"
            f"Edge density: **{e['label']}** ({e['percent']}% of pixels are edges)\n\n"
            f"{'High edge density suggests detailed subject matter, architecture, or fine textures.' if e['label'] in ['high','very high'] else 'Low edge density suggests simple shapes, smooth backgrounds, or minimalist content.'}"
        )

    def _texture(self) -> str:
        t = self.a["texture"]
        return (
            f"🧱 **Texture Analysis**\n\n"
            f"Texture level: **{t['label']}** (local variance: {t['value']:.1f})\n\n"
            f"{'Rich surface detail is present — could be fabric, skin, wood, grass, etc.' if t['value'] > 20 else 'The image has smooth, flat areas with minimal surface texture.'}"
        )

    def _scene(self) -> str:
        sc = self.a["scene"]
        top = sc["top3"]
        lines = [f"🏞️ **Scene Classification**\n",
                 f"Most likely scene: **{sc['primary'].upper()}**\n",
                 "Probability ranking:"]
        for item in top:
            bar = "█" * max(1, item["score"] * 2)
            lines.append(f"  {item['scene']:12s} {bar}")
        lines.append(f"\nThis classification is based on color palette, brightness patterns, and edge density analysis.")
        return "\n".join(lines)

    def _dimensions(self) -> str:
        return (
            f"📏 **Image Dimensions**\n\n"
            f"Width:       {self.a['width']} px\n"
            f"Height:      {self.a['height']} px\n"
            f"Megapixels:  {self.a['megapixels']} MP\n"
            f"Aspect ratio: {self.a['aspect']}\n"
            f"Orientation: {self.a['orientation']}\n"
            f"File size:   {self.a['file_size_kb']} KB"
        )

    def _orientation(self) -> str:
        return (
            f"🖼️ **Orientation & Aspect**\n\n"
            f"Orientation: **{self.a['orientation']}**\n"
            f"Aspect ratio: **{self.a['aspect']}**\n"
            f"Dimensions: {self.a['width']} × {self.a['height']} px"
        )

    def _file_info(self) -> str:
        return (
            f"📁 **File Information**\n\n"
            f"Filename:  {self.a['filename']}\n"
            f"Format:    {self.a['format']}\n"
            f"File size: {self.a['file_size_kb']} KB\n"
            f"Dimensions: {self.a['width']} × {self.a['height']} px\n"
            f"Resolution: {self.a['megapixels']} megapixels"
        )

    def _text(self) -> str:
        t = self.a["has_text_regions"]
        return (
            f"📝 **Text Detection**\n\n"
            f"Result: **{t['description']}**\n"
            f"Confidence: {t['confidence']*100:.0f}%\n\n"
            f"{'High-frequency horizontal variations suggest text characters or labels.' if t['likely'] else 'The image does not show strong indicators of text regions.'}\n\n"
            f"Note: This is a heuristic detection, not OCR. For actual text reading, install pytesseract."
        )

    def _complexity(self) -> str:
        c = self.a["complexity"]
        return (
            f"🔲 **Image Complexity**\n\n"
            f"Complexity: **{c['label']}** (score: {c['score']:.1f}/100)\n\n"
            f"{'The image has many elements, fine details, and varied textures.' if c['score'] > 55 else 'The image is clean and simple with few visual elements.'}"
        )

    def _histogram(self) -> str:
        h = self.a["histogram"]
        return (
            f"📊 **Tonal Histogram**\n\n"
            f"Shadows (0–85):     {h['shadows_pct']}%  {'█'*int(h['shadows_pct']//5)}\n"
            f"Midtones (86–169):  {h['midtones_pct']}%  {'█'*int(h['midtones_pct']//5)}\n"
            f"Highlights (170+):  {h['highlights_pct']}%  {'█'*int(h['highlights_pct']//5)}\n\n"
            f"Dominant tonal range: **{h['dominant_range']}**"
        )

    def _regions(self) -> str:
        r = self.a["regions"]
        def bar(v): return "░" if v < 60 else "▒" if v < 120 else "▓" if v < 180 else "█"
        return (
            f"🗺️ **Spatial Region Brightness Map**\n\n"
            f"  TOP:    {bar(r['top'])*8}  {r['top']:.0f}\n"
            f"  MID:    {bar(r['middle'])*8}  {r['middle']:.0f}\n"
            f"  BOT:    {bar(r['bottom'])*8}  {r['bottom']:.0f}\n\n"
            f"  LEFT:   {bar(r['left'])*8}  {r['left']:.0f}\n"
            f"  CENTER: {bar(r['center'])*8}  {r['center']:.0f}\n"
            f"  RIGHT:  {bar(r['right'])*8}  {r['right']:.0f}\n\n"
            f"Brighter regions may indicate the subject or light source."
        )

    def _warmth(self) -> str:
        c = self.a["colors"]
        w = c["warmth"]
        r, g, b = c["mean_r"], c["mean_g"], c["mean_b"]
        desc = {
            "warm": f"The image leans warm (R:{r:.0f} > B:{b:.0f}). Warm tones suggest sunlight, fire, skin tones, or autumn colors.",
            "cool": f"The image leans cool (B:{b:.0f} > R:{r:.0f}). Cool tones suggest shade, water, night, or winter scenes.",
            "neutral": f"The image has a neutral color temperature (R:{r:.0f} ≈ B:{b:.0f}). Balanced or white-balanced."
        }
        return f"🌡️ **Color Temperature**\n\nTemperature: **{w}**\n\n{desc[w]}"

    def _binary(self) -> str:
        bh = self.a["binary_header"]
        return (
            f"💾 **Binary / Raw Data**\n\n"
            f"File: {self.a['filename']} ({self.a['file_size_kb']} KB)\n\n"
            f"First 8 bytes in binary + hex:\n{bh}\n\n"
            f"Total bytes: {int(self.a['file_size_kb']*1024):,}\n"
            f"Total pixels: {self.a['width'] * self.a['height']:,}\n"
            f"Bits per pixel (RGB): 24\n"
            f"Raw uncompressed size: {self.a['width']*self.a['height']*3//1024:,} KB"
        )

    def _full_description(self) -> str:
        a = self.a
        p = a["dominant_palette"]
        sc = a["scene"]
        b = a["brightness"]
        s = a["saturation"]
        e = a["edges"]
        t = a["texture"]
        c = a["complexity"]
        colors_str = ", ".join(f"{col['name']} ({col['percent']}%)" for col in p[:3])
        lines = [
            f"🖼️ **Full Image Analysis: {a['filename']}**\n",
            f"**Dimensions:** {a['width']} × {a['height']} px ({a['megapixels']} MP) · {a['orientation']} · {a['aspect']} · {a['file_size_kb']} KB\n",
            f"**Scene type:** {sc['primary'].upper()} (classified from color distribution & brightness)\n",
            f"**Dominant colors:** {colors_str}\n",
            f"**Color temperature:** {a['colors']['warmth']}\n",
            f"**Brightness:** {b['label']} ({b['percent']}%)\n",
            f"**Contrast:** {a['contrast']['label']}\n",
            f"**Saturation:** {s['label']} ({s['percent']}%)\n",
            f"**Sharpness:** {a['sharpness']['label']}\n",
            f"**Edge density:** {e['label']} ({e['percent']}%)\n",
            f"**Texture:** {t['label']}\n",
            f"**Complexity:** {c['label']} (score {c['score']:.0f}/100)\n",
            f"**Text detected:** {'Yes — possible text regions' if a['has_text_regions']['likely'] else 'No obvious text'}\n",
            f"**Tonal balance:** {a['histogram']['shadows_pct']}% shadows / {a['histogram']['midtones_pct']}% midtones / {a['histogram']['highlights_pct']}% highlights\n",
            f"\n**Binary header:** {a['binary_header'].split(chr(10))[0]}",
        ]
        return "\n".join(lines)

    def _faces(self) -> str:
        sc = self.a["scene"]
        sat = self.a["saturation"]
        bright = self.a["brightness"]
        p = self.a["dominant_palette"]
        skin_colors = {"tan","wheat","bisque","blanched almond","antique white",
                       "light pink","peachpuff","peru","light coral","salmon"}
        has_skin = any(col["name"] in skin_colors for col in p[:4])
        is_portrait = sc["primary"] == "portrait" or has_skin
        return (
            f"👤 **Person / Subject Detection**\n\n"
            f"Scene type suggests: **{'portrait / person likely present' if is_portrait else 'no obvious person detected'}**\n\n"
            f"Skin-tone colors in palette: {'Yes — ' + ', '.join(c['name'] for c in p[:4] if c['name'] in skin_colors) if has_skin else 'Not detected'}\n\n"
            f"Note: This uses color heuristics, not a face detection neural network. "
            f"For accurate face detection, install opencv-python (cv2.CascadeClassifier)."
        )

    def _background(self) -> str:
        r = self.a["regions"]
        p = self.a["dominant_palette"]
        edges = self.a["edges"]
        # Background is usually the most diffuse region
        low_edge = edges["label"] in ["minimal","low"]
        bg_color = p[-1] if len(p) > 1 else p[0]
        return (
            f"🌅 **Background Analysis**\n\n"
            f"Likely background color: **{bg_color['name']}** ({bg_color['hex']})\n\n"
            f"Background region brightness:\n"
            f"  Top: {r['top']:.0f}  |  Left: {r['left']:.0f}  |  Right: {r['right']:.0f}\n\n"
            f"Background appears: **{'simple / clean' if low_edge else 'complex / detailed'}**"
        )

    def _mood(self) -> str:
        b = self.a["brightness"]
        s = self.a["saturation"]
        c = self.a["colors"]
        warm = c["warmth"]
        bv = b["value"]; sv = s["value"]
        if bv > 180 and sv > 0.4 and warm == "warm":
            mood = "energetic, joyful, and vibrant"
        elif bv < 60:
            mood = "dark, mysterious, or dramatic"
        elif bv > 160 and sv < 0.15:
            mood = "clean, minimal, and serene"
        elif warm == "cool" and bv < 120:
            mood = "melancholic, calm, or cinematic"
        elif sv > 0.6:
            mood = "bold, exciting, and intense"
        else:
            mood = "balanced and neutral"
        return (
            f"🎭 **Mood & Atmosphere**\n\n"
            f"The image conveys a **{mood}** mood.\n\n"
            f"Based on:\n"
            f"  • Brightness: {b['label']} ({bv:.0f}/255)\n"
            f"  • Saturation: {s['label']}\n"
            f"  • Color temperature: {warm}\n"
            f"  • Contrast: {self.a['contrast']['label']}"
        )

    def _composition(self) -> str:
        r = self.a["regions"]
        e = self.a["edges"]
        diff_lr = abs(r["left"] - r["right"])
        diff_tb = abs(r["top"] - r["bottom"])
        sym = "roughly symmetric" if diff_lr < 15 else "asymmetric (left-right)"
        return (
            f"📐 **Composition & Framing**\n\n"
            f"Orientation: **{self.a['orientation']}** ({self.a['aspect']})\n"
            f"Balance: **{sym}** (L:{r['left']:.0f} vs R:{r['right']:.0f})\n"
            f"Top-bottom: {'brighter top' if r['top']>r['bottom'] else 'brighter bottom'} (T:{r['top']:.0f} vs B:{r['bottom']:.0f})\n"
            f"Center brightness: {r['center']:.0f}\n"
            f"Edge complexity: {e['label']}\n\n"
            f"{'Center-weighted composition — subject likely in the middle.' if r['center'] > r['top'] and r['center'] > r['bottom'] else 'Off-center subject or wide/open composition.'}"
        )


# ═══════════════════════════════════════════════════════════════
#  IMAGE MEMORY STORE
# ═══════════════════════════════════════════════════════════════

class ImageMemory:
    def __init__(self):
        self.images: dict = {}
        self.active: str | None = None
        self._ctr = 0

    def add(self, path: str) -> str:
        self._ctr += 1
        iid = f"img_{self._ctr}"
        analyzer = ImageAnalyzer(path)
        analysis = analyzer.analyze()
        qa = ImageQAEngine(analysis)
        self.images[iid] = {
            "id": iid, "path": path, "analysis": analysis,
            "qa": qa, "history": [], "thumb": None,
            "ts": datetime.now().strftime("%H:%M"),
            "name": Path(path).name,
        }
        return iid

    def chat(self, iid: str, question: str) -> str:
        img = self.images[iid]
        answer = img["qa"].answer(question)
        img["history"].append({"role":"user","text":question,"ts":datetime.now().strftime("%H:%M")})
        img["history"].append({"role":"ai","text":answer,"ts":datetime.now().strftime("%H:%M")})
        return answer

    def get(self, iid: str): return self.images.get(iid)


# ═══════════════════════════════════════════════════════════════
#  GUI APPLICATION
# ═══════════════════════════════════════════════════════════════

class VisionMindApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.mem = ImageMemory()
        self._setup_window()
        self._build_ui()
        self._show_welcome()

    def _setup_window(self):
        self.root.title("VisionMind — Local AI Image Intelligence")
        self.root.geometry("1300x840")
        self.root.minsize(900, 620)
        self.root.configure(bg=C["bg"])
        try: self.root.state("zoomed")
        except: pass

    # ── Full UI ───────────────────────────────────────────
    def _build_ui(self):
        self._topbar()
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)
        self._sidebar(body)
        self._chat_area(body)

    # ── Topbar ────────────────────────────────────────────
    def _topbar(self):
        bar = tk.Frame(self.root, bg=C["panel"], height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="⬡", bg=C["panel"], fg=C["accent"],
                 font=("Consolas",22)).pack(side="left", padx=(16,4))
        tk.Label(bar, text="VisionMind", bg=C["panel"], fg=C["text"],
                 font=F["title"]).pack(side="left")
        tk.Label(bar, text="LOCAL AI · NO API NEEDED", bg=C["panel"],
                 fg=C["dim"], font=F["tag"]).pack(side="left", padx=(10,0), pady=(16,0))

        self._btn(bar, "＋  Upload Images", self._upload,
                  C["accent"], C["bg"]).pack(side="right", padx=(0,14), pady=10)
        self._btn(bar, "🗑 Clear All", self._clear_all,
                  C["card"], C["red"]).pack(side="right", padx=(0,6), pady=10)

        # Status
        self.status = tk.Label(bar, text="● OFFLINE MODE — All AI runs locally",
                               bg=C["panel"], fg=C["green"], font=F["small"])
        self.status.pack(side="right", padx=20)

    # ── Sidebar ───────────────────────────────────────────
    def _sidebar(self, parent):
        side = tk.Frame(parent, bg=C["panel"], width=250)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, text="IMAGES", bg=C["panel"], fg=C["dim"],
                 font=F["tag"]).pack(anchor="w", padx=14, pady=(12,4))

        self.img_count = tk.Label(side, text="None uploaded", bg=C["panel"],
                                  fg=C["muted"], font=F["small"])
        self.img_count.pack(anchor="w", padx=14, pady=(0,8))

        # Separator
        tk.Frame(side, bg=C["border"], height=1).pack(fill="x", padx=8, pady=4)

        # Scrollable gallery
        outer = tk.Frame(side, bg=C["panel"])
        outer.pack(fill="both", expand=True)
        self._gcanvas = tk.Canvas(outer, bg=C["panel"], highlightthickness=0)
        gsb = tk.Scrollbar(outer, orient="vertical", command=self._gcanvas.yview)
        self.gallery = tk.Frame(self._gcanvas, bg=C["panel"])
        self.gallery.bind("<Configure>", lambda e:
            self._gcanvas.configure(scrollregion=self._gcanvas.bbox("all")))
        self._gcanvas.create_window((0,0), window=self.gallery, anchor="nw")
        self._gcanvas.configure(yscrollcommand=gsb.set)
        self._gcanvas.pack(side="left", fill="both", expand=True)
        gsb.pack(side="right", fill="y")
        self._gcanvas.bind("<MouseWheel>",
            lambda e: self._gcanvas.yview_scroll(-1*(e.delta//120),"units"))

        # Bottom hint
        tk.Frame(side, bg=C["border"], height=1).pack(fill="x", padx=8)
        tk.Label(side,
            text="All analysis runs locally.\nNo internet · No API key.\nBuilt from scratch with\nNumPy + PIL only.",
            bg=C["panel"], fg=C["dim"], font=F["tiny"], justify="left"
        ).pack(anchor="w", padx=14, pady=10)

    # ── Chat Area ─────────────────────────────────────────
    def _chat_area(self, parent):
        self.chat_panel = tk.Frame(parent, bg=C["bg"])
        self.chat_panel.pack(side="left", fill="both", expand=True)

        # Header
        hdr = tk.Frame(self.chat_panel, bg=C["panel"], height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        self.chat_title = tk.Label(hdr, text="Select an image →",
                                   bg=C["panel"], fg=C["text"], font=F["head"])
        self.chat_title.pack(side="left", padx=16)
        self.chat_meta = tk.Label(hdr, text="", bg=C["panel"],
                                  fg=C["muted"], font=F["small"])
        self.chat_meta.pack(side="left", padx=4)

        self._btn(hdr, "📊 Full Analysis", self._full_analysis,
                  C["card"], C["blue"]).pack(side="right", padx=(0,8), pady=8)
        self._btn(hdr, "🗑 Clear Chat", self._clear_chat,
                  C["card"], C["red"]).pack(side="right", padx=(0,4), pady=8)

        # Separator
        tk.Frame(self.chat_panel, bg=C["border2"], height=1).pack(fill="x")

        # Messages
        mf = tk.Frame(self.chat_panel, bg=C["bg"])
        mf.pack(fill="both", expand=True)
        self._mcanvas = tk.Canvas(mf, bg=C["bg"], highlightthickness=0)
        msb = tk.Scrollbar(mf, orient="vertical", command=self._mcanvas.yview)
        self.msg_frame = tk.Frame(self._mcanvas, bg=C["bg"])
        self.msg_frame.bind("<Configure>", lambda e:
            self._mcanvas.configure(scrollregion=self._mcanvas.bbox("all")))
        self._mcanvas.create_window((0,0), window=self.msg_frame, anchor="nw")
        self._mcanvas.configure(yscrollcommand=msb.set)
        self._mcanvas.pack(side="left", fill="both", expand=True)
        msb.pack(side="right", fill="y")
        self._mcanvas.bind("<MouseWheel>",
            lambda e: self._mcanvas.yview_scroll(-1*(e.delta//120),"units"))

        # Thinking bar
        self.think_bar = tk.Label(self.chat_panel, text="", bg=C["bg"],
                                  fg=C["accent"], font=F["small"])
        self.think_bar.pack(fill="x", padx=16, pady=2)

        # Input area
        inp_outer = tk.Frame(self.chat_panel, bg=C["panel"])
        inp_outer.pack(fill="x")
        tk.Frame(inp_outer, bg=C["border2"], height=1).pack(fill="x")
        inp = tk.Frame(inp_outer, bg=C["panel"])
        inp.pack(fill="x", padx=14, pady=12)

        self.input_txt = tk.Text(inp, height=3, bg=C["input"], fg=C["text"],
                                 font=F["input"], insertbackground=C["accent"],
                                 relief="flat", wrap="word", padx=12, pady=10,
                                 highlightthickness=1,
                                 highlightcolor=C["border2"],
                                 highlightbackground=C["border"])
        self.input_txt.pack(side="left", fill="both", expand=True)
        self.input_txt.bind("<Return>", self._on_enter)

        btn_col = tk.Frame(inp, bg=C["panel"])
        btn_col.pack(side="right", padx=(10,0))
        self.send_btn = self._btn(btn_col, "Send ▶", self._send,
                                  C["accent"], C["bg"], width=9)
        self.send_btn.pack(pady=(0,4))
        tk.Label(btn_col, text="↵ send", bg=C["panel"],
                 fg=C["dim"], font=F["tiny"]).pack()

        # Quick questions bar
        qq = tk.Frame(self.chat_panel, bg=C["panel"])
        qq.pack(fill="x", padx=14, pady=(0,8))
        tk.Label(qq, text="Quick:", bg=C["panel"], fg=C["dim"],
                 font=F["tiny"]).pack(side="left", padx=(0,6))
        for label in ["Colors", "Brightness", "Scene", "Mood", "Sharpness",
                      "Texture", "Binary", "Describe"]:
            self._chip(qq, label, lambda l=label: self._quick(l)).pack(side="left", padx=2)

    # ── Widget Helpers ────────────────────────────────────
    def _btn(self, p, txt, cmd, bg, fg, width=None):
        kw = dict(text=txt, command=cmd, bg=bg, fg=fg, font=F["small"],
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  activebackground=C["hover"], activeforeground=fg, bd=0)
        if width: kw["width"] = width
        b = tk.Button(p, **kw)
        b.bind("<Enter>", lambda e: b.configure(bg=C["hover"]))
        b.bind("<Leave>", lambda e: b.configure(bg=bg))
        return b

    def _chip(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=C["card"], fg=C["accent"], font=F["tiny"],
                      relief="flat", cursor="hand2", padx=8, pady=3,
                      activebackground=C["hover"], activeforeground=C["accent2"], bd=0)
        b.bind("<Enter>", lambda e: b.configure(bg=C["hover"]))
        b.bind("<Leave>", lambda e: b.configure(bg=C["card"]))
        return b

    # ── Welcome Screen ────────────────────────────────────
    def _show_welcome(self):
        for w in self.msg_frame.winfo_children(): w.destroy()
        f = tk.Frame(self.msg_frame, bg=C["bg"])
        f.pack(expand=True, fill="both", pady=40, padx=40)

        tk.Label(f, text="⬡", bg=C["bg"], fg=C["accent"],
                 font=("Consolas",52)).pack()
        tk.Label(f, text="VisionMind", bg=C["bg"], fg=C["text"],
                 font=("Consolas",26,"bold")).pack(pady=(4,2))
        tk.Label(f, text="100% Local AI  ·  No API Key  ·  No Internet Required",
                 bg=C["bg"], fg=C["accent"], font=F["small"]).pack()

        tk.Frame(f, bg=C["border2"], height=1).pack(fill="x", pady=20)

        features = [
            ("⬡", "Color Intelligence", "K-means clustering · Palette extraction · Warmth analysis"),
            ("⬡", "Computer Vision", "Sobel edge detection · Texture analysis · Region mapping"),
            ("⬡", "Scene Understanding", "Scene classification · Mood detection · Composition"),
            ("⬡", "Deep Inspection", "Binary data · Histogram · Sharpness · Saturation"),
            ("⬡", "Conversation Memory", "Full chat history per image · Ask anything anytime"),
        ]
        for icon, title, desc in features:
            row = tk.Frame(f, bg=C["card"], padx=18, pady=10)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, bg=C["card"], fg=C["accent"],
                     font=("Consolas",14)).pack(side="left", padx=(0,12))
            col = tk.Frame(row, bg=C["card"])
            col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=title, bg=C["card"], fg=C["text"],
                     font=F["head"]).pack(anchor="w")
            tk.Label(col, text=desc, bg=C["card"], fg=C["muted"],
                     font=F["small"]).pack(anchor="w")

        tk.Frame(f, bg=C["border"], height=1).pack(fill="x", pady=16)
        tk.Label(f, text="Upload an image using the button above to begin ↑",
                 bg=C["bg"], fg=C["dim"], font=F["small"]).pack()

    # ── Upload ────────────────────────────────────────────
    def _upload(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images","*.jpg *.jpeg *.png *.gif *.webp *.bmp *.tiff"),("All","*.*")]
        )
        for path in paths:
            self.status.configure(text=f"⚙ Analyzing {Path(path).name}...", fg=C["yellow"])
            self.root.update()
            iid = self.mem.add(path)
            self._add_gallery_card(iid)

        n = len(self.mem.images)
        self.img_count.configure(text=f"{n} image{'s' if n!=1 else ''}")
        self.status.configure(text="● OFFLINE MODE — All AI runs locally", fg=C["green"])

    # ── Gallery Card ──────────────────────────────────────
    def _add_gallery_card(self, iid: str):
        img = self.mem.get(iid)
        card = tk.Frame(self.gallery, bg=C["card"], padx=6, pady=6, cursor="hand2")
        card.pack(fill="x", padx=8, pady=4)

        # Thumbnail
        tlbl = tk.Label(card, bg=C["card"])
        tlbl.pack(anchor="center", pady=(0,4))
        if PIL_OK:
            try:
                pi = Image.open(img["path"]); pi.thumbnail((210,130))
                pt = ImageTk.PhotoImage(pi); img["thumb"] = pt
                tlbl.configure(image=pt)
            except:
                tlbl.configure(text=f"📷 {img['name'][:20]}",
                               fg=C["accent"], font=F["body"])
        else:
            tlbl.configure(text=f"📷 {img['name'][:20]}",
                           fg=C["accent"], font=F["body"])

        # Info
        sc = img["analysis"]["scene"]["primary"].upper()
        name = img["name"][:24] + ("..." if len(img["name"])>24 else "")
        tk.Label(card, text=name, bg=C["card"], fg=C["text"],
                 font=("Consolas",9,"bold")).pack(anchor="w")
        tk.Label(card, text=f"Scene: {sc}  ·  {img['analysis']['file_size_kb']} KB  ·  {img['ts']}",
                 bg=C["card"], fg=C["muted"], font=F["tiny"]).pack(anchor="w")

        # Palette dots
        pal_f = tk.Frame(card, bg=C["card"])
        pal_f.pack(anchor="w", pady=(3,0))
        for col in img["analysis"]["dominant_palette"][:5]:
            hex_ = col["hex"]
            tk.Label(pal_f, text="  ", bg=hex_, width=2,
                     relief="flat").pack(side="left", padx=1)
        tk.Label(pal_f, text=" palette", bg=C["card"],
                 fg=C["dim"], font=F["tiny"]).pack(side="left", padx=4)

        def select(e=None, i=iid, c=card):
            self._select(i)

        for w in [card, tlbl]:
            w.bind("<Button-1>", select)
        card.bind("<Enter>", lambda e: [card.configure(bg=C["hover"]),
            [ch.configure(bg=C["hover"]) for ch in card.winfo_children()
             if not isinstance(ch, tk.Frame)]])
        card.bind("<Leave>", lambda e: [card.configure(bg=C["card"]),
            [ch.configure(bg=C["card"]) for ch in card.winfo_children()
             if not isinstance(ch, tk.Frame)]])

        if len(self.mem.images) == 1:
            self.root.after(100, select)

    # ── Select Image ──────────────────────────────────────
    def _select(self, iid: str):
        self.mem.active = iid
        img = self.mem.get(iid)
        a = img["analysis"]
        self.chat_title.configure(text=f"⬡ {img['name']}")
        self.chat_meta.configure(
            text=f"{a['width']}×{a['height']}  ·  {a['orientation']}  ·  "
                 f"Scene: {a['scene']['primary']}  ·  {a['file_size_kb']} KB")
        self._redraw_chat(iid)
        # Auto welcome message on first select
        if not img["history"]:
            self.root.after(200, lambda: self._auto_welcome(iid))

    def _auto_welcome(self, iid: str):
        if self.mem.active != iid: return
        img = self.mem.get(iid)
        if img and not img["history"]:
            ans = self.mem.chat(iid, "describe")
            self._redraw_chat(iid)

    # ── Send ──────────────────────────────────────────────
    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._send(); return "break"

    def _send(self):
        if not self.mem.active:
            messagebox.showinfo("No Image", "Upload and select an image first.")
            return
        txt = self.input_txt.get("1.0","end").strip()
        if not txt: return
        self.input_txt.delete("1.0","end")
        self.think_bar.configure(text="⬡ Analyzing...", fg=C["accent"])
        self.send_btn.configure(state="disabled")
        self.root.update()
        iid = self.mem.active
        threading.Thread(target=self._do_send, args=(iid,txt), daemon=True).start()

    def _do_send(self, iid, txt):
        self.mem.chat(iid, txt)
        self.root.after(0, lambda: self._finish_send(iid))

    def _finish_send(self, iid):
        self.think_bar.configure(text="")
        self.send_btn.configure(state="normal")
        if self.mem.active == iid:
            self._redraw_chat(iid)

    # ── Quick question chips ──────────────────────────────
    def _quick(self, topic: str):
        if not self.mem.active:
            messagebox.showinfo("No Image", "Select an image first.")
            return
        self.input_txt.delete("1.0","end")
        self.input_txt.insert("1.0", topic)
        self._send()

    # ── Full Analysis Dump ────────────────────────────────
    def _full_analysis(self):
        if not self.mem.active: return
        img = self.mem.get(self.mem.active)
        a = img["analysis"]
        self.mem.chat(self.mem.active, "describe everything about this image in full detail")
        self._redraw_chat(self.mem.active)

    # ── Redraw Chat ───────────────────────────────────────
    def _redraw_chat(self, iid: str):
        for w in self.msg_frame.winfo_children(): w.destroy()
        img = self.mem.get(iid)
        if not img: return
        history = img["history"]
        if not history:
            tk.Label(self.msg_frame, text="💬 Ask anything about this image!",
                     bg=C["bg"], fg=C["dim"], font=F["body"]).pack(pady=40)
            return
        for turn in history:
            self._bubble(turn["role"], turn["text"], turn["ts"])
        self.msg_frame.update_idletasks()
        self._mcanvas.yview_moveto(1.0)

    def _bubble(self, role, text, ts):
        is_user = role == "user"
        outer = tk.Frame(self.msg_frame, bg=C["bg"])
        outer.pack(fill="x", padx=14, pady=(4,2))

        hdr = tk.Frame(outer, bg=C["bg"])
        hdr.pack(fill="x")
        icon_txt = "You" if is_user else "⬡ VisionMind AI"
        icon_fg  = C["blue"] if is_user else C["accent"]
        tk.Label(hdr, text=icon_txt, bg=C["bg"], fg=icon_fg,
                 font=("Consolas",9,"bold")).pack(side="left")
        tk.Label(hdr, text=f"  {ts}", bg=C["bg"], fg=C["dim"],
                 font=F["tiny"]).pack(side="left")

        bbg = C["user_bg"] if is_user else C["ai_bg"]
        bubble = tk.Frame(outer, bg=bbg, padx=14, pady=10)
        bubble.pack(fill="x")

        # Wrap width dynamically
        ww = max(400, self._mcanvas.winfo_width() - 80)
        tk.Label(bubble, text=text, bg=bbg, fg=C["text"],
                 font=F["mono"] if role=="ai" else F["body"],
                 wraplength=ww, justify="left", anchor="w").pack(fill="x", anchor="w")

    # ── Clear Chat ────────────────────────────────────────
    def _clear_chat(self):
        if not self.mem.active: return
        img = self.mem.get(self.mem.active)
        if img and messagebox.askyesno("Clear", f"Clear chat for {img['name']}?"):
            img["history"].clear()
            self._redraw_chat(self.mem.active)

    # ── Clear All ─────────────────────────────────────────
    def _clear_all(self):
        if messagebox.askyesno("Clear All", "Remove all images and chats?"):
            self.mem.images.clear()
            self.mem.active = None
            for w in self.gallery.winfo_children(): w.destroy()
            self.img_count.configure(text="None uploaded")
            self.chat_title.configure(text="Select an image →")
            self.chat_meta.configure(text="")
            self._show_welcome()


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    if not PIL_OK:
        print("ERROR: Pillow required. Run: pip install Pillow"); return
    if not NP_OK:
        print("ERROR: NumPy required. Run: pip install numpy"); return

    print("""
  ╔═══════════════════════════════════════════╗
  ║  VisionMind — Local AI Image Intelligence ║
  ║  100% offline · No API key needed         ║
  ║  pip install Pillow numpy  (one-time)      ║
  ╚═══════════════════════════════════════════╝
  Starting...
""")
    root = tk.Tk()
    app = VisionMindApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()