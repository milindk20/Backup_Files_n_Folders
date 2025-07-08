from flask import Flask, render_template, request, redirect, flash
import os
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        source_dirs = request.form.get('source_dirs', '').split(';')
        destination = request.form.get('destination', '')
        errors = []
        for src in source_dirs:
            src = src.strip()
            if not src or not os.path.isdir(src):
                errors.append(f"Invalid source: {src}")
                continue
            try:
                dest_path = os.path.join(destination, os.path.basename(src))
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(src, dest_path)
            except Exception as e:
                errors.append(f"Error copying {src}: {e}")
        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            flash('Backup completed successfully!', 'success')
        return redirect('/')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
