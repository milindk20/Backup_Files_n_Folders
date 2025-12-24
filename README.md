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