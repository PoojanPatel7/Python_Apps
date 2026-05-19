# 🐍 Python Apps Collection

A curated collection of **20 desktop Python applications** built by Poojan Patel — ranging from network utilities and productivity tools to creative apps and system monitors. Each app is self-contained with its own documentation, dependencies, and setup instructions.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white&style=for-the-badge)
![Apps](https://img.shields.io/badge/Apps-20-success?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

---

## 📋 Application Directory

| # | App | Description | Key Tech |
|---|-----|-------------|----------|
| 01 | [**Speed Checker**](./01_Speed_Checker) | Real-time internet speed monitor | psutil, tkinter |
| 02 | [**Task Manager**](./02_Task_Manager) | Process monitor & controller | psutil, tkinter |
| 03 | [**YouTube Downloader**](./03_YouTube_Downloader) | YTDROP PRO — 4K/1080p/MP3 downloader | yt-dlp, customtkinter |
| 04 | [**Attendance Scraper**](./04_Attendance_Scraper) | Automated attendance data extractor | Selenium, pandas |
| 05 | [**Document Converter**](./05_Document_Converter) | Offline multi-format file converter | Flask, Pandoc |
| 06 | [**Image AI Analyzer**](./06_Image_AI_Analyzer) | VisionMind — offline image intelligence | Pillow, numpy |
| 07 | [**Mini Python IDE**](./07_Mini_Python_IDE) | Lightweight code editor with autocomplete | jedi, tkinter |
| 08 | [**Web Scraper**](./08_Web_Scraper) | Visual web data extractor | BeautifulSoup, pandas |
| 09 | [**Advanced Web Scraper**](./09_Advanced_Web_Scraper) | JS-rendered page scraper | Playwright |
| 10 | [**WiFi & BLE Scanner**](./10_WiFi_BLE_Scanner) | Network & Bluetooth discovery | bleak |
| 11 | [**App Shortcut Maker**](./11_App_Shortcut_Maker) | Windows Start Menu shortcut creator | pywin32 |
| 12 | [**Attendance Dashboard**](./12_Attendance_Dashboard) | Streamlit data visualizer | Streamlit, plotly |
| 13 | [**Attendance Command Center**](./13_Attendance_Command_Center) | Integrated scraper + dashboard | Streamlit, Selenium |
| 14 | [**TurboFTP Client**](./14_TurboFTP_Client) | Professional FTP client | ftplib (stdlib) |
| 15 | [**LAN File Share**](./15_LAN_File_Share) | Premium local network file sharing | Flask, customtkinter |
| 16 | [**Screen Recorder**](./16_Screen_Recorder) | ScreenForge Pro — recording tool | OpenCV, pyautogui |
| 17 | [**Python Script Manager**](./17_Python_Script_Manager) | Environment & script runner | tkinter (stdlib) |
| 18 | [**Temp File Cleaner**](./18_Temp_File_Cleaner) | System temp file scanner & cleaner | tkinter (stdlib) |
| 19 | [**Package Library Scanner**](./19_Package_Library_Scanner) | Python environment inspector | tkinter (stdlib) |
| 20 | [**LAN Device Scanner**](./20_LAN_Device_Scanner) | NetScope — network device discovery | tkinter (stdlib) |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/PoojanPatel7/Python_Apps.git
cd Python_Apps
```

### 2. Navigate to an App
```bash
cd 03_YouTube_Downloader
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python youtube_downloader.py
```

> 💡 **Each app folder has its own `README.md`** with detailed setup instructions, feature lists, and architecture explanations.

---

## 🏗️ Design Philosophy

- **🌙 Dark-First UI** — All apps use premium dark themes (obsidian, Catppuccin, terminal-hacker)
- **📴 Offline-First** — Most apps work without internet after initial setup
- **🧩 Self-Contained** — Each app has its own folder, dependencies, and docs
- **⚡ Lightweight** — 7 out of 20 apps require zero pip installations
- **🖥️ Desktop-Native** — Built with tkinter/customtkinter for native desktop feel

---

## 📦 Technology Stack

| Category | Technologies |
|----------|-------------|
| **GUI Frameworks** | tkinter, customtkinter, Streamlit |
| **Web** | Flask, Playwright, Selenium |
| **Data** | pandas, openpyxl, BeautifulSoup |
| **Media** | OpenCV, Pillow, yt-dlp |
| **System** | psutil, pyautogui, subprocess |
| **Network** | ftplib, socket, bleak |

---

## 📂 Repository Structure

```
Python_Apps/
├── 01_Speed_Checker/          # Real-time network speed monitor
├── 02_Task_Manager/           # Custom process manager
├── 03_YouTube_Downloader/     # YTDROP PRO video downloader
├── 04_Attendance_Scraper/     # Selenium-based data extraction
├── 05_Document_Converter/     # Flask + Pandoc converter
├── 06_Image_AI_Analyzer/      # Offline image analysis
├── 07_Mini_Python_IDE/        # Code editor with autocomplete
├── 08_Web_Scraper/            # GUI web data extractor
├── 09_Advanced_Web_Scraper/   # Playwright JS scraper
├── 10_WiFi_BLE_Scanner/       # Network & Bluetooth scanner
├── 11_App_Shortcut_Maker/     # Windows shortcut creator
├── 12_Attendance_Dashboard/   # Streamlit data dashboard
├── 13_Attendance_Command_Center/ # Integrated scraper + dashboard
├── 14_TurboFTP_Client/        # Professional FTP client
├── 15_LAN_File_Share/         # LAN file sharing server
├── 16_Screen_Recorder/        # ScreenForge Pro recorder
├── 17_Python_Script_Manager/  # Script runner & manager
├── 18_Temp_File_Cleaner/      # System cleaner
├── 19_Package_Library_Scanner/# Python environment inspector
├── 20_LAN_Device_Scanner/     # NetScope LAN scanner
├── .gitignore
└── README.md                  # This file
```

---

## 👤 Author

**Poojan Patel**
- GitHub: [@PoojanPatel7](https://github.com/PoojanPatel7)

---

## 📄 License

This project is licensed under the MIT License — see individual app folders for details.
