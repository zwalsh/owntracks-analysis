import os
import glob
import json
from datetime import datetime
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
    # Counters for logging
    total_entries = 0
    skipped_missing = 0
    skipped_zero = 0
    skipped_invalid = 0
    skipped_dup_same = 0
    skipped_dup_conflict = 0
    # track last seen (person, device, timestamp) -> (lat, lon) to dedupe across files
    last_seen = {}
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
                        if i + 1 < len(entries_sorted):
                            timestamp_to = entries_sorted[i + 1].get("tst")
                        else:
                            continue  # discard the last entry because we don't know a following timestamp

                        timestamp = entry.get("tst")
                        lat = entry.get("lat")
                        lon = entry.get("lon")
                        accuracy = entry.get("acc")
                        battery = entry.get("batt")

                        total_entries += 1

                        # Skip malformed/invalid coordinates: missing or zero lat/lon
                        if lat is None or lon is None:
                            skipped_missing += 1
                            continue
                        try:
                            # treat exact zero as invalid GPS coordinate in this dataset
                            if float(lat) == 0.0 or float(lon) == 0.0:
                                skipped_zero += 1
                                continue
                        except Exception:
                            # if lat/lon cannot be cast to float, skip
                            skipped_invalid += 1
                            continue

                        # Deduplicate by (person, device, timestamp)
                        key = (person, device, timestamp)
                        if key in last_seen:
                            prev_lat, prev_lon = last_seen[key]
                            try:
                                same_lat = float(prev_lat) == float(lat)
                                same_lon = float(prev_lon) == float(lon)
                            except Exception:
                                same_lat = False
                                same_lon = False
                            if same_lat and same_lon:
                                skipped_dup_same += 1
                                continue
                            else:
                                skipped_dup_conflict += 1
                                # skip the conflicting later entry
                                continue
                        # record first-seen coords for this key
                        last_seen[key] = (lat, lon)

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
                            )
                        )

    # Bulk insert all locations at once
    if bulk_locations:
        db.insert_locations_bulk(bulk_locations)
    # Print summary
    print(
        f"Import summary: total_entries={total_entries}, inserted={len(bulk_locations)}, skipped_missing={skipped_missing}, skipped_zero={skipped_zero}, skipped_invalid={skipped_invalid}, skipped_dup_same={skipped_dup_same}, skipped_dup_conflict={skipped_dup_conflict}"
    )


if __name__ == "__main__":
    run_import()
