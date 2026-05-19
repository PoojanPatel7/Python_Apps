# 🧹 SYS.CLEANER PRO — Temp File Scanner & Cleaner

A hacker-themed system cleaner that scans directories for temporary files (`.tmp`, `.log`, `.bak`, `.old`) and lets you selectively or batch-delete them with a live progress bar and ASCII terminal aesthetic.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Recursive scanning** — Finds all temp files in a directory tree
- **File type filters** — Select `.tmp`, `.log`, `.bak`, `.old` extensions
- **Live progress bar** — ASCII-art progress indicator during scan
- **Real-time results** — Files appear in the list as they're found
- **Selective deletion** — Delete specific files or purge all
- **Size tracking** — Shows total size of found files
- **Abort support** — Stop scanning mid-operation
- **Hacker terminal theme** — Green-on-black Courier New aesthetic

---

## 🛠️ Setup & Installation

### Step 1: No External Dependencies Needed!
Uses only Python standard library modules.

### Step 2: Run the Application
```bash
python temp_cleaner.py
```

### Step 3: Scan & Clean
1. Set the target directory
2. Select file types to scan for
3. Click **"INITIATE_SCAN()"**
4. Review found files
5. Click **"EXECUTE_PURGE_ALL()"** or select specific files

---

## 📦 Dependencies

> 🎉 **Zero pip installations required!** Uses only built-in modules.

---

## 📂 File Structure

```
18_Temp_File_Cleaner/
├── temp_cleaner.py     # Main application (TempCleanerApp)
├── requirements.txt    # (Empty — no external deps)
└── README.md           # This file
```

---

## ⚠️ Warning

**Deletion is permanent!** Files deleted by this tool are **not sent to the Recycle Bin**. Always review the file list before purging.

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
