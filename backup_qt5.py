import os
import shutil
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFileDialog, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import sys
import logging

# Configure logging for backup_qt5.py
logging.basicConfig(filename='qt5.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('qt5')

# Main backup application class using PyQt5
class BackupAppQt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Directory Backup Tool')
        self.setGeometry(100, 100, 1000, 600)
        self.source_dirs = []  # List of source directories
        self.destination = ''  # Destination directory
        self.copied_files = 0  # Number of files copied so far
        self.total_files = 0   # Total number of files to copy
        self.start_time = None # Start time for ETA calculation
        self.is_running = False # Backup running state
        self.thread = None     # Thread for backup operation

        self.init_ui()

    def init_ui(self):
        # Set up the main UI layout and widgets
        layout = QVBoxLayout()

        # Title label
        title = QLabel('<b><span style="color:#4a90e2; font-size:28pt;">Directory Backup Tool</span></b>')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Source directories UI
        src_label = QLabel('Source Directories:')
        src_label.setStyleSheet('font-weight: bold; font-size: 12pt;')
        layout.addWidget(src_label)
        src_hbox = QHBoxLayout()
        self.src_list = QListWidget()
        self.src_list.setFixedHeight(80)
        src_hbox.addWidget(self.src_list)
        add_src_btn = QPushButton('Add Folder')
        add_src_btn.clicked.connect(self.add_folder)
        src_hbox.addWidget(add_src_btn)
        remove_src_btn = QPushButton('Remove Selected')
        remove_src_btn.clicked.connect(self.remove_selected_folder)
        src_hbox.addWidget(remove_src_btn)
        layout.addLayout(src_hbox)

        # Destination directory UI
        dest_label = QLabel('Destination Directory:')
        dest_label.setStyleSheet('font-weight: bold; font-size: 12pt;')
        layout.addWidget(dest_label)
        dest_hbox = QHBoxLayout()
        self.dest_display = QLabel('No folder selected')
        self.dest_display.setStyleSheet('background: #eee; padding: 4px;')
        dest_hbox.addWidget(self.dest_display)
        dest_btn = QPushButton('Select Folder')
        dest_btn.clicked.connect(self.select_dest)
        dest_hbox.addWidget(dest_btn)
        layout.addLayout(dest_hbox)

        # Progress bar and percent label
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setMinimum(0)
        self.progress.setFixedHeight(40)
        self.progress.setStyleSheet('QProgressBar {font-size: 18pt; text-align: center;}')
        layout.addWidget(self.progress)
        self.progress_percent_label = QLabel('0%')
        self.progress_percent_label.setAlignment(Qt.AlignCenter)
        self.progress_percent_label.setStyleSheet('color: white; font-size: 28pt; font-weight: bold; background: transparent; position: absolute;')
        layout.addWidget(self.progress_percent_label)
        self.progress_label = QLabel('')
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # Main action buttons
        btn_hbox = QHBoxLayout()
        self.start_btn = QPushButton('▶')
        self.start_btn.setFixedSize(80, 80)
        self.start_btn.setStyleSheet('border-radius: 40px; background: #34b233; color: white; font-size: 32pt;')
        self.start_btn.clicked.connect(self.start_backup)
        btn_hbox.addWidget(self.start_btn)
        self.reset_btn = QPushButton('⟳')
        self.reset_btn.setFixedSize(80, 80)
        self.reset_btn.setStyleSheet('border-radius: 40px; background: #d32f2f; color: white; font-size: 32pt;')
        self.reset_btn.clicked.connect(self.reset)
        btn_hbox.addWidget(self.reset_btn)
        layout.addLayout(btn_hbox)

        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

    def add_folder(self):
        # Add a source directory using a folder dialog
        folder = QFileDialog.getExistingDirectory(self, 'Select Source Folder', os.path.expanduser('~'))
        if folder and folder not in self.source_dirs:
            self.source_dirs.append(folder)
            self.src_list.addItem(QListWidgetItem(folder))

    def remove_selected_folder(self):
        # Remove the selected source directory from the list
        selected = self.src_list.currentRow()
        if selected >= 0:
            self.source_dirs.pop(selected)
            self.src_list.takeItem(selected)

    def select_dest(self):
        # Select the destination directory using a folder dialog
        folder = QFileDialog.getExistingDirectory(self, 'Select Destination Folder', os.path.expanduser('~'))
        if folder:
            self.destination = folder
            self.dest_display.setText(folder)

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
        logger.info(f'Starting backup from {self.source_dirs} to {self.destination}')
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
            logger.info('Backup completed successfully')
            self.is_running = False
        except Exception as e:
            logger.error(f'Backup failed: {e}')
            self.is_running = False
            self.progress_label.setText(f'Error: {e}')

    def update_progress(self):
        # Update the progress bar and labels
        if self.total_files == 0:
            percent = 0
        else:
            percent = int((self.copied_files / self.total_files) * 100)
        elapsed = time.time() - self.start_time if self.start_time else 0
        eta = int(elapsed * (self.total_files - self.copied_files) / self.copied_files) if self.copied_files else 0
        self.progress.setValue(percent)
        self.progress_percent_label.setText(f'{percent}%')
        self.progress_label.setText(f'Copied {self.copied_files} of {self.total_files} files ({percent}%) | ETA: {eta}s')
        if not self.is_running:
            self.progress_label.setText('Backup completed!')
            self.timer.stop()

    def start_backup(self):
        # Start the backup process in a new thread
        if self.is_running:
            self.progress_label.setText('Backup is already running.')
            return
        if not self.source_dirs or not self.destination:
            self.progress_label.setText('Please select source and destination folders.')
            return
        self.progress.setValue(0)
        self.progress_label.setText('Starting backup...')
        self.thread = threading.Thread(target=self.run_backup, daemon=True)
        self.thread.start()
        self.timer.start(100)

    def run_backup(self):
        # Run the backup worker (for threading)
        self.backup_worker()

    def reset(self):
        # Reset all fields and progress
        self.source_dirs = []
        self.src_list.clear()
        self.destination = ''
        self.dest_display.setText('No folder selected')
        self.progress.setValue(0)
        self.progress_label.setText('')
        self.progress_percent_label.setText('0%')

# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BackupAppQt()
    window.show()
    sys.exit(app.exec_())
