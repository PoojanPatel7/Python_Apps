# 🖥️ Task Manager — Process Monitor & Controller

A custom-built Windows Task Manager alternative with real-time process monitoring, CPU/memory tracking, and a dark premium UI built with tkinter.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Live process list** with PID, name, CPU%, memory usage
- **Process control** — Kill, suspend, and resume processes
- **System stats dashboard** — CPU, RAM, disk, and network usage
- **Auto-refresh** with configurable intervals
- **Search & filter** processes by name
- **Dark obsidian theme** with premium styling

---

## 🛠️ Setup & Installation

### Step 1: Install Dependencies
```bash
pip install psutil Pillow
```

### Step 2: Generate App Icon (Optional)
```bash
python create_icon.py
```

### Step 3: Run the Application
```bash
python main.py
```

---

## 📦 Dependencies

| Package  | Purpose                               |
|----------|---------------------------------------|
| `psutil` | Process enumeration & system stats    |
| `Pillow` | Icon generation (`create_icon.py`)    |

---

## 📂 File Structure

```
02_Task_Manager/
├── main.py            # Main application (TaskPulseApp)
├── create_icon.py     # Icon generator
├── icon.ico           # Generated app icon
├── icon.png           # Generated PNG icon
└── README.md          # This file
```

---

## 🔧 How It Works

1. **`psutil.process_iter()`** enumerates all running processes
2. Each process's CPU and memory are sampled in a background thread
3. The Treeview widget displays sortable process columns
4. Right-click context menu provides kill/suspend/resume actions
5. System-wide stats (CPU, RAM, Disk) update in the header bar

---

## ⚠️ Note

- **Run as Administrator** for full process control (killing system processes)
- Some protected processes may show "Access Denied" when terminated

---

## 👤 Author

**Poojan Patel** — [GitHub](https://github.com/PoojanPatel7)
