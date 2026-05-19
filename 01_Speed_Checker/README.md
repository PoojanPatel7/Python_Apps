# 🚀 Speed Checker — Real-Time Network Monitor

A premium dark-themed desktop application that monitors your internet speed in real-time, displaying download/upload rates with a sleek professional UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Real-time monitoring** of download and upload speeds
- **Premium dark UI** with obsidian-inspired color palette (`#0a0a0f`)
- **Auto-updating stats** via threaded background monitoring
- **System tray integration** with custom icon support
- **Lightweight** — minimal CPU usage with smart update intervals

## 📸 Preview

The app features a modern dashboard with:
- Live speed gauges (MB/s / KB/s)
- Network interface detection
- Historical data tracking per session

---

## 🛠️ Setup & Installation

### Step 1: Install Python
Make sure you have **Python 3.8+** installed:
```bash
python --version
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Generate App Icon (Optional)
```bash
python create_icon.py
```
This creates `icon.ico` and `icon.png` programmatically using PIL.

### Step 4: Run the Application
```bash
python main.py
```

---

## 📦 Dependencies

| Package  | Purpose                          |
|----------|----------------------------------|
| `psutil` | Network I/O stats & monitoring   |
| `Pillow` | Icon generation (`create_icon.py`) |

---

## 📂 File Structure

```
01_Speed_Checker/
├── main.py            # Main application (SpeedMonitorApp)
├── create_icon.py     # Programmatic icon generator
├── requirements.txt   # Python dependencies
├── icon.ico           # Generated app icon
├── icon.png           # Generated PNG icon
└── README.md          # This file
```

---

## 🔧 How It Works

1. **`psutil.net_io_counters()`** captures bytes sent/received
2. A background thread calculates speed deltas every second
3. The tkinter GUI updates labels with formatted speed values
4. Custom themed widgets provide the premium dark aesthetic

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
