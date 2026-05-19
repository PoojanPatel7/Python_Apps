"""
╔══════════════════════════════════════════╗
║    NETSCOPE  —  LAN Device Scanner       ║
║    Discover every device on your network  ║
╚══════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk
import threading
import socket
import subprocess
import re
import time
import os
import csv
import json
from datetime import datetime

# ── OUI Vendor Lookup (common prefixes) ──
VENDOR_DB = {
    "00:50:56":"VMware","00:0C:29":"VMware","00:1C:42":"Parallels",
    "AC:DE:48":"Apple","3C:22:FB":"Apple","F0:18:98":"Apple",
    "A4:83:E7":"Apple","14:7D:DA":"Apple","F8:FF:C2":"Apple",
    "DC:A6:32":"Raspberry Pi","B8:27:EB":"Raspberry Pi",
    "00:1A:2B":"Cisco","00:26:CB":"Cisco","00:1B:2A":"Cisco",
    "00:15:5D":"Microsoft Hyper-V","00:50:F2":"Microsoft",
    "FC:FB:FB":"Cisco","30:B5:C2":"TP-Link","50:C7:BF":"TP-Link",
    "EC:08:6B":"TP-Link","60:32:B1":"TP-Link",
    "00:1E:58":"D-Link","1C:7E:E5":"D-Link",
    "00:24:01":"D-Link","28:10:7B":"D-Link",
    "2C:F0:5D":"Samsung","8C:F5:A3":"Samsung","AC:5F:3E":"Samsung",
    "00:1A:11":"Google","3C:5A:B4":"Google","F4:F5:D8":"Google",
    "A0:C9:A0":"Murata/Sony","B4:F1:DA":"LG",
    "48:A4:72":"Intel","8C:EC:4B":"Intel","3C:97:0E":"Intel",
    "00:E0:4C":"Realtek","52:54:00":"QEMU/KVM",
    "B0:BE:76":"TP-Link","C0:25:E9":"TP-Link",
    "78:44:76":"TP-Link","00:14:BF":"Linksys",
    "D8:07:B6":"TP-Link","38:D5:47":"ASUS",
    "00:1F:C6":"ASUS","74:D0:2B":"ASUS",
    "10:FE:ED":"Netgear","A4:2B:8C":"Netgear",
    "C4:3D:C7":"Netgear","6C:B0:CE":"Netgear",
    "B0:48:7A":"TP-Link","E8:DE:27":"TP-Link",
    "18:A6:F7":"TP-Link","CC:32:E5":"TP-Link",
    "20:CF:30":"ASUS","F0:79:59":"ASUS",
}

def get_vendor(mac):
    if not mac:
        return "Unknown"
    prefix = mac.upper()[:8]
    return VENDOR_DB.get(prefix, "Unknown")

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "—"

def get_local_info():
    """Get local IP and subnet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = "192.168.1.1"
    finally:
        s.close()
    # Derive subnet (assume /24)
    parts = local_ip.split(".")
    subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
    return local_ip, subnet

