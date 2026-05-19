# 📡 WiFi & BLE Scanner — Network & Bluetooth Discovery Tool

A script for scanning nearby Wi-Fi networks and Bluetooth Low Energy (BLE) devices using native platform commands and the `bleak` library.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **WiFi scanning** — Discovers all nearby wireless networks
- **Signal strength** — Shows RSSI/signal quality for each network
- **Security type** — Identifies WPA2, WPA3, Open networks
- **BLE device scanning** — Finds Bluetooth Low Energy devices
- **Cross-platform** — Uses native OS commands (netsh on Windows)

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Scanner
```bash
python scanner.py
```

---

## 📦 Dependencies

| Package | Purpose                          |
|---------|----------------------------------|
| `bleak` | Bluetooth Low Energy scanning    |

---

## 📂 File Structure

```
10_WiFi_BLE_Scanner/
├── scanner.py          # Main scanner script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
