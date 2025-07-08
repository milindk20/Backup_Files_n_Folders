from flask import Flask, render_template, request, jsonify
import os
import shutil
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Global progress state for tracking backup progress
progress = {
    'total_files': 0,
    'copied_files': 0,
    'start_time': None,
    'eta': None,
    'percent': 0,
    'status': 'idle',
    'error': None
}

def count_files(dirs):
    # Count total files in all source directories
    count = 0
    for d in dirs:
        for root, _, files in os.walk(d):
            count += len(files)
    return count

def backup_worker(source_dirs, destination):
    # Worker thread for performing the backup
    global progress
    progress['status'] = 'running'
    progress['copied_files'] = 0
    progress['start_time'] = time.time()
    progress['error'] = None
    try:
        total_files = count_files(source_dirs)
        progress['total_files'] = total_files
        copied = 0
        for src in source_dirs:
            src = src.strip()
            if not src or not os.path.isdir(src):
                continue
            dest_path = os.path.join(destination, os.path.basename(src))
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
                    copied += 1
                    progress['copied_files'] = copied
                    if total_files > 0:
                        progress['percent'] = int((copied / total_files) * 100)
                        elapsed = time.time() - progress['start_time']
                        if copied > 0:
                            eta = elapsed * (total_files - copied) / copied
                            progress['eta'] = int(eta)
        progress['status'] = 'done'
    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)

@app.route('/', methods=['GET'])
def index():
    # Render the main web UI
    return render_template('index.html')

@app.route('/start-backup', methods=['POST'])
def start_backup():
    # Start the backup process in a new thread
    global progress
    data = request.json
    source_dirs = data.get('source_dirs', [])
    destination = data.get('destination', '')
    if not source_dirs or not destination:
        return jsonify({'status': 'error', 'message': 'Missing source or destination'}), 400
    # Reset progress
    progress['status'] = 'starting'
    thread = threading.Thread(target=backup_worker, args=(source_dirs, destination))
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/progress', methods=['GET'])
def get_progress():
    # Return the current backup progress as JSON
    global progress
    return jsonify(progress)

if __name__ == '__main__':
    app.run(debug=True)
