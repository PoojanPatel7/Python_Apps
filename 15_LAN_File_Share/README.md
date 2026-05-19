# 📁 LAN File Share — Premium Local Network File Sharing

A premium LAN file-sharing application with a Flask web server backend and a customtkinter desktop GUI. Share files across devices on the same network with QR code access, live chat, per-file locking, and user management.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Web-based file sharing** — Any device with a browser can access shared files
- **QR code access** — Scan to connect from mobile devices
- **Live chat system** — Group and private messaging between connected users
- **Per-file PIN locking** — Protect individual files with 4-digit PINs
- **User management** — See connected devices, kick users, toggle permissions
- **Upload/download** — Bidirectional file transfers
- **ZIP batch download** — Select multiple files to download as ZIP
- **Desktop GUI** — Admin control panel built with customtkinter
- **Premium dark UI** — Both web and desktop interfaces feature modern dark themes
- **Secure mode** — Optional server-wide PIN protection

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python local_lan.py
```

### Step 3: Access from Other Devices
1. The app shows a **QR code** and URL (e.g., `http://192.168.1.100:5000`)
2. Open the URL on any device connected to the same Wi-Fi/LAN
3. Enter the PIN if secure mode is enabled
4. Browse, upload, and download files!

---

## 📦 Dependencies

| Package          | Purpose                         |
|------------------|---------------------------------|
| `customtkinter`  | Desktop admin GUI               |
| `flask`          | Web server for file sharing     |
| `qrcode`         | QR code generation              |
| `Pillow`         | Image processing for QR codes   |

---

## 📂 File Structure

```
15_LAN_File_Share/
├── local_lan.py        # Main application (2100+ lines)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 Architecture

```
┌──────────────────┐         ┌─────────────────────┐
│  Desktop GUI     │         │  Web Interface       │
│  (customtkinter) │ ◄─────► │  (Flask + HTML/JS)   │
│  - Admin panel   │   HTTP  │  - File browser      │
│  - User mgmt     │         │  - Upload/Download   │
│  - File sharing   │         │  - Live chat         │
│  - System logs   │         │  - Search & filter   │
└──────────────────┘         └─────────────────────┘
         │                            │
         └────────── LAN ─────────────┘
              192.168.x.x:5000
```

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
