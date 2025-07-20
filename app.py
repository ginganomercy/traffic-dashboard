import os
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime
import uuid

from counter import process_and_save_video

app = Flask(__name__)
app.secret_key = 'secret-key'

UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'

# Buat folder yang diperlukan
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

@app.route("/")
def home():
    return render_template("home.html", title="Home")

@app.route("/perhitungan", methods=["GET", "POST"])
def perhitungan():
    return render_template("perhitungan.html", title="Perhitungan", video_path=None)

@app.route("/upload", methods=["POST"])
def upload_video():
    if 'video' not in request.files:
        return redirect(url_for('perhitungan'))

    video = request.files['video']
    if video.filename == '':
        return redirect(url_for('perhitungan'))

    ext = os.path.splitext(video.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    video.save(video_path)

    return render_template("perhitungan.html", title="Perhitungan", video_path=f"uploads/{unique_name}")

@app.route("/process-video", methods=["POST"])
def process_video():
    try:
        data = request.get_json()

        input_path = os.path.join("static", data["video_path"])
        output_path = os.path.join(PROCESSED_FOLDER, f"processed_{os.path.basename(input_path)}")
        output_path = os.path.splitext(output_path)[0] + ".mp4"

        os.makedirs(PROCESSED_FOLDER, exist_ok=True)

        # Jalankan proses
        processed_filename, excel_filename, counts = process_and_save_video(input_path, output_path)

        # Simpan hasil ke session untuk halaman /hasil
        session["hasil_counts"] = counts
        session["excel_filename"] = excel_filename

        print("[INFO] Video & Excel berhasil diproses")
        print("[INFO] processed_filename:", processed_filename)
        print("[INFO] counts:", counts)

        return {
            "processed_video": processed_filename  # hanya nama file
        }

    except Exception as e:
        print("[ERROR]", str(e))
        return {"error": str(e)}, 500

@app.route("/video/<filename>")
def serve_video(filename):
    # Sajikan video hasil proses melalui route ini
    path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, mimetype='video/mp4')
    return "Video tidak ditemukan", 404

@app.route("/hasil")
def hasil():
    waktu = datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    counts = session.get("hasil_counts", {})
    excel_filename = session.get("excel_filename", None)
    return render_template("hasil.html", title="Hasil Perhitungan", waktu=waktu, counts=counts, excel_filename=excel_filename)

@app.route("/download-excel")
def download_excel():
    filename = request.args.get("filename")
    if not filename:
        return "File tidak tersedia", 404

    file_path = os.path.join(PROCESSED_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
