# 🔗 App Shortcut Maker — Windows Start Menu Shortcut Creator

A utility script for creating Windows Start Menu shortcuts for Python scripts, with custom icon support and automatic shortcut management.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Create Start Menu shortcuts** for any Python script
- **Custom icon support** — Use `.ico` files for your shortcuts
- **Auto-detection** of Python interpreter path
- **Working directory configuration**
- **Shortcut management** — List and remove created shortcuts

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app_maker.py
```

---

## 📦 Dependencies

| Package    | Purpose                         |
|------------|---------------------------------|
| `pywin32`  | Windows COM interface for shortcuts |
| `Pillow`   | Icon handling                   |

---

## 📂 File Structure

```
11_App_Shortcut_Maker/
├── app_maker.py        # Shortcut creation utility
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## ⚠️ Note

This tool is **Windows-only** as it uses Windows COM objects to create `.lnk` shortcut files.

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
