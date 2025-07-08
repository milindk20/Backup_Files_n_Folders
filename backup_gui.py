import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Directory Backup Tool')
        self.source_dirs = []
        self.destination = ''
        self.copied_files = 0
        self.total_files = 0
        self.start_time = None
        self.eta = None
        self.progress_percent = 0
        self.is_running = False
        self.thread = None
        self.create_widgets()

    def create_widgets(self):
        frm = tk.Frame(self.root)
        frm.pack(padx=20, pady=20)

        tk.Label(frm, text='Source Directories:').grid(row=0, column=0, sticky='w')
        self.src_listbox = tk.Listbox(frm, width=50, height=5)
        self.src_listbox.grid(row=1, column=0, columnspan=2, pady=5)
        tk.Button(frm, text='Add Folders', command=self.add_folders).grid(row=1, column=2, padx=5)
        tk.Button(frm, text='Remove Selected', command=self.remove_selected).grid(row=1, column=3, padx=5)

        tk.Label(frm, text='Destination Directory:').grid(row=2, column=0, sticky='w', pady=(10,0))
        self.dest_entry = tk.Entry(frm, width=50)
        self.dest_entry.grid(row=3, column=0, columnspan=2, pady=5)
        tk.Button(frm, text='Select Folder', command=self.select_dest).grid(row=3, column=2, padx=5)

        self.progress = ttk.Progressbar(frm, length=400)
        self.progress.grid(row=4, column=0, columnspan=4, pady=15)
        self.progress_label = tk.Label(frm, text='')
        self.progress_label.grid(row=5, column=0, columnspan=4)

        self.start_btn = tk.Button(frm, text='Start Backup', command=self.start_backup)
        self.start_btn.grid(row=6, column=0, pady=10)
        self.reset_btn = tk.Button(frm, text='Reset', command=self.reset)
        self.reset_btn.grid(row=6, column=1, pady=10)

    def add_folders(self):
        dirs = filedialog.askdirectory(mustexist=True, title='Select Source Folder(s)')
        if dirs:
            # Tkinter does not support multi-select, so call multiple times
            if dirs not in self.source_dirs:
                self.source_dirs.append(dirs)
                self.src_listbox.insert(tk.END, dirs)

    def remove_selected(self):
        selected = list(self.src_listbox.curselection())
        for idx in reversed(selected):
            self.src_listbox.delete(idx)
            del self.source_dirs[idx]

    def select_dest(self):
        dest = filedialog.askdirectory(mustexist=True, title='Select Destination Folder')
        if dest:
            self.destination = dest
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, dest)

    def count_files(self, dirs):
        count = 0
        for d in dirs:
            for root, _, files in os.walk(d):
                count += len(files)
        return count

    def backup_worker(self):
        self.is_running = True
        self.copied_files = 0
        self.total_files = self.count_files(self.source_dirs)
        self.start_time = time.time()
        self.progress['maximum'] = self.total_files if self.total_files else 1
        try:
            for src in self.source_dirs:
                dest_path = os.path.join(self.destination, os.path.basename(src))
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                for root, dirs, files in os.walk(src):
                    rel_path = os.path.relpath(root, src)
                    dest_dir = os.path.join(dest_path, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        shutil.copy2(src_file, dest_file)
                        self.copied_files += 1
                        self.update_progress()
            self.is_running = False
            self.progress_label.config(text='Backup completed!')
        except Exception as e:
            self.is_running = False
            self.progress_label.config(text=f'Error: {e}')

    def update_progress(self):
        percent = int((self.copied_files / self.total_files) * 100) if self.total_files else 0
        elapsed = time.time() - self.start_time
        eta = int(elapsed * (self.total_files - self.copied_files) / self.copied_files) if self.copied_files else 0
        self.progress['value'] = self.copied_files
        self.progress_label.config(text=f'Copied {self.copied_files} of {self.total_files} files ({percent}%) | ETA: {eta}s')
        self.root.update_idletasks()

    def start_backup(self):
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
        if self.is_running:
            self.root.after(200, self.check_thread)

    def reset(self):
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
