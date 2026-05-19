# 🎬 ScreenForge Pro — Premium Screen Recorder

A professional screen recording application with region selection, pause/resume, floating stop widget, cursor tracking, and frame-time synchronization for accurate playback speed.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Full screen or region recording** — Select custom areas to record
- **Pause/Resume** — Pause recording and resume without creating a new file
- **Floating stop widget** — Minimal overlay with timer (hidden from recording)
- **Frame-time sync** — Duplicates frames to ensure accurate playback speed
- **FPS options** — 15, 24, 30, or 60 FPS
- **Output formats** — MP4, AVI, MKV
- **Countdown timer** — 0/3/5/10 second delay before recording
- **Cursor dot overlay** — Shows cursor position in the recording
- **Self-exclusion** — The floating widget is masked from the recording
- **Keyboard shortcuts** — F9 Start/Stop, F10 Pause, F11 Region Select

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python screen_recorder.py
```

### Step 3: Record
1. Configure FPS, format, and countdown delay
2. Optionally select a screen region (or use fullscreen)
3. Click **"⏺ Start Recording"** or press **F9**
4. The app minimizes and shows a floating stop widget
5. Click **⏹** or press **F9** to stop and save

---

## 📦 Dependencies

| Package      | Purpose                          |
|--------------|----------------------------------|
| `opencv-python` | Video encoding (VideoWriter)  |
| `numpy`      | Frame data processing            |
| `pyautogui`  | Screenshot capture               |
| `Pillow`     | Image handling                   |

---

## 📂 File Structure

```
16_Screen_Recorder/
├── screen_recorder.py  # Main application (ScreenForgeApp)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 Key Technical Details

### Frame-Time Synchronization
The recorder calculates how many frames should exist based on elapsed time, and duplicates the current frame if capture is slower than target FPS. This ensures playback speed always matches real time.

### Self-Recording Prevention
The floating stop widget's screen coordinates are tracked, and those pixels are painted over in each frame using nearby pixel colors, preventing the widget from appearing in the final recording.

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
