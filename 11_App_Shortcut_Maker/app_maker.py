import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import win32com.client

class PythonAppManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Start Menu App Creator")
        self.root.geometry("650x550")
        self.root.configure(padx=20, pady=20)

        self.icon_path = None
        self.found_files = []

        # --- UI SETUP ---
        
        # 1. Scanning Section
        tk.Label(root, text="1. Find Python Scripts", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(root, text="Select a folder to scan (Scanning the whole C: drive takes too long!)").pack(anchor="w")
        
        scan_frame = tk.Frame(root)
        scan_frame.pack(fill="x", pady=5)
        self.btn_scan = tk.Button(scan_frame, text="Browse & Scan Folder", command=self.start_scan_thread)
        self.btn_scan.pack(side="left")
        
        self.lbl_status = tk.Label(scan_frame, text="Waiting...", fg="gray")
        self.lbl_status.pack(side="left", padx=10)

        # 2. List of Files
        self.listbox = tk.Listbox(root, height=12, width=80)
        self.listbox.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(self.listbox, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # 3. App Configuration Section
        tk.Label(root, text="2. Configure App Details", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 0))
        
        config_frame = tk.Frame(root)
        config_frame.pack(fill="x", pady=5)
        
        tk.Label(config_frame, text="App Name (Start Menu):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_name = tk.Entry(config_frame, width=40)
        self.entry_name.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(config_frame, text="App Icon (.ico):").grid(row=1, column=0, sticky="w", pady=5)
        self.btn_icon = tk.Button(config_frame, text="Select Icon Image", command=self.select_icon)
        self.btn_icon.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        self.lbl_icon_path = tk.Label(config_frame, text="No icon selected (Default Python icon will be used)", fg="gray")
        self.lbl_icon_path.grid(row=1, column=2, sticky="w")

        # 4. Action Button
        self.btn_create = tk.Button(root, text="Create Start Menu App!", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=self.create_shortcut)
        self.btn_create.pack(pady=20, fill="x")

    def start_scan_thread(self):
        folder_to_scan = filedialog.askdirectory(title="Select Folder to Scan for .py files")
        if not folder_to_scan:
            return
            
        self.listbox.delete(0, tk.END)
        self.found_files.clear()
        self.btn_scan.config(state="disabled")
        self.lbl_status.config(text=f"Scanning {folder_to_scan}...", fg="blue")
        
        # Run scan in a separate thread so the GUI doesn't freeze
        threading.Thread(target=self.scan_directory, args=(folder_to_scan,), daemon=True).start()

    def scan_directory(self, directory):
        for root_dir, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root_dir, file)
                    self.found_files.append(full_path)
                    # Update GUI from thread safely
                    self.root.after(0, self.listbox.insert, tk.END, f"{file}  -->  ({full_path})")
        
        self.root.after(0, self.finish_scan)

    def finish_scan(self):
        self.btn_scan.config(state="normal")
        self.lbl_status.config(text=f"Scan complete. Found {len(self.found_files)} files.", fg="green")

    def select_icon(self):
        # Windows shortcuts require .ico files
        file = filedialog.askopenfilename(title="Select Icon", filetypes=[("Icon Files", "*.ico")])
        if file:
            self.icon_path = file
            self.lbl_icon_path.config(text=os.path.basename(file), fg="black")

    def create_shortcut(self):
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a Python script from the list first.")
            return
            
        app_name = self.entry_name.get().strip()
        if not app_name:
            messagebox.showwarning("Warning", "Please enter an App Name.")
            return

        # Get the actual file path from our list
        target_script = self.found_files[selected_index[0]]
        
        try:
            # Connect to Windows Shell
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # Get the path to the user's Start Menu Programs folder
            start_menu = shell.SpecialFolders("Programs")
            shortcut_path = os.path.join(start_menu, f"{app_name}.lnk")
            
            # Create the shortcut
            shortcut = shell.CreateShortCut(shortcut_path)
            
            # Use the current Python executable to run the script
            shortcut.Targetpath = sys.executable 
            shortcut.Arguments = f'"{target_script}"'
            
            # Set the icon if selected
            if self.icon_path:
                shortcut.IconLocation = self.icon_path
                
            # Set starting directory to the script's folder
            shortcut.WorkingDirectory = os.path.dirname(target_script)
            
            shortcut.save()
            
            messagebox.showinfo("Success!", f"'{app_name}' has been added to your Start Menu!\n\nPress the Windows Key and type its name to find it.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create shortcut: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonAppManager(root)
    root.mainloop()