def arp_scan(subnet, callback, done_callback):
    """
    Scan using system ARP ping (works without admin on Windows).
    Pings each IP then reads the ARP table.
    """
    # First, ping sweep (fast, parallel)
    processes = []
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        proc = subprocess.Popen(
            ["ping", "-n", "1", "-w", "300", ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        processes.append((ip, proc))

    # Wait for all pings (with progress)
    total = len(processes)
    for idx, (ip, proc) in enumerate(processes):
        proc.wait()
        callback(progress=(idx + 1) / total)

    # Now read the ARP table
    result = subprocess.run(
        ["arp", "-a"], capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    devices = []
    pattern = re.compile(
        r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]+(?:[\w-]+)+)\s+(dynamic|static)",
        re.IGNORECASE
    )
    for line in result.stdout.splitlines():
        m = pattern.search(line)
        if m:
            ip = m.group(1)
            mac = m.group(2).replace("-", ":").upper()
            dtype = m.group(3).capitalize()
            if ip.startswith(subnet) and mac != "FF:FF:FF:FF:FF:FF":
                hostname = get_hostname(ip)
                vendor = get_vendor(mac)
                devices.append({
                    "ip": ip,
                    "mac": mac,
                    "hostname": hostname,
                    "vendor": vendor,
                    "type": dtype,
                })

    done_callback(devices)


# ── GUI ──
class NetScopeApp:
    C = {
        "bg": "#0a0a16", "card": "#111122", "border": "#1c1c36",
        "accent": "#6c5ce7", "acc_hov": "#7e70f0",
        "green": "#2ecc71", "red": "#e74c3c", "yellow": "#f1c40f",
        "cyan": "#00cec9", "text": "#e0e0f0", "dim": "#6a6a8e",
        "input": "#181830", "row_alt": "#14142a",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("NetScope — LAN Scanner")
        self.root.geometry("820x640")
        self.root.resizable(True, True)
        self.root.configure(bg=self.C["bg"])
        self.root.minsize(700, 500)

        self.devices = []
        self.scanning = False

        self._build_ui()

    def _build_ui(self):
        C = self.C

        # ── Header ──
        hdr = tk.Frame(self.root, bg=C["bg"])
        hdr.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(hdr, text="📡", fg=C["cyan"], bg=C["bg"],
                 font=("Segoe UI", 16)).pack(side="left")
        tk.Label(hdr, text="  NetScope", fg=C["text"], bg=C["bg"],
                 font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(hdr, text="LAN Device Scanner", fg=C["dim"], bg=C["bg"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 0), pady=(6, 0))

        # ── Info + Scan Row ──
        info = tk.Frame(self.root, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1)
        info.pack(fill="x", padx=24, pady=(14, 0))
        ii = tk.Frame(info, bg=C["card"])
        ii.pack(fill="x", padx=16, pady=12)

        local_ip, subnet = get_local_info()

        left = tk.Frame(ii, bg=C["card"])
        left.pack(side="left")
        tk.Label(left, text="Your IP:", fg=C["dim"], bg=C["card"],
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(left, text=local_ip, fg=C["green"], bg=C["card"],
                 font=("Consolas", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(6, 20))
        tk.Label(left, text="Subnet:", fg=C["dim"], bg=C["card"],
                 font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")
        tk.Label(left, text=f"{subnet}.0/24", fg=C["yellow"], bg=C["card"],
                 font=("Consolas", 10, "bold")).grid(row=0, column=3, sticky="w", padx=(6, 0))

        right = tk.Frame(ii, bg=C["card"])
        right.pack(side="right")

        self.scan_btn = tk.Button(right, text="🔍  Scan Network", bg=C["accent"], fg="white",
                                   activebackground=C["acc_hov"], activeforeground="white",
                                   font=("Segoe UI", 11, "bold"), bd=0, padx=18, pady=6,
                                   cursor="hand2", command=self._start_scan)
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.export_btn = tk.Button(right, text="💾", bg=C["border"], fg=C["text"],
                                     activebackground=C["dim"], font=("Segoe UI", 11),
                                     bd=0, padx=8, pady=6, cursor="hand2",
                                     command=self._export, state="disabled")
        self.export_btn.pack(side="left")

        # ── Progress Bar ──
        self.progress_frame = tk.Frame(self.root, bg=C["bg"])
        self.progress_frame.pack(fill="x", padx=24, pady=(8, 0))

        self.progress_bg = tk.Canvas(self.progress_frame, bg=C["border"],
                                      height=6, highlightthickness=0)
        self.progress_bg.pack(fill="x")
        self.progress_fill = None
        self.status_lbl = tk.Label(self.progress_frame, text="Ready — click Scan to begin",
                                    fg=C["dim"], bg=C["bg"], font=("Segoe UI", 9))
        self.status_lbl.pack(anchor="w", pady=(4, 0))

        # ── Device Table ──
        table_frame = tk.Frame(self.root, bg=C["bg"])
        table_frame.pack(fill="both", expand=True, padx=24, pady=(8, 0))

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dev.Treeview",
                         background=C["card"], foreground=C["text"],
                         fieldbackground=C["card"], borderwidth=0,
                         font=("Consolas", 10), rowheight=32)
        style.configure("Dev.Treeview.Heading",
                         background=C["border"], foreground=C["text"],
                         font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Dev.Treeview",
                   background=[("selected", C["accent"])],
                   foreground=[("selected", "white")])
        style.map("Dev.Treeview.Heading",
                   background=[("active", C["accent"])])

        cols = ("ip", "mac", "hostname", "vendor", "type")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="Dev.Treeview", selectmode="browse")

        self.tree.heading("ip", text="IP Address")
        self.tree.heading("mac", text="MAC Address")
        self.tree.heading("hostname", text="Hostname")
        self.tree.heading("vendor", text="Vendor")
        self.tree.heading("type", text="Type")

        self.tree.column("ip", width=130, minwidth=100)
        self.tree.column("mac", width=150, minwidth=130)
        self.tree.column("hostname", width=200, minwidth=100)
        self.tree.column("vendor", width=140, minwidth=80)
        self.tree.column("type", width=80, minwidth=60)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Bind right-click
        self.tree.bind("<Button-3>", self._show_context)

        # ── Bottom Bar ──
        bot = tk.Frame(self.root, bg=C["border"])
        bot.pack(fill="x", side="bottom", pady=(8, 0))
        bi = tk.Frame(bot, bg=C["card"])
        bi.pack(fill="x", padx=1, pady=1)
        self.bottom_lbl = tk.Label(bi, text="No devices found yet",
                                    fg=C["dim"], bg=C["card"],
                                    font=("Consolas", 9), pady=6)
        self.bottom_lbl.pack()

    # ── Progress ──
    def _set_progress(self, pct):
        self.progress_bg.delete("bar")
        w = self.progress_bg.winfo_width()
        if w > 1:
            self.progress_bg.create_rectangle(
                0, 0, int(w * pct), 6, fill=self.C["accent"], outline="", tags="bar")

    # ── Scan ──
    def _start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.scan_btn.config(text="⏳  Scanning...", state="disabled", bg=self.C["border"])
        self.export_btn.config(state="disabled")
        self.status_lbl.config(text="Pinging 254 hosts...", fg=self.C["yellow"])
        self.tree.delete(*self.tree.get_children())

        _, subnet = get_local_info()

        def on_progress(progress=0):
            self.root.after(0, self._set_progress, progress)
            pct = int(progress * 100)
            self.root.after(0, lambda: self.status_lbl.config(
                text=f"Scanning... {pct}%"))

        def on_done(devices):
            self.root.after(0, self._scan_done, devices)

        threading.Thread(target=arp_scan, args=(subnet, on_progress, on_done),
                         daemon=True).start()

    def _scan_done(self, devices):
        self.devices = sorted(devices, key=lambda d: list(map(int, d["ip"].split("."))))
        self.scanning = False
        self.scan_btn.config(text="🔍  Scan Network", state="normal", bg=self.C["accent"])

        local_ip, _ = get_local_info()

        self.tree.delete(*self.tree.get_children())
        for i, d in enumerate(self.devices):
            tag = "alt" if i % 2 else "normal"
            ip_display = d["ip"]
            if d["ip"] == local_ip:
                ip_display = f"{d['ip']} (You)"
            self.tree.insert("", "end", values=(
                ip_display, d["mac"], d["hostname"], d["vendor"], d["type"]
            ), tags=(tag,))

        self.tree.tag_configure("alt", background=self.C["row_alt"])
        self.tree.tag_configure("normal", background=self.C["card"])

        count = len(self.devices)
        self._set_progress(1.0)
        self.status_lbl.config(text=f"✔ Scan complete — {count} device(s) found",
                                fg=self.C["green"])
        self.bottom_lbl.config(text=f"{count} devices  •  "
                                     f"Scanned at {datetime.now().strftime('%H:%M:%S')}")

        if count > 0:
            self.export_btn.config(state="normal")

    # ── Context Menu ──
    def _show_context(self, event):
        sel = self.tree.identify_row(event.y)
        if not sel:
            return
        self.tree.selection_set(sel)
        vals = self.tree.item(sel, "values")
        ip = vals[0].split(" ")[0]  # strip "(You)"

        menu = tk.Menu(self.root, tearoff=0, bg=self.C["card"], fg=self.C["text"],
                       activebackground=self.C["accent"], activeforeground="white",
                       font=("Segoe UI", 10))
        menu.add_command(label=f"📋 Copy IP: {ip}",
                         command=lambda: self._copy(ip))
        menu.add_command(label=f"📋 Copy MAC: {vals[1]}",
                         command=lambda: self._copy(vals[1]))
        menu.add_separator()
        menu.add_command(label=f"🏓 Ping {ip}",
                         command=lambda: self._ping(ip))
        menu.post(event.x_root, event.y_root)

    def _copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _ping(self, ip):
        os.system(f'start cmd /k ping {ip}')

    # ── Export ──
    def _export(self):
        if not self.devices:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"netscope_scan_{ts}.csv")
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["ip", "mac", "hostname", "vendor", "type"])
            w.writeheader()
            w.writerows(self.devices)
        self.status_lbl.config(text=f"✔ Exported to {os.path.basename(path)}",
                                fg=self.C["green"])


# ── Launch ──
if __name__ == "__main__":
    root = tk.Tk()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 820) // 2
    y = (root.winfo_screenheight() - 640) // 2
    root.geometry(f"820x640+{x}+{y}")
    NetScopeApp(root)
    root.mainloop()
