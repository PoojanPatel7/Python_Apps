import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import sys
import tempfile
import os
import re

# Try to import Jedi for autocomplete
try:
    import jedi
except ImportError:
    jedi = None

class MiniPythonIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Python IDE (Auto-Pip & Autocomplete)")
        self.root.geometry("800x650")

        # --- Toolbar ---
        self.toolbar = tk.Frame(root, bg="#2d2d2d")
        self.toolbar.pack(fill=tk.X)

        self.run_btn = tk.Button(self.toolbar, text="▶ Run Program", command=self.run_code, 
                                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.run_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.help_lbl = tk.Label(self.toolbar, text="Press Ctrl+Space for Autocomplete", 
                                 bg="#2d2d2d", fg="white", font=("Arial", 9))
        self.help_lbl.pack(side=tk.RIGHT, padx=10)

        # --- Code Editor ---
        self.editor = scrolledtext.ScrolledText(root, wrap=tk.NONE, font=("Consolas", 12), bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.editor.bind("<Control-space>", self.show_suggestions)

        # --- Output Terminal ---
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), height=12, bg="black", fg="#00ff00")
        self.output_area.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        if jedi is None:
            self.output_area.insert(tk.END, "⚠️ 'jedi' module not found. Autocomplete disabled.\nRun 'pip install jedi' in your terminal and restart.\n\n")
        else:
            self.output_area.insert(tk.END, "Terminal Ready...\n\n")

        self.suggestion_popup = None

    def show_suggestions(self, event):
        """Fetches and displays code suggestions using Jedi."""
        if not jedi:
            return "break"

        code = self.editor.get("1.0", tk.END)
        cursor_index = self.editor.index(tk.INSERT)
        line, col = map(int, cursor_index.split('.'))

        try:
            script = jedi.Script(code)
            completions = script.complete(line, col)
        except Exception:
            return "break"

        if not completions:
            return "break"

        # Destroy old popup if it exists
        if self.suggestion_popup:
            self.suggestion_popup.destroy()

        # Calculate popup position based on cursor
        bbox = self.editor.bbox(tk.INSERT)
        if bbox:
            x, y, _, _ = bbox
            x += self.editor.winfo_rootx() + 20
            y += self.editor.winfo_rooty() + 20
        else:
            x, y = self.root.winfo_pointerxy()

        # Create suggestion popup
        self.suggestion_popup = tk.Toplevel(self.root)
        self.suggestion_popup.wm_overrideredirect(True) # Remove window borders
        self.suggestion_popup.wm_geometry(f"+{x}+{y}")

        self.listbox = tk.Listbox(self.suggestion_popup, font=("Consolas", 10), bg="#252526", fg="#d4d4d4", selectbackground="#007acc")
        self.listbox.pack()

        # Insert top 10 suggestions
        for c in completions[:10]:
            self.listbox.insert(tk.END, c.name)

        # Bindings to insert the suggestion
        self.listbox.bind("<Double-Button-1>", lambda e: self.insert_suggestion(completions))
        self.listbox.bind("<Return>", lambda e: self.insert_suggestion(completions))
        self.editor.bind("<FocusOut>", lambda e: self.suggestion_popup.destroy() if self.suggestion_popup else None)

        self.listbox.focus_set()
        self.listbox.selection_set(0)

        return "break"

    def insert_suggestion(self, completions):
        """Inserts the selected suggestion into the editor."""
        selection_index = self.listbox.curselection()[0]
        completion = completions[selection_index]
        
        # Insert the completion text
        self.editor.insert(tk.INSERT, completion.complete)
        self.suggestion_popup.destroy()
        self.suggestion_popup = None
        self.editor.focus_set()

    def run_code(self):
        """Saves code to a temp file and executes it."""
        code = self.editor.get("1.0", tk.END)
        self.output_area.delete("1.0", tk.END)

        # Create a temporary file to run the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_filename = f.name

        self.execute_script(temp_filename)

    def execute_script(self, filename):
        """Runs the python script and catches output/errors."""
        self.output_area.insert(tk.END, f"Running script...\n{'-'*50}\n")
        self.root.update()

        # Run the subprocess
        process = subprocess.Popen([sys.executable, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        # Print standard output
        if stdout:
            self.output_area.insert(tk.END, stdout)

        # Print standard error and check for missing modules
        if stderr:
            self.output_area.insert(tk.END, stderr)
            
            # Use RegEx to find "ModuleNotFoundError"
            match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", stderr)
            if match:
                missing_module = match.group(1)
                # Ask user if they want to install it
                if messagebox.askyesno("Missing Package Detected", f"Python cannot find the module '{missing_module}'.\n\nWould you like the IDE to install it automatically using pip?"):
                    self.install_module(missing_module, filename)

        # Clean up the temporary file
        try:
            os.remove(filename)
        except:
            pass

    def install_module(self, module_name, filename):
        """Installs a module via pip and re-runs the code."""
        self.output_area.insert(tk.END, f"\n{'-'*50}\n[SYSTEM] Attempting to 'pip install {module_name}'...\n")
        self.root.update()
        
        try:
            # Run pip install
            subprocess.run([sys.executable, "-m", "pip", "install", module_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.output_area.insert(tk.END, f"[SYSTEM] Successfully installed '{module_name}'. Re-running program...\n\n")
            self.root.update()
            
            # Re-run the script now that the module is installed
            self.execute_script(filename)
            
        except subprocess.CalledProcessError as e:
            self.output_area.insert(tk.END, f"[SYSTEM] Failed to install '{module_name}'.\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = MiniPythonIDE(root)
    root.mainloop()