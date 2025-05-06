import os
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(2**64 - 1)

from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import datetime
import pandas as pd
from openpyxl import Workbook
from player_info import (
    preprocess_image,
    extract_text_from_image,
    extract_player_info_from_text,
    schedule_file_deletion,
    cleanup_old_results
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/player-info", methods=["GET", "POST"])
def player_info():
    if request.method == "POST":
        uploaded_files = request.files.getlist("screenshots")
        all_player_data = []

        cleanup_old_results()

        for file in uploaded_files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            print(f"🔁 Processing: {filename}")
            try:
                print("👁️ OCR starting...")
                image = preprocess_image(path)
                resized_path = path.replace(".png", "_resized.png")
                image.save(resized_path, format="PNG")
                text = extract_text_from_image(resized_path)
                resized_path = path.replace(".png", "_resized.png")
                image.save(resized_path, format="PNG")
                text = extract_text_from_image(resized_path)
                print(f"📄 OCR from {filename}:{text}")
                player_data = extract_player_info_from_text(text)
                all_player_data.append(player_data)
                print("✅ OCR success!")
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")

        
        # Merge rows with the same ID
        merged_data = {}
        for row in all_player_data:
            pid = row.get("ID", "")
            if not pid:
                continue
            if pid not in merged_data:
                merged_data[pid] = row
            else:
                for key, value in row.items():
                    if not merged_data[pid].get(key) and value:
                        merged_data[pid][key] = value

        all_player_data = list(merged_data.values())

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"all-player-info_{timestamp}"
        excel_path = os.path.join(app.config['RESULTS_FOLDER'], f"{base_filename}.xlsx")

        df = pd.DataFrame(all_player_data)
        df.to_excel(excel_path, index=False)

        schedule_file_deletion(excel_path)

        return jsonify({
            "data": all_player_data,
            "excel_file": f"/download-excel/{base_filename}.xlsx"
        })

    return render_template("player-info.html")

@app.route("/alliance-duel-points")
def alliance_duel_points():
    return render_template("alliance-duel-points.html")

@app.route("/upload", methods=["POST"])
def upload_log_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    from alliance_duel import extract_alliance_duel_points

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    print(f"📥 Uploaded: {filename}")
    print("🔍 Extracting Alliance Duel data...")

    try:
        extract_alliance_duel_points(save_path, app.config["RESULTS_FOLDER"])
        latest_excel = max(
            (f for f in os.listdir(app.config["RESULTS_FOLDER"]) if f.endswith(".xlsx")),
            key=lambda x: os.path.getmtime(os.path.join(app.config["RESULTS_FOLDER"], x))
        )
        return jsonify({
            "message": "✅ Extraction completed successfully!",
            "excel_file": f"/download-excel/{latest_excel}"
        })
    except Exception as e:
        print("❌ Extraction error:", e)
        return jsonify({"message": f"❌ Error: {str(e)}"}), 500


@app.route("/zone-passes-count")
def zone_passes_count():
    return render_template("zone-passes-count.html")

@app.route("/download-excel/<filename>")
def download_excel(filename):
    path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
