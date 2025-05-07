from flask import Flask, request, render_template, send_file
from pymongo import MongoClient
import gridfs
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ✅ MongoDB setup with password included
client = MongoClient("mongodb+srv://jagatpathak:zRxzoj5TlVc4kDcw@cluster0.wlfsqni.mongodb.net/?retryWrites=true&w=majority")
db = client["batman_files"]
fs = gridfs.GridFS(db)

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    files = []

    if request.method == "POST":
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)

            # Optional: Remove existing file with same name
            existing = db.fs.files.find_one({"filename": filename})
            if existing:
                fs.delete(existing["_id"])

            fs.put(file, filename=filename)
            message = f"File '{filename}' uploaded successfully!"

    # Search functionality
    search_query = request.args.get("search", "").lower()
    if search_query:
        files_cursor = db.fs.files.find({"filename": {"$regex": search_query, "$options": "i"}})
    else:
        files_cursor = db.fs.files.find()

    files = [f["filename"] for f in files_cursor]
    return render_template("index.html", message=message, files=files, search_query=search_query)

@app.route("/download/<filename>")
def download_file(filename):
    file = fs.find_one({"filename": filename})
    if not file:
        return "File not found.", 404

    return send_file(BytesIO(file.read()), download_name=filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
