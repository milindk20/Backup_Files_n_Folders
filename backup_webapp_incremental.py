from flask import Flask, render_template, request, jsonify
import os
import shutil
import threading
import time
import logging

# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Set to True to log every copied file name
LOG_FILE_NAMES = False

# --------------------------------------------------
# Logging configuration
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
# Global progress state
# --------------------------------------------------
progress = {
    'total_files': 0,
    'copied_files': 0,
    'failed_files': 0,
    'start_time': None,
    'eta': None,
    'percent': 0,
    'status': 'idle',
    'error': None
}


# --------------------------------------------------
# Incremental backup helpers
# --------------------------------------------------
def should_copy(src_file, dest_file):
    """Return True if file is new or modified."""
    if not os.path.exists(dest_file):
        return True

    src_stat = os.stat(src_file)
    dest_stat = os.stat(dest_file)

    if src_stat.st_size != dest_stat.st_size:
        return True

    if src_stat.st_mtime > dest_stat.st_mtime:
        return True

    return False


def count_all_files(source_dirs):
    """Count ALL files (before incremental filtering)."""
    count = 0
    for src in source_dirs:
        src = src.strip()
        if not os.path.isdir(src):
            continue
        for _, _, files in os.walk(src):
            count += len(files)
    return count


def count_incremental_files(source_dirs, destination):
    """Count only files that need copying."""
    count = 0

    for src in source_dirs:
        src = src.strip()
        if not os.path.isdir(src):
            continue

        dest_base = os.path.join(destination, os.path.basename(src))

        for root, _, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dest_base, rel_path)

            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)

                if should_copy(src_file, dest_file):
                    count += 1

    return count


# --------------------------------------------------
# Backup worker thread
# --------------------------------------------------
def backup_worker(source_dirs, destination):
    global progress

    progress.update({
        'status': 'running',
        'copied_files': 0,
        'percent': 0,
        'eta': None,
        'start_time': time.time(),
        'error': None
    })

    logger.info(f"Starting incremental backup: {source_dirs} -> {destination}")

    try:
        # --- Pre-scan (all files) ---
        total_before = count_all_files(source_dirs)
        logger.info(
            f"Pre-scan complete: {total_before} total files found"
        )

        # --- Incremental scan ---
        total_after = count_incremental_files(source_dirs, destination)
        progress['total_files'] = total_after

        logger.info(
            f"Incremental scan complete: {total_after} files selected for copy "
            f"({total_before - total_after} unchanged)"
        )

        if total_after == 0:
            logger.info("No changes detected — nothing to copy")

        copied = 0

        for src in source_dirs:
            src = src.strip()
            if not src or not os.path.isdir(src):
                continue

            dest_root = os.path.join(destination, os.path.basename(src))
            os.makedirs(dest_root, exist_ok=True)

            for root, _, files in os.walk(src):
                rel_path = os.path.relpath(root, src)
                dest_dir = os.path.join(dest_root, rel_path)
                os.makedirs(dest_dir, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)

                    if not should_copy(src_file, dest_file):
                        continue

                    try:
                        shutil.copy2(src_file, dest_file)
                        copied += 1
                        progress['copied_files'] = copied

                        if LOG_FILE_NAMES:
                            logger.info(f"Copied: {src_file} -> {dest_file}")

                    except Exception as e:
                        progress['failed_files'] += 1
                        logger.error(
                            f"Failed to copy: {src_file} -> {dest_file} | Error: {e}"
                        )
                        continue


                    if LOG_FILE_NAMES:
                        logger.info(
                            f"Copied: {src_file} -> {dest_file}"
                        )

                    if total_after > 0:
                        progress['percent'] = int(
                            (copied / total_after) * 100
                        )
                        elapsed = time.time() - progress['start_time']
                        if copied > 0:
                            progress['eta'] = int(
                                elapsed * (total_after - copied) / copied
                            )

        progress['status'] = 'done'

        if copied == total_after:
            logger.info(
                f"Backup completed: copied {copied}/{total_after} files "
                f"(from {total_before} total)"
            )
        else:
            logger.warning(
                f"Backup completed with mismatch: copied {copied}/{total_after} "
                f"(from {total_before} total)"
            )

    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)
        logger.error(f"Backup failed: {e}")


# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/start-backup', methods=['POST'])
def start_backup():
    global progress

    data = request.json
    source_dirs = data.get('source_dirs', [])
    destination = data.get('destination', '')

    if not source_dirs or not destination:
        return jsonify({
            'status': 'error',
            'message': 'Missing source or destination'
        }), 400

    if progress['status'] == 'running':
        return jsonify({
            'status': 'error',
            'message': 'Backup already running'
        }), 409

    progress['status'] = 'starting'

    thread = threading.Thread(
        target=backup_worker,
        args=(source_dirs, destination),
        daemon=True
    )
    thread.start()

    logger.info(f"Backup initiated: {source_dirs} -> {destination}")
    return jsonify({'status': 'started'})


@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
