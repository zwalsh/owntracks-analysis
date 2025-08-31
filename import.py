import os
import glob
import json
from db import LocationDB, DB_PATH

JSON_DIR = "owntracks-json"

# Remove existing database if present
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


# Recreate the database schema
db = LocationDB()
db.create_schema()

json_files = glob.glob(os.path.join(JSON_DIR, "**", "*.json"), recursive=True)

bulk_locations = []
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        # Each top-level key is a person
        for person, devices in data.items():
            if not isinstance(devices, dict):
                continue
            for device, entries in devices.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    timestamp = entry.get("tst")
                    lat = entry.get("lat")
                    lon = entry.get("lon")
                    accuracy = entry.get("acc")
                    battery = entry.get("batt")
                    raw_json = json.dumps(entry)
                    bulk_locations.append((person, device, timestamp, lat, lon, accuracy, battery, raw_json))

# Bulk insert all locations at once
if bulk_locations:
    db.insert_locations_bulk(bulk_locations)