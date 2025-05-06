import os
import time
from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)

# Temporary upload directory (to store files temporarily)
UPLOAD_FOLDER = 'uploads'
EXPIRATION_TIME = timedelta(days=1)  # Files expire after 24 hours

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure the upload folder exists
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Helper function to delete expired files
def cleanup_files():
    now = datetime.now()
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            # Get file creation time and check expiration
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_time > EXPIRATION_TIME:
                os.remove(file_path)
                print(f"Deleted expired file: {filename}")

# Main route for uploading and displaying files
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files['file']
        if file:
            # Save the uploaded file securely
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Cleanup old files before rendering the page
            cleanup_files()

            # Send success message and show the uploaded file
            return render_template("index.html", message=f"File '{filename}' uploaded successfully!", filename=filename)

    return render_template("index.html")

# Route for downloading a file
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
