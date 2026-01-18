# Directory Backup Tool

A collection of Python scripts for backing up directories with different GUI frameworks.

## Features

- Backup multiple source directories to a destination.
- Progress tracking with ETA.
- Full backup for GUI versions (Tkinter, PyQt5, Kivy).
- Full or incremental backup options for Flask web apps.
- Logging to separate files for each script.

## Files

- `backup_webapp.py`: Flask web application for full backup via web interface.
- `backup_webapp_incremental.py`: Flask web application for incremental backup via web interface.
- `backup_gui.py`: Tkinter-based GUI for full backup.
- `backup_qt5.py`: PyQt5-based GUI for full backup.
- `backup_kivy.py`: Kivy-based GUI for full backup.
- `requirements.txt`: Python dependencies.
- `templates/index.html`: HTML template for the Flask apps.

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`

## Usage

### Flask Apps
Run one of the Flask scripts and open http://localhost:5000 in your browser:
- `python backup_webapp.py` for full backup.
- `python backup_webapp_incremental.py` for incremental backup (only copies changed or new files).

### GUI Apps
Run the respective script:
- `python backup_gui.py` (Tkinter)
- `python backup_qt5.py` (PyQt5)
- `python backup_kivy.py` (Kivy)

Select source directories, destination, and start backup.

## Logging

Each script logs to its own file:
- `webapp.log` (for Flask apps)
- `gui.log`
- `qt5.log`
- `kivy.log`



Flask Web Backup App

A lightweight Flask-based web backup application that supports incremental backups, mirror (sync) mode, and real-time progress tracking via a web interface.

This project provides functionality similar to rsync, but wrapped in a simple web UI and JSON API.

🚀 Features

✅ Incremental file backups

🔁 Optional mirror/sync mode (delete removed files)

📊 Real-time progress reporting (percent, ETA, status)

🧵 Background processing using threads

📁 Multiple source directories supported

📝 Detailed logging to file

🌐 Web UI + REST-style API

❌ Fault-tolerant (file errors do not stop the backup)

📂 How It Works (High Level)

User submits:

One or more source directories

A destination directory

Optional mirror mode

Backup runs in a background thread

Files are copied only if:

They don’t exist at destination

Size differs

Source file is newer

Progress can be queried live via an API endpoint

Optional mirror mode removes destination files no longer present in source

🧠 Core Concepts
Incremental Backups

Files are copied only when needed, based on:

File existence

File size

Modification time

This saves time and disk I/O.

Mirror Mode

When enabled:

Destination becomes an exact mirror of the source

Extra files in destination are deleted

Similar to rsync --delete

Background Execution

Backups run in a daemon thread

Web server remains responsive

Only one backup can run at a time

Live Progress Tracking

Progress information includes:

Total files to copy

Files copied

Failed copies

Files removed (mirror mode)

Percent complete

Estimated time remaining (ETA)

Status (idle, running, done, error)

🛠 Configuration
LOG_FILE_NAMES = False


When True, logs every copied file

Useful for debugging or auditing

Disable for better performance and cleaner logs

📝 Logging

Logs are written to webapp.log

Includes:

Backup start & completion

File copy failures

File deletions (mirror mode)

Fatal errors

🌐 API Endpoints
GET /

Serves the main web interface.

POST /start-backup

Starts a new backup job.

Request JSON:

{
  "source_dirs": ["/path/source1", "/path/source2"],
  "destination": "/path/backup",
  "mirror_mode": true
}


Responses:

200 OK → Backup started

409 Conflict → Backup already running

GET /progress

Returns current backup progress.

Example Response:

{
  "total_files": 120,
  "copied_files": 45,
  "failed_files": 1,
  "removed_files": 10,
  "percent": 37,
  "eta": 95,
  "status": "running",
  "error": null
}

🧵 Threading & Safety

Uses Python’s threading.Thread

Prevents blocking the Flask request cycle

Designed for single concurrent backup job

🖥 Requirements

Python 3.8+

Flask

Install dependencies:

pip install flask

▶️ Running the App
python app.py


By default, the app runs in debug mode:

http://127.0.0.1:5000


⚠️ Debug mode is not recommended for production.

🔒 Security Notes

No authentication included (intended for local/private use)

secret_key should be changed before deployment

File paths are trusted input — validate if exposing publicly

🧩 Possible Enhancements

🔐 Authentication / authorization

⏸ Pause & resume backups

📅 Scheduled backups

🐳 Docker support

🗂 Exclude patterns

⚡ Performance optimizations (checksum, multithreading)

🌍 Production server support (Gunicorn + Nginx)

📌 Use Cases

Home server backups

NAS → external drive sync

Web-controlled backup jobs

Learning Flask + threading

Lightweight rsync alternative with UI