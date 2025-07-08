import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Main backup application class
class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Directory Backup Tool')
        self.source_dirs = []  # List of source directories
        self.destination = ''  # Destination directory
        self.copied_files = 0  # Number of files copied so far
        self.total_files = 0   # Total number of files to copy
        self.start_time = None # Start time for ETA calculation
        self.eta = None
        self.progress_percent = 0
        self.is_running = False # Backup running state
        self.thread = None     # Thread for backup operation
        self.create_widgets()

    def create_widgets(self):
        # Configure main window and styles
        self.root.configure(bg='#f4f6fa')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Segoe UI', 11), padding=6)
        style.configure('TLabel', font=('Segoe UI', 11))
        style.configure('TEntry', font=('Segoe UI', 11))
        style.configure('TProgressbar', thickness=20, troughcolor='#e0e0e0', background='#4a90e2')

        title = tk.Label(self.root, text='Directory Backup Tool', font=('Segoe UI', 18, 'bold'), fg='#4a90e2', bg='#f4f6fa')
        title.pack(pady=(18, 10))

        frm = tk.Frame(self.root, bg='#f4f6fa', highlightbackground='#d1d5db', highlightthickness=1, bd=0)
        frm.pack(padx=30, pady=10, fill='both', expand=True)

        # Source directories UI
        src_label = tk.Label(frm, text='Source Directories:', font=('Segoe UI', 12, 'bold'), bg='#f4f6fa')
        src_label.grid(row=0, column=0, sticky='w', pady=(10, 2), columnspan=4)
        self.src_listbox = tk.Listbox(frm, width=55, height=5, font=('Segoe UI', 10), bd=1, relief='solid', highlightthickness=0)
        self.src_listbox.grid(row=1, column=0, columnspan=4, pady=5, padx=2, sticky='ew')
        add_btn = ttk.Button(frm, text='Add Folder', command=self.add_folders)
        add_btn.grid(row=2, column=0, pady=5, padx=(0, 5), sticky='w')
        remove_btn = ttk.Button(frm, text='Remove Selected', command=self.remove_selected)
        remove_btn.grid(row=2, column=1, pady=5, padx=(0, 5), sticky='w')

        # Destination directory UI
        dest_label = tk.Label(frm, text='Destination Directory:', font=('Segoe UI', 12, 'bold'), bg='#f4f6fa')
        dest_label.grid(row=3, column=0, sticky='w', pady=(18, 2), columnspan=4)
        self.dest_entry = ttk.Entry(frm, width=48)
        self.dest_entry.grid(row=4, column=0, columnspan=3, pady=5, padx=(0, 5), sticky='ew')
        dest_btn = ttk.Button(frm, text='Select Folder', command=self.select_dest)
        dest_btn.grid(row=4, column=3, pady=5, sticky='w')

        # Progress bar and label
        self.progress = ttk.Progressbar(frm, length=420, style='TProgressbar')
        self.progress.grid(row=5, column=0, columnspan=4, pady=20, padx=2, sticky='ew')
        self.progress_label = tk.Label(frm, text='', font=('Segoe UI', 11), bg='#f4f6fa', fg='#333')
        self.progress_label.grid(row=6, column=0, columnspan=4, pady=(0, 10))

        # Main action buttons
        self.start_btn = ttk.Button(frm, text='Start Backup', command=self.start_backup)
        self.start_btn.grid(row=7, column=0, pady=10, padx=(0, 5), sticky='w')
        self.reset_btn = ttk.Button(frm, text='Reset', command=self.reset)
        self.reset_btn.grid(row=7, column=1, pady=10, padx=(0, 5), sticky='w')

        # Tooltips for usability
        self.create_tooltip(add_btn, 'Add a source folder to backup (one at a time)')
        self.create_tooltip(remove_btn, 'Remove the selected source folder(s)')
        self.create_tooltip(dest_btn, 'Choose the destination folder for backup')
        self.create_tooltip(self.start_btn, 'Start the backup process')
        self.create_tooltip(self.reset_btn, 'Reset all fields and progress')

    def create_tooltip(self, widget, text):
        # Create a tooltip for a widget
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, background='#333', foreground='white', relief='solid', borderwidth=1, font=('Segoe UI', 9))
        label.pack(ipadx=6, ipady=2)
        def enter(event):
            x = widget.winfo_rootx() + 40
            y = widget.winfo_rooty() + 30
            tooltip.geometry(f'+{x}+{y}')
            tooltip.deiconify()
        def leave(event):
            tooltip.withdraw()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def add_folders(self):
        # Add a source directory (Tkinter does not support multi-select)
        dirs = filedialog.askdirectory(mustexist=True, title='Select Source Folder(s)')
        if dirs:
            if dirs not in self.source_dirs:
                self.source_dirs.append(dirs)
                self.src_listbox.insert(tk.END, dirs)

    def remove_selected(self):
        # Remove selected source directories
        selected = list(self.src_listbox.curselection())
        for idx in reversed(selected):
            self.src_listbox.delete(idx)
            del self.source_dirs[idx]

    def select_dest(self):
        # Select the destination directory
        dest = filedialog.askdirectory(mustexist=True, title='Select Destination Folder')
        if dest:
            self.destination = dest
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, dest)

    def count_files(self, dirs):
        # Count total files in all source directories
        count = 0
        for d in dirs:
            for root, _, files in os.walk(d):
                count += len(files)
        return count

    def backup_worker(self):
        # Worker thread for performing the backup
        self.is_running = True
        self.copied_files = 0
        self.total_files = self.count_files(self.source_dirs)
        self.start_time = time.time()
        self.progress['maximum'] = self.total_files if self.total_files else 1
        try:
            for src in self.source_dirs:
                dest_path = os.path.join(self.destination, os.path.basename(src))
                for root, dirs, files in os.walk(src):
                    rel_path = os.path.relpath(root, src)
                    dest_dir = os.path.join(dest_path, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        # Incremental backup: only copy if dest does not exist or src is newer
                        if not os.path.exists(dest_file) or os.path.getmtime(src_file) > os.path.getmtime(dest_file):
                            shutil.copy2(src_file, dest_file)
                        self.copied_files += 1
                        self.update_progress()
            self.is_running = False
            self.progress_label.config(text='Backup completed!')
        except Exception as e:
            self.is_running = False
            self.progress_label.config(text=f'Error: {e}')

    def update_progress(self):
        # Update the progress bar and label
        percent = int((self.copied_files / self.total_files) * 100) if self.total_files else 0
        elapsed = time.time() - self.start_time
        eta = int(elapsed * (self.total_files - self.copied_files) / self.copied_files) if self.copied_files else 0
        self.progress['value'] = self.copied_files
        self.progress_label.config(text=f'Copied {self.copied_files} of {self.total_files} files ({percent}%) | ETA: {eta}s')
        self.root.update_idletasks()

    def start_backup(self):
        # Start the backup process in a new thread
        if self.is_running:
            messagebox.showinfo('Backup', 'Backup is already running.')
            return
        self.source_dirs = [self.src_listbox.get(i) for i in range(self.src_listbox.size())]
        self.destination = self.dest_entry.get()
        if not self.source_dirs or not self.destination:
            messagebox.showwarning('Input Error', 'Please select source directories and destination.')
            return
        self.progress['value'] = 0
        self.progress_label.config(text='Starting backup...')
        self.thread = threading.Thread(target=self.backup_worker, daemon=True)
        self.thread.start()
        self.root.after(200, self.check_thread)

    def check_thread(self):
        # Periodically check if the backup thread is still running
        if self.is_running:
            self.root.after(200, self.check_thread)

    def reset(self):
        # Reset all fields and progress
        self.src_listbox.delete(0, tk.END)
        self.source_dirs = []
        self.dest_entry.delete(0, tk.END)
        self.destination = ''
        self.progress['value'] = 0
        self.progress_label.config(text='')

if __name__ == '__main__':
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()
