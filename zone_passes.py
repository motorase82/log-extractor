# zone_passes.py

import os
import sqlite3
import pandas as pd

def extract_zone_passes(file_path, results_folder):
    room_id = "custom_19462985000541_1744528405"
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    cursor.execute("SELECT SenderUid, Msg FROM chat WHERE RoomId = ?", (room_id,))
    messages = cursor.fetchall()

    zone_data = {}
    for uid, msg in messages:
        if msg.isdigit():
            value = int(msg)
            if uid not in zone_data or value > zone_data[uid]:
                zone_data[uid] = value

    try:
        user_info_df = pd.read_sql_query("SELECT Uid, UserName FROM chatUserInfo", conn)
    except:
        user_info_df = pd.DataFrame(columns=["Uid", "UserName"])

    df = pd.DataFrame([{"UID": uid, "Zone Passes": val} for uid, val in zone_data.items()])
    df = df.merge(user_info_df, left_on="UID", right_on="Uid", how="left")
    df.drop(columns=["Uid"], inplace=True)
    df.rename(columns={"UserName": "Name"}, inplace=True)
    df = df[["Name", "UID", "Zone Passes"]].sort_values(by="Zone Passes", ascending=False)

    excel_path = os.path.join(results_folder, "zone-passes-count_data.xlsx")
    csv_path = os.path.join(results_folder, "zone-passes-count_data.csv")
    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)

    print("✅ Saved Zone Passes Count Excel:", excel_path)
    conn.close()

    return df.to_dict(orient="records")
