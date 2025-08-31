import os
import glob
import json
from db.db import LocationDB, DB_PATH, Location

JSON_DIR = "owntracks-json"

def run_import():
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

                    # Sort entries by timestamp
                    entries_sorted = sorted(entries, key=lambda e: e.get("tst", 0))
                    for i, entry in enumerate(entries_sorted):
                        timestamp_from = entry.get("tst")
                        if i + 1 < len(entries_sorted):
                            timestamp_to = entries_sorted[i + 1].get("tst")
                        else:
                            timestamp_to = 2147483647

                        timestamp = entry.get("tst")
                        lat = entry.get("lat")
                        lon = entry.get("lon")
                        accuracy = entry.get("acc")
                        battery = entry.get("batt")
                        raw_json = json.dumps(entry)
                        bulk_locations.append(
                            Location(
                                person=person,
                                device=device,
                                timestamp_from=timestamp,
                                timestamp_to=timestamp_to,
                                lat=lat,
                                lon=lon,
                                accuracy=accuracy,
                                battery=battery,
                                raw_json=raw_json,
                            )
                        )


    # Bulk insert all locations at once
    if bulk_locations:
        db.insert_locations_bulk(bulk_locations)

if __name__ == "__main__":
    run_import()