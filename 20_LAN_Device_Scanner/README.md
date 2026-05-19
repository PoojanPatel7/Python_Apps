# 📡 NetScope — LAN Device Scanner

A network device discovery tool that performs ARP-based scanning to find all devices on your local network, displaying IP addresses, MAC addresses, hostnames, and vendor information.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **ARP-based scanning** — Pings all 254 hosts then reads the ARP table
- **Vendor detection** — Identifies device manufacturers from MAC address prefixes (OUI database)
- **Hostname resolution** — Resolves IP addresses to hostnames
- **Progress bar** — Real-time scan progress indicator
- **Sortable table** — IP, MAC, hostname, vendor, and connection type
- **Right-click context menu** — Copy IP, copy MAC, or ping a device
- **CSV export** — Save scan results to a CSV file
- **Dark themed UI** — Professional dark interface with accent colors
- **Auto-subnet detection** — Automatically detects your network subnet

---

## 🛠️ Setup & Installation

### Step 1: No External Dependencies Needed!
Uses only Python standard library modules.

### Step 2: Run the Application
```bash
python lan_scanner.py
```

### Step 3: Scan Your Network
Click **"🔍 Scan Network"** and wait for the scan to complete (typically 30-60 seconds for a /24 subnet).

---

## 📦 Dependencies

> 🎉 **Zero pip installations required!** Uses only built-in modules: `tkinter`, `socket`, `subprocess`, `re`.

---

## 📂 File Structure

```
20_LAN_Device_Scanner/
├── lan_scanner.py      # Main application (NetScopeApp)
├── requirements.txt    # (Empty — no external deps)
└── README.md           # This file
```

---

## 🔧 How It Works

1. **Auto-detects** your local IP and /24 subnet
2. Sends **parallel ICMP pings** to all 254 addresses (1-254)
3. Reads the **system ARP table** (`arp -a`) after ping sweep
4. **Parses ARP entries** with regex for IP, MAC, and type
5. **Resolves hostnames** via `socket.gethostbyaddr()`
6. **Looks up vendors** using a built-in OUI (MAC prefix) database

### Built-in Vendor Database
Includes MAC prefixes for: Apple, Samsung, Google, Intel, Realtek, TP-Link, Cisco, D-Link, ASUS, Netgear, VMware, Raspberry Pi, and more.

---

## ⚠️ Note

- Windows only (uses `ping -n 1 -w 300` and Windows ARP format)
- Some devices may not respond to ICMP pings and won't appear in results
- Scanning a /24 subnet takes approximately 30-60 seconds

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
