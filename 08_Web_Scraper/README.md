# 🕷️ Web Scraper — Visual Web Data Extractor

A modular web scraping tool with a tkinter GUI that lets you analyze any website's structure and extract specific data categories (links, images, tables, text) into Excel spreadsheets.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Visual GUI** — Enter URL, analyze, and select what to scrape
- **Page structure analysis** — Detects available data types (links, images, tables, etc.)
- **Category selection** — Choose specific elements to extract
- **Excel export** — Formatted `.xlsx` output with openpyxl
- **BeautifulSoup parsing** — Robust HTML parsing
- **Request handling** — Proper headers, timeouts, and error handling

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python web_scraper.py
```

---

## 📦 Dependencies

| Package          | Purpose                           |
|------------------|-----------------------------------|
| `requests`       | HTTP requests                     |
| `beautifulsoup4` | HTML parsing                      |
| `pandas`         | Data structuring                  |
| `openpyxl`       | Excel file creation               |
| `lxml`           | Fast HTML/XML parser              |

---

## 📂 File Structure

```
08_Web_Scraper/
├── web_scraper.py      # Main application (WebScraperApp)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
