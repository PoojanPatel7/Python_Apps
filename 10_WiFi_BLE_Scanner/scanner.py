import sys
import subprocess
import platform
import asyncio

# Attempt to load the bleak library for Bluetooth
try:
    from bleak import BleakScanner
except ImportError:
    print("Error: The 'bleak' library is not installed.")
    print("Please run: pip install bleak")
    sys.exit(1)

def scan_wifi():
    print("\n" + "="*70)
    print("📶 SCANNED WI-FI NETWORKS")
    print("="*70)
    
    os_name = platform.system()
    
    if os_name == "Windows":
        try:
            # Run the Windows native netsh command
            output = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"], text=True, encoding='utf-8', errors='ignore')
            networks = []
            current_network = {}
            
            # Parse the text output
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith("SSID"):
                    if current_network.get("SSID"):
                        networks.append(current_network)
                        current_network = {}
                    current_network["SSID"] = line.split(":", 1)[1].strip()
                elif line.startswith("BSSID"):
                    current_network["BSSID"] = line.split(":", 1)[1].strip()
                elif line.startswith("Signal"):
                    current_network["Signal"] = line.split(":", 1)[1].strip()
                elif line.startswith("Authentication"):
                    current_network["Auth"] = line.split(":", 1)[1].strip()
            
            # Append the last collected network
            if current_network:
                networks.append(current_network)
                
            # Print parsed networks
            for net in networks:
                ssid = net.get("SSID", "")
                if not ssid: ssid = "Hidden/Unknown"
                
                print(f"SSID: {ssid[:20]:<20} | MAC: {net.get('BSSID', 'N/A'):<17} | Signal: {net.get('Signal', 'N/A'):<5} | Sec: {net.get('Auth', 'N/A')}")
                
        except Exception as e:
            print(f"Failed to scan Wi-Fi on Windows: {e}")
            
    elif os_name == "Linux":
        try:
            # Run the Linux NetworkManager command
            output = subprocess.check_output(["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY", "dev", "wifi", "list"], text=True)
            for line in output.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 4:
                    ssid = parts[0] if parts[0] else "Hidden"
                    bssid = parts[1]
                    signal = parts[2]
                    sec = parts[3]
                    print(f"SSID: {ssid[:20]:<20} | MAC: {bssid:<17} | Signal: {signal}%  | Sec: {sec}")
        except Exception as e:
            print(f"Failed to scan Wi-Fi on Linux. Ensure NetworkManager is running. Error: {e}")
            
    elif os_name == "Darwin": # macOS
        try:
            # Run the macOS hidden airport utility
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            output = subprocess.check_output([airport_path, "-s"], text=True)
            lines = output.split('\n')[1:] # Skip the header line
            for line in lines:
                if line.strip():
                    parts = line.split()
                    ssid = parts[0]
                    mac = parts[1]
                    rssi = parts[2]
                    print(f"SSID: {ssid[:20]:<20} | MAC: {mac:<17} | Signal (RSSI): {rssi} dBm")
        except Exception as e:
            print(f"Failed to scan Wi-Fi on macOS: {e}")
    else:
        print(f"Wi-Fi scanning is not natively supported in this script for {os_name}")

async def scan_bluetooth():
    print("\n" + "="*70)
    print("🔵 SCANNED BLUETOOTH (BLE) DEVICES")
    print("="*70)
    print("Scanning... (This takes about 8 seconds to listen for signals)\n")
    
    try:
        # Listen for BLE beacons
        devices = await BleakScanner.discover(timeout=8.0)
        
        if not devices:
            print("No Bluetooth devices found nearby.")
            return
            
        for device in devices:
            name = device.name if device.name else "Unknown Device"
            # Bluetooth addresses on MacOS are UUIDs, on Windows/Linux they are MAC Addresses
            print(f"Name: {name[:20]:<20} | Address/MAC: {device.address:<17} | RSSI: {device.rssi} dBm")
            
    except Exception as e:
        print(f"Failed to scan Bluetooth. Ensure your device has Bluetooth enabled. Error: {e}")

if __name__ == "__main__":
    try:
        # Run Wi-Fi scan synchronously
        scan_wifi()
        
        # Run Bluetooth scan asynchronously 
        asyncio.run(scan_bluetooth())
        
        print("\nScan Complete.")
        
    except KeyboardInterrupt:
        print("\nScan aborted by user.")