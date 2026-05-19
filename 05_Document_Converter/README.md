# 📄 Document Converter — Offline File Format Converter

A Flask-based web application that converts documents between various formats (PDF, DOCX, HTML, Markdown, etc.) using Pandoc. Runs entirely offline.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Multiple format support** — PDF, DOCX, HTML, Markdown, LaTeX, EPUB, and more
- **Drag-and-drop** file upload interface
- **Offline-first** — No internet required after setup
- **Flask web server** — Access via browser at `localhost`
- **Batch conversion** support
- **Clean responsive UI**

---

## 🛠️ Setup & Installation

### Step 1: Install Pandoc (Required)
```bash
# Windows
winget install pandoc

# Mac
brew install pandoc

# Linux
sudo apt install pandoc
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Open in Browser
Navigate to: `http://127.0.0.1:5000`

---

## 📦 Dependencies

| Package    | Purpose                           |
|------------|-----------------------------------|
| `Flask`    | Web server framework              |
| `pypandoc` | Python wrapper for Pandoc         |
| `Pandoc`   | Document conversion engine (system install) |

---

## 📂 File Structure

```
05_Document_Converter/
├── app.py              # Flask server + conversion logic
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 Supported Conversions

| Input Formats | Output Formats |
|---------------|----------------|
| DOCX, DOC     | PDF, HTML, Markdown |
| HTML          | DOCX, PDF, Markdown |
| Markdown (.md)| PDF, DOCX, HTML |
| LaTeX (.tex)  | PDF, HTML       |
| EPUB          | PDF, DOCX       |
| TXT           | All formats     |

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
