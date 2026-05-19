# 🌐 Advanced Web Scraper — JavaScript-Rendered Page Scraper

An advanced web scraping tool using **Playwright** for handling JavaScript-rendered content and **BeautifulSoup** for HTML parsing. Capable of scraping dynamic single-page applications.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **JavaScript rendering** — Handles SPAs and dynamically loaded content
- **Playwright browser engine** — Chromium, Firefox, or WebKit
- **BeautifulSoup parsing** — Extract specific HTML elements
- **Headless mode** — Run without visible browser window
- **Wait strategies** — Waits for page load completion before scraping
- **Export to multiple formats** — JSON, CSV, or console output

---

## 🛠️ Setup & Installation

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install Playwright Browsers
```bash
playwright install
```

### Step 3: Run the Scraper
```bash
python advanced_scrape.py
```

---

## 📦 Dependencies

| Package          | Purpose                              |
|------------------|--------------------------------------|
| `playwright`     | Browser automation for JS rendering  |
| `beautifulsoup4` | HTML parsing                         |
| `lxml`           | Fast parser backend                  |

---

## 📂 File Structure

```
09_Advanced_Web_Scraper/
├── advanced_scrape.py  # Main scraping script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
