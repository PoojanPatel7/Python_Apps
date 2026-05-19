# 📦 Python Package & Library Scanner — Environment Inspector

A comprehensive Python environment inspector that scans and displays all pip packages, standard library modules, built-in C extensions, and executables with file locations, sizes, summaries, and CSV/JSON export.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Pip packages** — Lists all installed pip packages with versions, sizes, and summaries
- **Stdlib modules** — Enumerates all standard library modules
- **Built-in modules** — Shows C extension modules compiled into Python
- **Executables** — Finds Python-related executables in PATH (pip, pytest, black, etc.)
- **Tabbed interface** — Switch between Pip, Stdlib, Built-ins, Executables, and All views
- **Search & filter** — Search by name, version, location, or summary
- **Sortable columns** — Click column headers to sort
- **Detail panel** — Shows package info, path, size, dependencies, and homepage
- **Open folder** — Open package location in file explorer
- **CSV/JSON export** — Export data for external analysis
- **Environment info** — Python version, sys.path, site-packages, and env variables
- **Premium dark UI** — Deep blue-black theme with accent colors

---

## 🛠️ Setup & Installation

### Step 1: No External Dependencies Needed!
Uses only Python standard library modules.

### Step 2: Run the Application
```bash
python package_scanner.py
```

The scanner will automatically begin scanning your Python environment on launch.

---

## 📦 Dependencies

> 🎉 **Zero pip installations required!** Uses only built-in modules: `tkinter`, `subprocess`, `importlib`, `pkgutil`, `site`.

---

## 📂 File Structure

```
19_Package_Library_Scanner/
├── package_scanner.py  # Main application (950+ lines)
├── requirements.txt    # (Empty — no external deps)
└── README.md           # This file
```

---

## 🔧 How It Works

1. **Pip scan** — Runs `pip list --format=json` then batches `pip show` for metadata
2. **Stdlib scan** — Uses `pkgutil.iter_modules()` on non-site-packages paths
3. **Built-in scan** — Reads `sys.builtin_module_names` for C extensions
4. **Executable scan** — Scans Scripts/bin directories for executables
5. Results are displayed in a sortable, filterable tree with a detail sidebar

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
