import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

class TempCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TERMINAL // SYS.CLEANER_PRO")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # --- Hacker Theme Colors & Fonts ---
        self.BG_COLOR = "#050505"
        self.FG_COLOR = "#00FF00"
        self.ACCENT_COLOR = "#003300"
        self.WARN_COLOR = "#FF0000"
        self.FONT_MAIN = ("Courier New", 10, "bold")
        self.FONT_TITLE = ("Courier New", 12, "bold")
        
        self.root.configure(bg=self.BG_COLOR)
        
        # State Variables
        self.found_files = []
        self.is_scanning = False
        self.stop_requested = False
        self.scanned_bytes = 0
        self.total_bytes_to_scan = 1
        self.last_displayed_index = 0
        self.blink_state = True
        
        self.setup_ui()

    def create_hacker_button(self, parent, text, command, **kwargs):
        """Helper to create stylized buttons"""
        btn = tk.Button(parent, text=text, command=command,
                        bg=self.ACCENT_COLOR, fg=self.FG_COLOR,
                        activebackground=self.FG_COLOR, activeforeground=self.BG_COLOR,
                        font=self.FONT_MAIN, relief=tk.FLAT, borderwidth=1,
                        highlightbackground=self.FG_COLOR, highlightthickness=1, **kwargs)
        return btn

    def format_size(self, size_in_bytes):
        """Converts bytes to a human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} PB"

    def generate_progress_bar(self, percent):
        """Generates a text-based ASCII progress bar."""
        bar_length = 40
        filled_len = int(bar_length * percent // 100)
        bar = '█' * filled_len + '-' * (bar_length - filled_len)
        return f"[{bar}] {percent:5.1f}%"

    def setup_ui(self):
        # --- Top Frame: Directory Selection ---
        top_frame = tk.Frame(self.root, bg=self.BG_COLOR, pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="TARGET_DIR >", bg=self.BG_COLOR, fg=self.FG_COLOR, font=self.FONT_TITLE).pack(side=tk.LEFT, padx=(0, 5))
        
        self.path_var = tk.StringVar(value="C:\\" if os.name == "nt" else "/")
        self.path_entry = tk.Entry(top_frame, textvariable=self.path_var, width=50, 
                                   bg="#111", fg=self.FG_COLOR, insertbackground=self.FG_COLOR,
                                   font=self.FONT_MAIN, relief=tk.FLAT, highlightthickness=1, highlightbackground=self.ACCENT_COLOR)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
        
        self.create_hacker_button(top_frame, "BROWSE_LOCAL()", self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        # --- Options Frame: File Types ---
        options_frame = tk.LabelFrame(self.root, text=">> SELECT_PAYLOADS", bg=self.BG_COLOR, fg=self.FG_COLOR, font=self.FONT_MAIN, pady=10, padx=10, bd=1)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ext_vars = {
            ".tmp": tk.BooleanVar(value=True),
            ".log": tk.BooleanVar(value=False),
            ".bak": tk.BooleanVar(value=False),
            ".old": tk.BooleanVar(value=False)
        }
        
        for i, (ext, var) in enumerate(self.ext_vars.items()):
            cb = tk.Checkbutton(options_frame, text=ext.upper(), variable=var,
                                bg=self.BG_COLOR, fg=self.FG_COLOR, selectcolor=self.BG_COLOR,
                                activebackground=self.BG_COLOR, activeforeground=self.FG_COLOR,
                                font=self.FONT_MAIN)
            cb.grid(row=0, column=i, padx=10, pady=2)
            
        tk.Label(options_frame, text="WARNING: BYPASSING .LOG OR .BAK PROTOCOLS MAY CORRUPT SYSTEM FILES.", 
                 bg=self.BG_COLOR, fg=self.WARN_COLOR, font=("Courier New", 8, "bold")).grid(row=1, column=0, columnspan=4, pady=(5, 0), sticky=tk.W)

        # --- Scan Controls Frame ---
        scan_frame = tk.Frame(self.root, bg=self.BG_COLOR, pady=10, padx=10)
        scan_frame.pack(fill=tk.X)
        
        self.scan_btn = self.create_hacker_button(scan_frame, "INITIATE_SCAN()", self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = self.create_hacker_button(scan_frame, "ABORT_OPERATION", self.stop_scan)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_btn.config(state=tk.DISABLED)
        
        self.progress_var = tk.StringVar(value=self.generate_progress_bar(0))
        tk.Label(scan_frame, textvariable=self.progress_var, bg=self.BG_COLOR, fg=self.FG_COLOR, font=self.FONT_MAIN).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value="SYSTEM.READY_")
        tk.Label(scan_frame, textvariable=self.status_var, width=35, bg=self.BG_COLOR, fg=self.FG_COLOR, font=self.FONT_MAIN, anchor="e").pack(side=tk.RIGHT, padx=10)

        # --- Results Frame ---
        results_frame = tk.Frame(self.root, bg=self.BG_COLOR, padx=10, pady=5)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y = tk.Scrollbar(results_frame, bg=self.BG_COLOR, troughcolor=self.BG_COLOR, activebackground=self.FG_COLOR)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(results_frame, orient=tk.HORIZONTAL, bg=self.BG_COLOR, troughcolor=self.BG_COLOR, activebackground=self.FG_COLOR)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.listbox = tk.Listbox(results_frame, selectmode=tk.EXTENDED, 
                                  yscrollcommand=scrollbar_y.set, 
                                  xscrollcommand=scrollbar_x.set,
                                  bg="#0A0A0A", fg=self.FG_COLOR, 
                                  selectbackground=self.FG_COLOR, selectforeground=self.BG_COLOR,
                                  font=("Courier New", 9), relief=tk.FLAT, highlightthickness=1, highlightbackground=self.ACCENT_COLOR)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar_y.config(command=self.listbox.yview)
        scrollbar_x.config(command=self.listbox.xview)

        # --- Bottom Frame: Actions ---
        bottom_frame = tk.Frame(self.root, bg=self.BG_COLOR, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)
        
        self.info_var = tk.StringVar(value="VULNERABILITIES: 0 | TOTAL_PAYLOAD: 0.00 B")
        tk.Label(bottom_frame, textvariable=self.info_var, bg=self.BG_COLOR, fg=self.FG_COLOR, font=self.FONT_TITLE).pack(side=tk.LEFT)
        
        self.delete_all_btn = self.create_hacker_button(bottom_frame, "EXECUTE_PURGE_ALL()", self.delete_all)
        self.delete_all_btn.pack(side=tk.RIGHT, padx=5)
        self.delete_all_btn.config(state=tk.DISABLED)
        
        self.delete_sel_btn = self.create_hacker_button(bottom_frame, "PURGE_SELECTED()", self.delete_selected)
        self.delete_sel_btn.pack(side=tk.RIGHT, padx=5)
        self.delete_sel_btn.config(state=tk.DISABLED)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="SELECT_TARGET_NODE")
        if folder:
            self.path_var.set(folder)

    def stop_scan(self):
        if self.is_scanning:
            self.stop_requested = True
            self.status_var.set("ABORTING_SEQUENCE...")
            self.stop_btn.config(state=tk.DISABLED)

    def start_scan(self):
        if self.is_scanning:
            return
            
        target_dir = self.path_var.get()
        if not os.path.exists(target_dir):
            messagebox.showerror("CRITICAL_ERROR", "TARGET_NODE_NOT_FOUND")
            return

        self.active_exts = [ext for ext, var in self.ext_vars.items() if var.get()]
        if not self.active_exts:
            messagebox.showwarning("WARNING", "NO_PAYLOAD_EXTENSIONS_SELECTED")
            return

        try:
            disk_usage = shutil.disk_usage(target_dir)
            self.total_bytes_to_scan = disk_usage.used
        except Exception:
            self.total_bytes_to_scan = 1 

        # UI Updates
        self.found_files.clear()
        self.scanned_bytes = 0
        self.last_displayed_index = 0
        self.listbox.delete(0, tk.END)
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.delete_all_btn.config(state=tk.DISABLED)
        self.delete_sel_btn.config(state=tk.DISABLED)
        self.progress_var.set(self.generate_progress_bar(0))
        self.is_scanning = True
        self.stop_requested = False

        # Run scan
        self.scan_thread = threading.Thread(target=self.scan_directory_thread, args=(target_dir,), daemon=True)
        self.scan_thread.start()
        
        # Start UI updater loop
        self.root.after(100, self.update_ui_loop)

    def scan_directory_thread(self, target_dir):
        try:
            for root, dirs, files in os.walk(target_dir):
                if self.stop_requested:
                    break
                    
                for file in files:
                    if self.stop_requested:
                        break
                        
                    full_path = os.path.join(root, file)
                    
                    try:
                        size = os.path.getsize(full_path)
                        self.scanned_bytes += size
                    except OSError:
                        pass
                        
                    if any(file.lower().endswith(ext) for ext in self.active_exts):
                        self.found_files.append(full_path)
        except Exception as e:
            print(f"KERNEL_PANIC: {e}")
        
        self.is_scanning = False

    def update_ui_loop(self):
        # Update live listbox
        current_len = len(self.found_files)
        if current_len > self.last_displayed_index:
            # Batch insert new files
            new_files = self.found_files[self.last_displayed_index:current_len]
            self.listbox.insert(tk.END, *new_files)
            self.listbox.see(tk.END) # Auto-scroll animation effect
            self.last_displayed_index = current_len

        # Update stats
        size_str = self.format_size(sum(os.path.getsize(f) for f in self.found_files if os.path.exists(f)))
        self.info_var.set(f"VULNERABILITIES: {current_len} | TOTAL_PAYLOAD: {size_str}")

        if self.is_scanning:
            # Update Progress Bar
            percent = (self.scanned_bytes / self.total_bytes_to_scan) * 100
            percent = min(percent, 100.0) 
            self.progress_var.set(self.generate_progress_bar(percent))
            
            # Animate Status Cursor
            self.blink_state = not self.blink_state
            cursor = "█" if self.blink_state else "_"
            scanned_str = self.format_size(self.scanned_bytes)
            total_str = self.format_size(self.total_bytes_to_scan)
            self.status_var.set(f"SCANNING: {scanned_str}/{total_str} {cursor}")
            
            # Continue Loop
            self.root.after(100, self.update_ui_loop)
        else:
            # Finalize
            self.progress_var.set(self.generate_progress_bar(100))
            self.scan_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            if self.stop_requested:
                self.status_var.set("SEQUENCE_ABORTED.")
            else:
                self.status_var.set("SCAN_COMPLETE.")
            
            if self.found_files:
                self.delete_all_btn.config(state=tk.NORMAL)
                self.delete_sel_btn.config(state=tk.NORMAL)

    def perform_deletion(self, files_to_delete):
        if not files_to_delete:
            return
            
        confirm = messagebox.askyesno("CONFIRM_OVERWRITE", 
                                      f"ARE YOU SURE YOU WANT TO PERMANENTLY ERASE {len(files_to_delete)} TARGETS?\n\nACTION CANNOT BE REVERSED.")
        if not confirm:
            return
            
        deleted = 0
        failed = 0
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted += 1
                if file_path in self.found_files:
                    self.found_files.remove(file_path)
            except Exception:
                failed += 1

        # Refresh UI
        self.listbox.delete(0, tk.END)
        self.last_displayed_index = 0
        
        # Re-populate remaining list
        if self.found_files:
            self.listbox.insert(tk.END, *self.found_files)
            self.last_displayed_index = len(self.found_files)
            
        size_str = self.format_size(sum(os.path.getsize(f) for f in self.found_files if os.path.exists(f)))
        self.info_var.set(f"VULNERABILITIES: {len(self.found_files)} | TOTAL_PAYLOAD: {size_str}")
        
        messagebox.showinfo("PURGE_REPORT", 
                            f"TARGETS_ERASED: {deleted}\nACCESS_DENIED/LOCKED: {failed}")
        
        if not self.found_files:
            self.delete_all_btn.config(state=tk.DISABLED)
            self.delete_sel_btn.config(state=tk.DISABLED)

    def delete_all(self):
        self.perform_deletion(list(self.found_files))

    def delete_selected(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("SYS_NOTICE", "NO_TARGETS_SELECTED")
            return
            
        files_to_delete = [self.listbox.get(i) for i in selected_indices]
        self.perform_deletion(files_to_delete)

if __name__ == "__main__":
    root = tk.Tk()
    app = TempCleanerApp(root)
    root.mainloop()