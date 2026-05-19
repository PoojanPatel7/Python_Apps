# 📊 Attendance Scraper — Automated Attendance Data Extractor

A suite of automated web scrapers designed to extract attendance records from attendance management systems (AttendMate / Vercel-hosted portals) using Selenium, with automated Excel export.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Automated browser control** via Selenium WebDriver
- **Headless mode** for background scraping
- **Dynamic dropdown handling** — Selects semester, subject, and date ranges
- **Pagination support** — Handles multi-page tables
- **Excel export** — Generates `.xlsx` files with pandas/openpyxl
- **Multiple scraper versions** for different portal variations
- **Error recovery** with explicit waits and retry logic

---

## 📁 Included Scripts

| File | Description |
|------|-------------|
| `attendance_scraper.py` | Primary scraper — full pagination & dropdown automation |
| `scraper_v2.py` | Optimized version with enhanced filtering |
| `scraper_v3.py` | Subject-specific attendance filtering |
| `scraper_simple.py` | Minimal scraper — direct table-to-pandas pipeline |

---

## 🛠️ Setup & Installation

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install ChromeDriver
The scraper uses `webdriver-manager` to auto-download the correct ChromeDriver:
```bash
pip install webdriver-manager
```

### Step 3: Configure Target URL
Open the scraper file and set the target URL:
```python
TARGET_URL = "https://your-attendance-portal.vercel.app"
```

### Step 4: Run a Scraper
```bash
# Full-featured scraper
python attendance_scraper.py

# Simple direct-export scraper
python scraper_simple.py
```

---

## 📦 Dependencies

| Package             | Purpose                              |
|---------------------|--------------------------------------|
| `selenium`          | Browser automation                   |
| `webdriver-manager` | Auto-download ChromeDriver           |
| `pandas`            | Data manipulation & Excel creation   |
| `openpyxl`          | Excel file writing engine            |
| `beautifulsoup4`    | HTML parsing (some versions)         |

---

## 📂 File Structure

```
04_Attendance_Scraper/
├── attendance_scraper.py   # Primary full-featured scraper
├── scraper_v2.py           # Enhanced filtering version
├── scraper_v3.py           # Subject-specific filtering
├── scraper_simple.py       # Minimal table→Excel scraper
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔧 How It Works

1. **Selenium** launches a Chrome browser (headless or visible)
2. Navigates to the attendance portal URL
3. **Automates dropdowns** — Selects semester, subject, and date range
4. **Waits for table** data to load using explicit WebDriver waits
5. **Parses HTML table** rows into a pandas DataFrame
6. Handles **pagination** by clicking "Next" until all pages are scraped
7. **Exports to Excel** (`.xlsx`) with formatted columns

---

## ⚠️ Important Notes

- **No hardcoded credentials** — Configure your own login details
- Ensure the target portal is accessible from your network
- Chrome must be installed on your system
- Running in **headless mode** is faster but non-visual

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
