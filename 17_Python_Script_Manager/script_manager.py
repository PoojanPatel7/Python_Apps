import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class PythonScriptManager(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Python Script Manager")
        self.geometry("1100x650")
        self.configure(bg="#f0f2f5")
        
        # State tracking
        self.found_files = []
        self.running_processes = {}  # Format: {filepath: subprocess.Popen}
        self.is_scanning = False
        
        self.setup_ui()
        
        # Start checking process status periodically
        self.check_running_processes()
        
        # Automatically load installed apps on startup
        self.load_installed_apps()

    def setup_ui(self):
        # --- Styles ---
        style = ttk.Style(self)
        style.theme_use('clam')
        
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, background="#0078D7", foreground="white")
        style.map("TButton", background=[('active', '#005A9E')])
        
        style.configure("Stop.TButton", background="#D13438")
        style.map("Stop.TButton", background=[('active', '#A80000')])
        
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e1dfdd", foreground="#323130")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="white", fieldbackground="white")
        style.map('Treeview', background=[('selected', '#cce8ff')], foreground=[('selected', 'black')])
        
        style.configure("TNotebook", background="#f0f2f5")
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 5])

        # --- Main Container ---
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Header ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(header_frame, text="Python Environment Manager", font=("Segoe UI", 18, "bold"), bg="#f0f2f5", fg="#323130")
        title_label.pack(side=tk.LEFT)

        # --- Paned Window for Split View ---
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # LEFT PANE: Notebook (Tabs for Scanner / Apps)
        # ==========================================
        left_pane = ttk.Frame(paned_window)
        paned_window.add(left_pane, weight=3) # Takes up more space

        self.notebook = ttk.Notebook(left_pane)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- TAB 1: Directory Scanner ---
        self.scanner_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.scanner_tab, text="🔍 Local Scripts Scanner")
        self.setup_scanner_tab()

        # --- TAB 2: Installed Python Apps ---
        self.apps_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.apps_tab, text="📦 Installed Python Apps")
        self.setup_apps_tab()

        # ==========================================
        # RIGHT PANE: Running Programs
        # ==========================================
        right_pane = ttk.Frame(paned_window, padding=(10, 0, 0, 0))
        paned_window.add(right_pane, weight=1)

        ttk.Label(right_pane, text="Running Programs", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 5))

        running_tree_frame = ttk.Frame(right_pane)
        running_tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        run_scroll_y = ttk.Scrollbar(running_tree_frame)
        run_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        run_scroll_x = ttk.Scrollbar(running_tree_frame, orient='horizontal')
        run_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Running Treeview Widget
        self.running_tree = ttk.Treeview(running_tree_frame, columns=("Name", "PID"), show="headings",
                                         yscrollcommand=run_scroll_y.set, xscrollcommand=run_scroll_x.set)
        self.running_tree.heading("Name", text="Script Name", anchor=tk.W)
        self.running_tree.heading("PID", text="Process ID", anchor=tk.CENTER)
        
        self.running_tree.column("Name", width=150, minwidth=100)
        self.running_tree.column("PID", width=80, minwidth=70, anchor=tk.CENTER)
        
        self.running_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        run_scroll_y.config(command=self.running_tree.yview)
        run_scroll_x.config(command=self.running_tree.xview)

        # Right Controls (Stop)
        right_controls = ttk.Frame(right_pane)
        right_controls.pack(fill=tk.X, pady=(15, 0))
        
        self.stop_btn = ttk.Button(right_controls, text="⏹ Stop Selected", style="Stop.TButton", command=self.stop_running_script)
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Select a directory and click 'Scan Now'.")
        status_label = tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9), bg="#e1dfdd", anchor="w", padx=10, pady=5)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_scanner_tab(self):
        top_bar = ttk.Frame(self.scanner_tab)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_bar, text="Directory:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Directory Path Entry
        self.dir_entry = ttk.Entry(top_bar, font=("Segoe UI", 10))
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.dir_entry.insert(0, os.path.expanduser("~")) # Default to home directory
        
        # Browse Button
        ttk.Button(top_bar, text="Browse...", command=self.browse_directory).pack(side=tk.LEFT, padx=(0, 5))
        
        # Scan Button
        self.scan_btn = ttk.Button(top_bar, text="Scan Now", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self.scanner_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(tree_frame, columns=("Name", "Path", "Status"), show="headings",
                                 yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.heading("Name", text="Script Name", anchor=tk.W)
        self.tree.heading("Path", text="File Path", anchor=tk.W)
        self.tree.heading("Status", text="Status", anchor=tk.CENTER)
        
        self.tree.column("Name", width=180, minwidth=150)
        self.tree.column("Path", width=350, minwidth=250)
        self.tree.column("Status", width=90, minwidth=90, anchor=tk.CENTER)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        self.tree.tag_configure('running', foreground='green', font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('ready', foreground='black')

        controls = ttk.Frame(self.scanner_tab)
        controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(controls, text="▶ Run Selected", command=self.run_scanned_script).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls, text="📋 Copy Path", command=lambda: self.copy_path(self.tree)).pack(side=tk.LEFT)

    def setup_apps_tab(self):
        top_bar = ttk.Frame(self.apps_tab)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_bar, text="Env Directory:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Determine default path based on OS
        if os.name == 'nt': # Windows
            default_dir = os.path.join(sys.prefix, 'Scripts')
        else: # Linux / Mac
            default_dir = os.path.join(sys.prefix, 'bin')
            
        # Directory Path Entry
        self.apps_dir_entry = ttk.Entry(top_bar, font=("Segoe UI", 10))
        self.apps_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.apps_dir_entry.insert(0, default_dir)
        
        # Browse Button
        ttk.Button(top_bar, text="Browse...", command=self.browse_apps_directory).pack(side=tk.LEFT, padx=(0, 5))
        
        # Scan Button
        ttk.Button(top_bar, text="Scan Executables", command=self.load_installed_apps).pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self.apps_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.apps_tree = ttk.Treeview(tree_frame, columns=("Name", "Path", "Status"), show="headings",
                                      yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.apps_tree.heading("Name", text="App / Command Name", anchor=tk.W)
        self.apps_tree.heading("Path", text="Executable Path", anchor=tk.W)
        self.apps_tree.heading("Status", text="Status", anchor=tk.CENTER)
        
        self.apps_tree.column("Name", width=180, minwidth=150)
        self.apps_tree.column("Path", width=350, minwidth=250)
        self.apps_tree.column("Status", width=90, minwidth=90, anchor=tk.CENTER)
        
        self.apps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.apps_tree.yview)
        tree_scroll_x.config(command=self.apps_tree.xview)
        
        self.apps_tree.tag_configure('running', foreground='green', font=("Segoe UI", 10, "bold"))
        self.apps_tree.tag_configure('ready', foreground='black')

        controls = ttk.Frame(self.apps_tab)
        controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(controls, text="▶ Run App", command=self.run_installed_app).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls, text="📋 Copy Path", command=lambda: self.copy_path(self.apps_tree)).pack(side=tk.LEFT)

    # ==========================================
    # LOGIC: Loading Installed Apps
    # ==========================================
    def browse_apps_directory(self):
        current_dir = self.apps_dir_entry.get()
        if not os.path.exists(current_dir):
            current_dir = sys.prefix
            
        directory = filedialog.askdirectory(title="Select folder to scan for executables", initialdir=current_dir)
        if directory:
            self.apps_dir_entry.delete(0, tk.END)
            self.apps_dir_entry.insert(0, directory)
            self.load_installed_apps()

    def load_installed_apps(self):
        """Finds executables inside the specified environment directory"""
        self.apps_tree.delete(*self.apps_tree.get_children())
        
        # Get path from entry field
        scripts_dir = self.apps_dir_entry.get()
            
        if not os.path.exists(scripts_dir):
            self.status_var.set(f"Could not find environment directory: {scripts_dir}")
            return
            
        count = 0
        try:
            for file in os.listdir(scripts_dir):
                full_path = os.path.join(scripts_dir, file)
                if os.path.isfile(full_path):
                    
                    # Prevent listing user-created python scripts (.py, .pyw) in the Installed Apps tab
                    if file.lower().endswith(('.py', '.pyw', '.pyc')):
                        continue
                    
                    # Filter for actual executables
                    if os.name == 'nt':
                        if not file.lower().endswith(('.exe', '.cmd', '.bat')):
                            continue
                    else:
                        if not os.access(full_path, os.X_OK):
                            continue
                    
                    status = "Running" if full_path in self.running_processes else "Ready"
                    tag = "running" if status == "Running" else "ready"
                    self.apps_tree.insert("", tk.END, iid=full_path, values=(file, full_path, status), tags=(tag,))
                    count += 1
                    
            self.status_var.set(f"Loaded {count} registered Python apps/commands (excluding local .py scripts).")
        except Exception as e:
            self.status_var.set(f"Error loading apps: {str(e)}")

    # ==========================================
    # LOGIC: Directory Scanning
    # ==========================================
    def browse_directory(self):
        current_dir = self.dir_entry.get()
        if not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")
            
        directory = filedialog.askdirectory(title="Select folder to scan for .py files", initialdir=current_dir)
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def start_scan(self):
        if self.is_scanning:
            messagebox.showwarning("Scanning", "A scan is already in progress.")
            return
            
        directory = self.dir_entry.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Invalid Directory", "The specified directory does not exist. Please enter a valid path.")
            return
            
        self.tree.delete(*self.tree.get_children())
        self.found_files.clear()
        
        self.is_scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Scanning directory: {directory} ... (This might take a moment)")
        
        threading.Thread(target=self._scan_thread, args=(directory,), daemon=True).start()

    def _scan_thread(self, directory):
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        self.found_files.append((file, full_path))
                        self.after(0, self._add_to_tree, file, full_path)
        except Exception as e:
            self.after(0, self.status_var.set, f"Error during scan: {str(e)}")
        finally:
            self.is_scanning = False
            self.after(0, self._finish_scan)

    def _add_to_tree(self, file_name, file_path):
        status = "Running" if file_path in self.running_processes else "Ready"
        tag = "running" if status == "Running" else "ready"
        self.tree.insert("", tk.END, iid=file_path, values=(file_name, file_path, status), tags=(tag,))

    def _finish_scan(self):
        self.scan_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Scan complete. Found {len(self.found_files)} Python programs.")

    # ==========================================
    # LOGIC: Running & Stopping
    # ==========================================
    def copy_path(self, target_tree):
        selected = target_tree.focus()
        if selected:
            self.clipboard_clear()
            self.clipboard_append(selected)
            self.update() 
            self.status_var.set(f"Copied path to clipboard: {selected}")
        else:
            messagebox.showinfo("Select Item", "Please select an item to copy its path.")

    def _execute_process(self, filepath, execution_args, working_dir):
        if filepath in self.running_processes:
            messagebox.showinfo("Already Running", "This process is already running!")
            return

        try:
            process = subprocess.Popen(execution_args, cwd=working_dir)
            
            self.running_processes[filepath] = process
            self.update_script_status(filepath, "Running")
            
            self.running_tree.insert("", tk.END, iid=filepath, values=(os.path.basename(filepath), process.pid))
            self.status_var.set(f"Started: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to run:\n{e}")

    def run_scanned_script(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showinfo("Select Script", "Please select a script from the list to run.")
            return
            
        # For raw .py files, we must execute them with the Python interpreter
        self._execute_process(selected_item, [sys.executable, selected_item], os.path.dirname(selected_item))

    def run_installed_app(self):
        selected_item = self.apps_tree.focus()
        if not selected_item:
            messagebox.showinfo("Select App", "Please select an app from the list to run.")
            return
            
        # Registered apps are already executables (e.g. .exe on Windows)
        # We can run them directly without prefixing sys.executable
        self._execute_process(selected_item, [selected_item], os.path.expanduser("~"))

    def stop_running_script(self):
        selected_item = self.running_tree.focus()
        if not selected_item:
            messagebox.showinfo("Select Process", "Please select a script from the Running Programs list to stop.")
            return
        
        if selected_item in self.running_processes:
            process = self.running_processes[selected_item]
            try:
                process.terminate() 
                self.status_var.set(f"Stopped: {os.path.basename(selected_item)}")
            except Exception as e:
                messagebox.showerror("Stop Error", f"Failed to stop process:\n{e}")

    def update_script_status(self, filepath, status):
        tag = 'running' if status == 'Running' else 'ready'
        
        # Update in Scanner Tree if it exists there
        if self.tree.exists(filepath):
            values = self.tree.item(filepath, "values")
            self.tree.item(filepath, values=(values[0], values[1], status), tags=(tag,))
            
        # Update in Apps Tree if it exists there
        if self.apps_tree.exists(filepath):
            values = self.apps_tree.item(filepath, "values")
            self.apps_tree.item(filepath, values=(values[0], values[1], status), tags=(tag,))

    def check_running_processes(self):
        finished_scripts = []
        
        for filepath, process in self.running_processes.items():
            if process.poll() is not None:  # Process has ended
                finished_scripts.append(filepath)
                
        # Clean up finished scripts
        for filepath in finished_scripts:
            del self.running_processes[filepath]
            self.update_script_status(filepath, "Ready")
            
            if self.running_tree.exists(filepath):
                self.running_tree.delete(filepath)
            
        self.after(1000, self.check_running_processes)

if __name__ == "__main__":
    app = PythonScriptManager()
    app.mainloop()