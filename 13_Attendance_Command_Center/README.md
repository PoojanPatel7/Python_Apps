# 🎯 Attendance Command Center — Integrated Scraper + Dashboard

A comprehensive Streamlit-powered command center that integrates the attendance scraper engine with a real-time data visualization dashboard. Scrape, analyze, and visualize attendance data in one unified interface.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **One-click scraping** — Trigger attendance scraping from the UI
- **Fast headless scraper** — Optimized ChromeOptions for speed
- **Dynamic dropdown automation** — Semester, subject, date range selection
- **Live data visualization** — Charts update after each scrape
- **Excel export** — Download scraped data as `.xlsx`
- **Session management** — Track scraping history

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Install ChromeDriver
```bash
pip install webdriver-manager
```

### Step 3: Run the Command Center
```bash
streamlit run command_center.py
```

---

## 📦 Dependencies

| Package             | Purpose                           |
|---------------------|-----------------------------------|
| `streamlit`         | Web dashboard framework           |
| `selenium`          | Browser automation                |
| `webdriver-manager` | Auto ChromeDriver download        |
| `pandas`            | Data manipulation                 |
| `openpyxl`          | Excel file operations             |
| `plotly`            | Interactive charting              |

---

## 📂 File Structure

```
13_Attendance_Command_Center/
├── command_center.py   # Streamlit + Selenium integrated app
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🔧 How It Works

1. **Configure** the target portal URL and credentials in the UI
2. Click **"Deploy Fast Scraper"** to launch headless Chrome
3. Selenium **automates navigation** through dropdowns and pagination
4. Scraped data is loaded into a **pandas DataFrame**
5. **Plotly charts** render attendance summaries in real-time
6. **Export** the data as an Excel file for offline analysis

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
