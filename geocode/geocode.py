from typing import NamedTuple

import requests
import json
import os
import time

CACHE_FILE = "geocode_cache.json"
USER_AGENT = "owntracks-analysis-script"


class PlaceInfo(NamedTuple):
    name: str
    display_name: str
    city: str
    state: str
    country: str


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

    def reverse_geocode(self, lat: float, lon: float, round_digits = 2) -> dict:
        # Approximate to avoid too many overly-precise requests.
        # 2 digits rounds to the nearest ~1.1km
        lat = round(lat, round_digits)
        lon = round(lon, round_digits)

        key = f"{lat:.5f},{lon:.5f}"
        if key in self.cache:
            return self.cache[key]
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": 14,
            "addressdetails": 1,
        }
        headers = {"User-Agent": USER_AGENT}
        try:
            print(f"Geocoding ({lat}, {lon})")
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                self.cache[key] = data
                self._save_cache()
                time.sleep(1)  # Be polite to the API
                return data
        except Exception as e:
            print(f"Error geocoding {lat},{lon}: {e}")
        self.cache[key] = {"display_name": "Unknown"}
        self._save_cache()
        return {"display_name": "Unknown"}

    def get_place_info(self, lat: float, lon: float) -> "PlaceInfo":
        resp = self.reverse_geocode(lat, lon)
        address = resp.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("hamlet")
            or address.get("suburb")
            or address.get("quarter")
            or address.get("neighbourhood")
            or address.get("county")
            or "Unknown"
        )
        return PlaceInfo(
            name=resp.get("name", "Unknown"),
            display_name=resp.get("display_name", "Unknown"),
            city=city,
            state=address.get("state", "Unknown"),
            country=address.get("country", "Unknown"),
        )
