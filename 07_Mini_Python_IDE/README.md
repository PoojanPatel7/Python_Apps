# 💻 Mini Python IDE — Lightweight Code Editor

A lightweight Python IDE built with tkinter featuring `jedi`-based intelligent autocomplete, syntax highlighting, and automatic pip installation for missing modules.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Intelligent autocomplete** powered by `jedi` library
- **Run scripts directly** within the IDE
- **Auto-pip install** — Automatically installs missing modules on import errors
- **Syntax highlighting** with customizable colors
- **Output console** — See print output and errors inline
- **Dark themed editor** with monospace fonts
- **File open/save** with standard keyboard shortcuts

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the IDE
```bash
python my_ide.py
```

---

## 📦 Dependencies

| Package | Purpose                        |
|---------|--------------------------------|
| `jedi`  | Python autocompletion engine   |

---

## 📂 File Structure

```
07_Mini_Python_IDE/
├── my_ide.py           # Main IDE application (MiniPythonIDE)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 Key Features Explained

### Auto-Pip Install
When you run a script that imports a module you haven't installed, the IDE:
1. Detects the `ModuleNotFoundError`
2. Automatically runs `pip install <module_name>`
3. Re-runs your script

### Jedi Autocomplete
Press `Ctrl+Space` or type `.` after an object to trigger intelligent completions.

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
