# ▶ YTDROP PRO — Premium YouTube Downloader

A full-featured YouTube video/audio downloader with a luxury obsidian dark UI, built using `customtkinter` and `yt-dlp`. Supports 4K, 1080p, and MP3 extraction.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **All quality options** — 4K, 2K, 1080p, 720p, 480p, 360p, 240p, 144p
- **Audio extraction** — MP3 (via FFmpeg) and M4A formats
- **Smart format detection** — Combines video-only + audio streams for HD
- **Live download progress** — Speed, percentage, ETA display
- **Thumbnail preview** — Fetches and displays video thumbnails
- **Robust extraction** — Cycles through 6 YouTube client APIs for reliability
- **Premium obsidian UI** — Apple-inspired dark theme with custom color palette
- **Quick directory selectors** — Downloads, Desktop, Videos shortcuts
- **Clipboard paste** — One-click URL paste button

---

## 🛠️ Setup & Installation

### Step 1: Install Python Dependencies
```bash
pip install customtkinter yt-dlp Pillow requests
```

### Step 2: Install FFmpeg (Required for 1080p+ and MP3)
```bash
# Windows (using winget)
winget install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

> ⚠️ **Without FFmpeg**, only 720p and below will be available (combined streams only). 1080p+ videos are served as video-only by YouTube and **require FFmpeg to merge** with audio.

### Step 3: Run the Application
```bash
python youtube_downloader.py
```

---

## 📦 Dependencies

| Package          | Purpose                              |
|------------------|--------------------------------------|
| `customtkinter`  | Modern dark-themed GUI framework     |
| `yt-dlp`         | YouTube video/audio extraction       |
| `Pillow`         | Thumbnail image processing           |
| `requests`       | HTTP requests for thumbnails         |
| `FFmpeg`         | Video+audio merging (system install) |

---

## 📂 File Structure

```
03_YouTube_Downloader/
├── youtube_downloader.py   # Main application (1196 lines)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔧 How It Works

1. **Paste a YouTube URL** and click "Download"
2. **yt-dlp** tries 6 different YouTube client APIs:
   - `tv_embedded` → `web_embedded` → `ios` → `android` → `mweb` → `web`
3. Available **formats are extracted** and categorized (video/audio)
4. **Select quality** from the grid of format cards
5. **FFmpeg merges** video-only + audio streams into a single MP4
6. File is saved to the selected directory

### Why the Multi-Client Approach?
YouTube frequently blocks certain API endpoints. By cycling through different client identifiers, YTDROP PRO maximizes the chance of successful extraction.

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| No 1080p+ options | Install FFmpeg: `winget install ffmpeg` |
| Black screen video | FFmpeg not installed — merge failed |
| "Extraction failed" | Update yt-dlp: `pip install -U yt-dlp` |
| SSL errors | Update yt-dlp: `pip install -U yt-dlp` |
| Age-restricted | Requires cookie authentication |

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
