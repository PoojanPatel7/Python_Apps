# 🚀 TurboFTP — Professional FTP Client

A full-featured, high-performance FTP desktop client with a premium Catppuccin-inspired dark UI. Features dual-pane file browsing, live transfer speeds, batch operations, and anti-timeout keep-alive.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Dual-pane file browser** — Local and remote side-by-side
- **Quick Connect** with Enter key binding and profile saving
- **Live transfer speeds** (MB/s) with progress bars
- **Tabbed logging** — Activity log and active transfers tabs
- **Right-click context menus** — Upload, download, rename, delete
- **Double-click transfers** — Instant file operations
- **Anti-timeout keep-alive** — NOOP ping every 30 seconds
- **Profile management** — Save and load recent connections
- **Passive mode (PASV)** support
- **Catppuccin dark theme** — VS Code-inspired premium styling

---

## 🛠️ Setup & Installation

### Step 1: No External Dependencies Needed!
This app uses **only Python standard library** modules.

### Step 2: Run the Application
```bash
python ftp_client.py
```

### Step 3: Connect to an FTP Server
1. Enter host, port, username, and password
2. Click **"⚡ Quick Connect"** or press **Enter**
3. Browse and transfer files between local and remote panes

---

## 📦 Dependencies

| Package   | Purpose                    | Status    |
|-----------|----------------------------|-----------|
| `tkinter` | GUI framework              | Built-in  |
| `ftplib`  | FTP protocol               | Built-in  |
| `json`    | Config file handling       | Built-in  |
| `base64`  | Password obfuscation       | Built-in  |

> 🎉 **Zero pip installations required!**

---

## 📂 File Structure

```
14_TurboFTP_Client/
├── ftp_client.py       # Main FTP client application (900+ lines)
├── requirements.txt    # (Empty — no external deps)
└── README.md           # This file
```

---

## 🔧 Key Features Explained

### Keep-Alive System
A background thread sends `NOOP` commands every 30 seconds to prevent the FTP server from timing out idle connections.

### Transfer Progress
Real-time progress tracking with speed calculation:
- Downloads use `RETR` with chunked callback
- Uploads use `STOR` with chunked callback
- Speed displayed as MB/s or KB/s

### Profile Storage
Connection profiles are saved to `turboftp_config.json` with base64-encoded passwords (basic obfuscation, not encryption).

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
