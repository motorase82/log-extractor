import os
import re
import json
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.styles import Font  # Add this line to fix the error
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment  # Add Alignment here
from openpyxl.styles import PatternFill  # Add this import for background color

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
ALLOWED_EXTENSIONS = {"txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULTS_FOLDER"] = RESULTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# APC Vehicle Mapping
apc_mapping = {
    "0": "None",
    "1": "APC (Regular Truck)",
    "2": "Armed Chariot",
    "3": "Iron Fist",
    "4": "Plunderer",
    "5": "New World Protector",
    "6": "Demon"
}
from openpyxl.styles import PatternFill  # Import this to apply background color

# --------------------------- Player Info Extraction --------------------------- #
def extract_player_info(file_path):
    json_pattern = re.compile(r'# Message #<color=green>extension return <get\.new\.user\.info> \|</color> (.*)')

    with open(file_path, "r", encoding="utf-8") as file:
        log_data = file.readlines()

    player_data = []
    seen_players = set()  # To track players we've already added

    for line in log_data:
        match = json_pattern.search(line)
        if match:
            try:
                data = json.loads(match.group(1))
                player_name = data.get("name", "")

                # Debug: Print the player name being processed
                print(f"Processing player: {player_name}")

                # Skip if the player name is already in the seen_players set
                if player_name in seen_players:
                    continue

                seen_players.add(player_name)  # Mark player as seen

                # Extract "viewPoint" data (Total Battles, Victories, etc.)
                view_points = {item["viewPoint"]: item["value"] for item in data.get("info", [])}

                player_info = {
                    "User ID": data.get("uid", ""),
                    "Player Name": player_name,
                    "Game ID": data.get("sharecode", ""),
                    "CP": data.get("power", ""),
                    "Sex": "Male" if data.get("sex") == 1 else "Female" if data.get("sex") == 2 else "Unknown",
                    "Amry Kill": data.get("armyKill", "0"),
                    "APC": apc_mapping.get(data.get("personalFormationVehicleId", "0"), "None"),  # Map APC ID to Name
                    "Total Battles": view_points.get("1,0", "0"),
                    "Battle Victories": view_points.get("1,1", "0"),
                    "Unit Defeated enemies": view_points.get("1,2", "0"),
                    "Unit Defeated yours": view_points.get("1,3", "0"),
                    "Unit Treated yours": view_points.get("1,4", "0"),
                    "Zombie defeated": view_points.get("1,5", "0")
                }

                player_data.append(player_info)

            except json.JSONDecodeError:
                continue

    # After loop, print the total number of players processed
    print(f"Total players processed: {len(player_data)}")

    # Save to Excel and CSV
    df = pd.DataFrame(player_data)
    excel_path = os.path.join(app.config["RESULTS_FOLDER"], "player_info_data.xlsx")
    csv_path = os.path.join(app.config["RESULTS_FOLDER"], "player_info_data.csv")

    # Save the data to Excel
    df.to_excel(excel_path, index=False)

    # Create a workbook using openpyxl to fine-tune the Excel file
    wb = Workbook()
    ws = wb.active
    ws.title = "Player Data"

    # Add column headers (this will be from the DataFrame's column names)
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="8db4e2", end_color="8db4e2", fill_type="solid")  # Yellow background for the header
    ws.append(df.columns.tolist())  # Add column headers to the sheet

    # Apply background color to header cells
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font  # Apply the bold font to headers

    # Insert data rows from the DataFrame
    for row in df.itertuples(index=False):
        ws.append(row)

    # Apply a filter to the first row (optional)
    ws.auto_filter.ref = ws.dimensions

    # Auto-adjust column width based on content length
    for col_num, column_title in enumerate(df.columns, start=1):
        col_letter = get_column_letter(col_num)
        max_length = max(len(str(column_title)), *(len(str(cell.value)) for cell in ws[col_letter]))
        ws.column_dimensions[col_letter].width = max_length + 2  # Add a little extra space for padding

    # Align the headers to the center
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Save the workbook
    wb.save(excel_path)

    # Save data to CSV (this part remains unchanged)
    df.to_csv(csv_path, index=False)

    return df.to_dict(orient="records")


