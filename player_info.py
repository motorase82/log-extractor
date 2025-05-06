
import os
import re
import threading
import time
import easyocr
from PIL import Image, ImageEnhance, ImageFilter

Image.MAX_IMAGE_PIXELS = None
reader = easyocr.Reader(['en'], gpu=True)

def preprocess_image(image_path):
    image = Image.open(image_path).convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    threshold = 140
    image = image.point(lambda x: 255 if x > threshold else 0)
    return image

def extract_text_from_image(path):
    print(f"📦 Loading image for OCR: {path}")
    try:
        text_lines = reader.readtext(path, detail=0)
        print(f"✅ OCR returned {len(text_lines)} lines")
        return "\n".join(text_lines)
    except Exception as e:
        print(f"💥 OCR failed: {e}")
        return ""

def correct_player_id(ocr_id):
    corrections = {
        'B': '8', 'S': '5', 'Z': '2', 'G': '6',
        'O': '0', 'Q': '0', 'I': '1', 'L': '1', 'T': '7'
    }
    ocr_id = ocr_id.strip().upper()
    if re.match(r"^[A-Z0-9]{8}$", ocr_id):
        return ocr_id

    corrected = ''.join(corrections.get(c, c) for c in ocr_id)
    return corrected if re.match(r"^[A-Z0-9]{8}$", corrected) else ocr_id

def extract_player_info_from_text(text):
    player_data = {
        "Username": "",
        "ID": "",
        "Server": "",
        "CP": "",
        "Alliance": "",
        "APC": "",
        "Fortress Level": "",
        "Total Battles": "",
        "Battle Victories": "",
        "Units Defeated (Enemies)": "",
        "Units Defeated (Yours)": "",
        "Units Treated (Yours)": "",
        "Zombies Defeated": ""
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_text = " ".join(lines)

    for line in lines:
        if "id" in line.lower():
            match = re.search(r"\bID[:：]?\s*([A-Z0-9]{5,})", line, re.IGNORECASE)
            if match:
                raw_id = match.group(1).strip().upper()
                player_data["ID"] = correct_player_id(raw_id)
                break

    match = re.search(r"#(\d{2,4})", full_text)
    if match:
        player_data["Server"] = match.group(1)

    match = re.search(r"\b\d{1,3}(?:,\d{3}){2,}\b", full_text)
    if match:
        player_data["CP"] = match.group(0)

    for i, line in enumerate(lines):
        if player_data["CP"] in line and i > 0:
            username_candidate = lines[i - 1]
            if 3 <= len(username_candidate) <= 20:
                player_data["Username"] = username_candidate.strip()
            break

    stat_patterns = {
        "Total Battles": [r"Total Battles\s+([\d,\.]+)"],
        "Battle Victories": [r"Battle Victories\s+([\d,\.]+)"],
        "Units Defeated (Enemies)": [r"Units Defeated\s*\(Enemies\)\s+([\d,\.]+)"],
        "Units Defeated (Yours)": [r"Units Defeated\s*\(Yours\)\s+([\d,\.]+)"],
        "Units Treated (Yours)": [r"Units Treated\s*\(Yours[\)_]*\s+([\d,\.]+)"],
        "Zombies Defeated": [r"Zombies Defeated\s+([\d,\.]+)"]
    }

    for key, patterns in stat_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                player_data[key] = match.group(1)
                break

    return player_data

def schedule_file_deletion(filepath, delay_seconds=43200):
    def delete_later():
        time.sleep(delay_seconds)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Deleted: {filepath}")
    threading.Thread(target=delete_later, daemon=True).start()

def cleanup_old_results(folder="results", extensions=(".xlsx", ".csv")):
    for fname in os.listdir(folder):
        if fname.endswith(extensions):
            try:
                os.remove(os.path.join(folder, fname))
                print(f"🧹 Removed old file: {fname}")
            except Exception as e:
                print(f"⚠️ Could not remove {fname}: {e}")
