# Directory Backup Tool

A collection of Python scripts for backing up directories with different GUI frameworks.

## Features

- Backup multiple source directories to a destination.
- Progress tracking with ETA.
- Incremental backup (only copies changed files) for GUI versions.
- Full backup for the Flask web app.
- Logging to separate files for each script.

## Files

- `app.py`: Flask web application for backup via web interface.
- `backup_gui.py`: Tkinter-based GUI for backup.
- `backup_qt5.py`: PyQt5-based GUI for backup.
- `backup_kivy.py`: Kivy-based GUI for backup.
- `requirements.txt`: Python dependencies.
- `templates/index.html`: HTML template for the Flask app.

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`

## Usage

### Flask App
Run `python app.py` and open http://localhost:5000 in your browser.

### GUI Apps
Run the respective script:
- `python backup_gui.py` (Tkinter)
- `python backup_qt5.py` (PyQt5)
- `python backup_kivy.py` (Kivy)

Select source directories, destination, and start backup.

## Logging

Each script logs to its own file:
- `app.log`
- `gui.log`
- `qt5.log`
- `kivy.log`