# --------------------------- Alliance Duel Points Extraction --------------------------- #
def extract_alliance_duel_points(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        log_data = file.read()

    # Locate the "allPlayerScore" section for AD points
    score_start_index = log_data.find('"allPlayerScore":') + len('"allPlayerScore":')
    score_end_index = log_data.find(']}', score_start_index) + 1
    player_score_json = log_data[score_start_index:score_end_index].strip()

    score_data = []
    try:
        player_scores = json.loads(player_score_json)

        for player in player_scores:
            name = player.get('name', 'Unknown')
            score = player.get('score', 0)
            score_data.append({"Player Name": name, "Points": score})

    except json.JSONDecodeError as e:
        print(f"Error parsing 'allPlayerScore' JSON: {e}")
        return []  # Return empty list if there’s an error

    # Save to Excel and CSV
    df = pd.DataFrame(score_data)
    excel_path = os.path.join(app.config["RESULTS_FOLDER"], "alliance_duel_points_data.xlsx")
    csv_path = os.path.join(app.config["RESULTS_FOLDER"], "alliance_duel_points_data.csv")

    df.to_excel(excel_path, index=False)

    # Create a workbook using openpyxl to fine-tune the Excel file
    wb = Workbook()
    ws = wb.active
    ws.title = "Alliance Duel Points Data"

    # Add column headers (this will be from the DataFrame's column names)
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="8db4e2", end_color="8db4e2", fill_type="solid")  # Yellow background for the header
    ws.append(df.columns.tolist())  # Add column headers to the sheet

    # Apply background color to header cells
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font  # Apply the bold font to headers

    # Insert data rows from the DataFrame
    for row in df.itertuples(index=False):
        ws.append(row)

    # Apply a filter to the first row (optional)
    ws.auto_filter.ref = ws.dimensions

    # Auto-adjust column width based on content length
    for col_num, column_title in enumerate(df.columns, start=1):
        col_letter = get_column_letter(col_num)
        max_length = max(len(str(column_title)), *(len(str(cell.value)) for cell in ws[col_letter]))
        ws.column_dimensions[col_letter].width = max_length + 2  # Add a little extra space for padding

    # Align the headers to the center
    for cell in ws[1]:
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Save the workbook
    wb.save(excel_path)

    # Save data to CSV (this part remains unchanged)
    df.to_csv(csv_path, index=False)

    return df.to_dict(orient="records")


# --------------------------- Download Routes for Player Info --------------------------- #
@app.route("/download-excel/player-info", methods=["GET"])
def download_excel_player_info():
    excel_path = os.path.join(app.config["RESULTS_FOLDER"], "player_info_data.xlsx")
    return send_file(excel_path, as_attachment=True)


@app.route("/download-csv/player-info", methods=["GET"])
def download_csv_player_info():
    csv_path = os.path.join(app.config["RESULTS_FOLDER"], "player_info_data.csv")
    return send_file(csv_path, as_attachment=True)


# --------------------------- Download Routes for Alliance Duel Points --------------------------- #
@app.route("/download-excel/alliance-duel-points", methods=["GET"])
def download_excel_alliance_duel_points():
    excel_path = os.path.join(app.config["RESULTS_FOLDER"], "alliance_duel_points_data.xlsx")
    return send_file(excel_path, as_attachment=True)


@app.route("/download-csv/alliance-duel-points", methods=["GET"])
def download_csv_alliance_duel_points():
    csv_path = os.path.join(app.config["RESULTS_FOLDER"], "alliance_duel_points_data.csv")
    return send_file(csv_path, as_attachment=True)


# Main Home Page with instructions
@app.route("/")
def home():
    return render_template("index.html")  # Main Page


# Alliance Duel Points extraction page
@app.route("/alliance-duel-points", methods=["GET", "POST"])
def alliance_duel_points():
    return render_template("alliance-duel-points.html", script="alliance_duel_points_script.js")


# Player Information extraction page
@app.route("/player-info", methods=["GET", "POST"])
def player_info():
    return render_template("player-info.html", script="player_info_script.js")


# File upload and extraction
@app.route("/upload", methods=["POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        extraction_type = request.form.get('extraction_type')

        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
            file.save(file_path)

            if extraction_type == "alliance-duel-points":
                extracted_data = extract_alliance_duel_points(file_path)
            else:
                extracted_data = extract_player_info(file_path)

            return jsonify({
                "message": "File extracted successfully!",
                "data": extracted_data,
                "excel_file": f"/download-excel/{extraction_type}",
                "csv_file": f"/download-csv/{extraction_type}"
            })
    return render_template("player-info.html")



@app.route("/download-excel/<extraction_type>", methods=["GET"])
def download_excel(extraction_type):
    return send_file(os.path.join(app.config["RESULTS_FOLDER"], f"{extraction_type}_data.xlsx"), as_attachment=True)


@app.route("/download-csv/<extraction_type>", methods=["GET"])
def download_csv(extraction_type):
    return send_file(os.path.join(app.config["RESULTS_FOLDER"], f"{extraction_type}_data.csv"), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
