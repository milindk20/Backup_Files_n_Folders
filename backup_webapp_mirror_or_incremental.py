from flask import Flask, render_template, request, jsonify
import os
import shutil
import threading
import time
import logging

# --------------------------------------------------
# This web application provides a web interface to back up files
# from multiple source directories to a destination directory. It
# supports both mirror mode (deleting extra files in the destination)
# and incremental mode (only adding/modifying files). The application
# tracks progress and logs operations.
# --------------------------------------------------


# --------------------------------------------------
# Configuration
# --------------------------------------------------

LOG_FILE_NAMES = False


MIRROR_MODE = False   
# True = mirror (delete extras), 
# False = incremental (only add/modify))

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
    'removed_files': 0,
    'start_time': None,
    'eta': None,
    'percent': 0,
    'status': 'idle',
    'error': None
}

# --------------------------------------------------
# Incremental helpers
# --------------------------------------------------
def should_copy(src_file, dest_file):
    if not os.path.exists(dest_file):
        return True

    src_stat = os.stat(src_file)
    dest_stat = os.stat(dest_file)

    return (
        src_stat.st_size != dest_stat.st_size or
        src_stat.st_mtime > dest_stat.st_mtime
    )


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

            for file in files:
                if should_copy(
                    os.path.join(root, file),
                    os.path.join(dest_dir, file)
                ):
                    count += 1

    return count

# --------------------------------------------------
# Mirror helpers
# --------------------------------------------------
def build_file_index(base_dir):
    files = set()
    for root, _, fs in os.walk(base_dir):
        for f in fs:
            full = os.path.join(root, f)
            files.add(os.path.relpath(full, base_dir))
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

        extras = dest_files - src_files

        for rel in extras:
            path = os.path.join(dest_root, rel)
            try:
                os.remove(path)
                removed += 1
                logger.info(f"Removed (mirror): {path}")
            except Exception as e:
                logger.error(f"Failed removing {path}: {e}")

    return removed

# --------------------------------------------------
# Backup worker thread
# --------------------------------------------------
def backup_worker(source_dirs, destination):
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

    try:
        total_before = count_all_files(source_dirs)
        total_after = count_incremental_files(source_dirs, destination)
        progress['total_files'] = total_after

        logger.info(
            f"Scan complete: {total_after}/{total_before} files need copy"
        )

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
                            logger.info(f"Copied: {src_file}")

                    except Exception as e:
                        progress['failed_files'] += 1
                        logger.error(f"Copy failed: {src_file} | {e}")

                    if total_after > 0:
                        progress['percent'] = int(
                            (copied / total_after) * 100
                        )
                        elapsed = time.time() - progress['start_time']
                        if copied:
                            progress['eta'] = int(
                                elapsed * (total_after - copied) / copied
                            )

        # --- MIRROR DELETE PHASE ---
        if MIRROR_MODE:
            removed = mirror_cleanup(source_dirs, destination)
            progress['removed_files'] = removed
            logger.info(f"Mirror cleanup removed {removed} files")

        progress['status'] = 'done'
        logger.info("Backup completed successfully")

    except Exception as e:
        progress['status'] = 'error'
        progress['error'] = str(e)
        logger.exception("Backup failed")

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
    destination = data.get('destination')

    if not source_dirs or not destination:
        return jsonify({'status': 'error', 'message': 'Missing input'}), 400

    if progress['status'] == 'running':
        return jsonify({'status': 'error', 'message': 'Already running'}), 409

    thread = threading.Thread(
        target=backup_worker,
        args=(source_dirs, destination),
        daemon=True
    )
    thread.start()

    return jsonify({'status': 'started'})


@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify(progress)

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
