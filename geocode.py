import requests
import json
import os
import time
from typing import Tuple

CACHE_FILE = "geocode_cache.json"
USER_AGENT = "owntracks-analysis-script"

class Geocoder:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def reverse_geocode_name(self, lat: float, lon: float) -> str:
        key = f"{lat:.5f},{lon:.5f}"
        if key in self.cache:
            return self.cache[key]["display_name"]
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": 14,
            "addressdetails": 1
        }
        headers = {"User-Agent": USER_AGENT}
        try:
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                self.cache[key] = data
                self._save_cache()
                time.sleep(1)  # Be polite to the API
                return data["display_name"]
        except Exception as e:
            print(f"Error geocoding {lat},{lon}: {e}")
        self.cache[key] = {"display_name": "Unknown"}
        self._save_cache()
        return {"display_name": "Unknown"}
