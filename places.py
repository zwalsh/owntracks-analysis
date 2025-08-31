import requests
from typing import List, Tuple, Dict
from db import LocationDB

class Point:
	def __init__(self, lat: float, lon: float):
		self.lat = lat
		self.lon = lon
	def __repr__(self):
		return f"Point(lat={self.lat:.3f}, lon={self.lon:.3f})"

# Granularity: ~0.001 deg lat/lon ≈ 100m, good for distinguishing places ~1 mile apart
ROUND_DIGITS = 2
DB = LocationDB()

def cluster_locations_by_time(person: str) -> List[Tuple[Point, float]]:
	locations = DB.get_locations(person=person)
	clusters: Dict[Tuple[float, float], float] = {}
	for loc in locations:
		# Round lat/lon to desired granularity
		lat_r = round(loc["lat"], ROUND_DIGITS)
		lon_r = round(loc["lon"], ROUND_DIGITS)
		key = (lat_r, lon_r)
		# Time spent at this location (seconds)
		timestamp_to = loc["timestamp_to"]
		if timestamp_to >= 2147483647:  # int max indicates "end" point
			continue

		duration = max(0, timestamp_to - loc["timestamp_from"])
		clusters[key] = clusters.get(key, 0) + duration
	# Convert to Point objects and hours spent
	result = [(Point(lat, lon), t / 3600.0) for (lat, lon), t in clusters.items()]
	# Sort by time spent descending
	result.sort(key=lambda x: -x[1])
	return result

import requests
import time

def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": 14,
        "addressdetails": 1
    }
    headers = {"User-Agent": "owntracks-analysis-script"}
    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("display_name", "Unknown")
    except Exception as e:
        print(f"Error geocoding {lat},{lon}: {e}")
    return "Unknown"

# Example usage:
if __name__ == "__main__":
	person = "zach"
	places = cluster_locations_by_time(person)
	for point, hours in places[:10]:
		name = reverse_geocode(point.lat, point.lon)
		print(f"{name:<30} ({point}): {hours:.2f} hours")

