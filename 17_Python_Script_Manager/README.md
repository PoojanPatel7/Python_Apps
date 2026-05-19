# 🐍 Python Script Manager — Environment & Script Runner

A Python environment manager with a split-pane GUI for scanning directories for `.py` files, viewing installed Python executables, and running/stopping scripts with live process tracking.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Directory scanner** — Recursively finds all `.py` files in a folder
- **Installed apps tab** — Lists Python executables (pip, pytest, black, etc.)
- **Run scripts** — Launch any Python script from the GUI
- **Running process panel** — Track active processes with PID
- **Stop processes** — Terminate running scripts with one click
- **Auto-refresh** — Periodic check of running process status
- **Split-pane layout** — Scanner on the left, running programs on the right

---

## 🛠️ Setup & Installation

### Step 1: No External Dependencies Needed!
This app uses only Python standard library modules.

### Step 2: Run the Application
```bash
python script_manager.py
```

---

## 📦 Dependencies

> 🎉 **Zero pip installations required!** Uses only built-in modules: `tkinter`, `subprocess`, `os`, `threading`.

---

## 📂 File Structure

```
17_Python_Script_Manager/
├── script_manager.py   # Main application (PythonScriptManager)
├── requirements.txt    # (Empty — no external deps)
└── README.md           # This file
```

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
