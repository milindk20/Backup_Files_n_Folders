from flask import Flask, render_template, request, jsonify
import os
import shutil
import threading
import time
import logging

# --------------------------------------------------
# Configuration
# --------------------------------------------------
LOG_FILE_NAMES = False

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    filename='webapp.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# --------------------------------------------------
# Flask app
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --------------------------------------------------
# Global progress
# --------------------------------------------------
progress = {
    'total_files': 0,
    'copied_files': 0,
    'failed_files': 0,
    'removed_files': 0,
    'start_time': None,
    'eta': None,
    'percent': 0,
    'status': 'idle',
    'error': None
}

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def should_copy(src_file, dest_file):
    if not os.path.exists(dest_file):
        return True

    s = os.stat(src_file)
    d = os.stat(dest_file)

    return s.st_size != d.st_size or s.st_mtime > d.st_mtime


def count_all_files(source_dirs):
    count = 0
    for src in source_dirs:
        if os.path.isdir(src):
            for _, _, files in os.walk(src):
                count += len(files)
    return count


def count_incremental_files(source_dirs, destination):
    count = 0
    for src in source_dirs:
        if not os.path.isdir(src):
            continue

        dest_root = os.path.join(destination, os.path.basename(src))

        for root, _, files in os.walk(src):
            rel = os.path.relpath(root, src)
            dest_dir = os.path.join(dest_root, rel)

            for f in files:
                if should_copy(
                    os.path.join(root, f),
                    os.path.join(dest_dir, f)
                ):
                    count += 1
    return count


def build_file_index(base_dir):
    files = set()
    for root, _, fs in os.walk(base_dir):
        for f in fs:
            files.add(os.path.relpath(os.path.join(root, f), base_dir))
    return files


def mirror_cleanup(source_dirs, destination):
    removed = 0

    for src in source_dirs:
        if not os.path.isdir(src):
            continue

        dest_root = os.path.join(destination, os.path.basename(src))
        if not os.path.isdir(dest_root):
            continue

        src_files = build_file_index(src)
        dest_files = build_file_index(dest_root)

        for rel in dest_files - src_files:
            path = os.path.join(dest_root, rel)
            try:
                os.remove(path)
                removed += 1
                logger.info(f"Removed (mirror): {path}")
            except Exception as e:
                logger.error(f"Remove failed: {path} | {e}")

    return removed

# --------------------------------------------------
# Worker
# --------------------------------------------------
def backup_worker(source_dirs, destination, mirror_mode):
    global progress

    progress.update({
        'status': 'running',
        'copied_files': 0,
        'failed_files': 0,
        'removed_files': 0,
        'percent': 0,
        'eta': None,
        'start_time': time.time(),
        'error': None
    })

    logger.info(
        f"Backup started | Mode: {'MIRROR' if mirror_mode else 'INCREMENTAL'}"
    )

    try:
        total_before = count_all_files(source_dirs)
        total_after = count_incremental_files(source_dirs, destination)
        progress['total_files'] = total_after

        copied = 0

        for src in source_dirs:
            if not os.path.isdir(src):
                continue

            dest_root = os.path.join(destination, os.path.basename(src))
            os.makedirs(dest_root, exist_ok=True)

            for root, _, files in os.walk(src):
                rel = os.path.relpath(root, src)
                dest_dir = os.path.join(dest_root, rel)
                os.makedirs(dest_dir, exist_ok=True)

                for f in files:
                    src_file = os.path.join(root, f)
                    dest_file = os.path.join(dest_dir, f)

                    if not should_copy(src_file, dest_file):
                        continue

                    try:
                        shutil.copy2(src_file, dest_file)
                        copied += 1
                        progress['copied_files'] = copied

                        if LOG_FILE_NAMES:
                            logger.info(f"Copied: {src_file}")

                    except Exception as e:
                        progress['failed_files'] += 1
                        logger.error(f"Copy failed: {src_file} | {e}")

                    if total_after:
                        progress['percent'] = int((copied / total_after) * 100)
                        elapsed = time.time() - progress['start_time']
                        if copied:
                            progress['eta'] = int(
                                elapsed * (total_after - copied) / copied
                            )

        if mirror_mode:
            progress['removed_files'] = mirror_cleanup(
                source_dirs, destination
            )

        progress['status'] = 'done'
        logger.info(
            f"Backup complete: {copied}/{total_after} copied "
            f"({total_before} total scanned)"
        )

    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)
        logger.exception("Backup failed")

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start-backup', methods=['POST'])
def start_backup():
    data = request.json

    if progress['status'] == 'running':
        return jsonify({'status': 'error', 'message': 'Already running'}), 409

    thread = threading.Thread(
        target=backup_worker,
        args=(
            data.get('source_dirs', []),
            data.get('destination'),
            data.get('mirror_mode', False)
        ),
        daemon=True
    )
    thread.start()

    return jsonify({'status': 'started'})


@app.route('/progress')
def get_progress():
    return jsonify(progress)

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
