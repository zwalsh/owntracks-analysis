from time import localtime, mktime, strptime
from geocode.geocode import Geocoder
from typing import List, Tuple, Dict
from db.db import LocationDB


class Point:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f"Point(lat={self.lat:.3f}, lon={self.lon:.3f})"


# Granularity: ~0.001 deg lat/lon ≈ 100m, good for distinguishing places ~1 mile apart
ROUND_DIGITS = 2
DB = LocationDB()


def cluster_locations_by_time(person: str, year: str) -> List[Tuple[Point, float]]:
    year_start_ts = int(mktime(strptime(f"{year}-01-01", "%Y-%m-%d")))
    year_end_ts = int(mktime(strptime(f"{year}-12-31", "%Y-%m-%d")))
    locations = DB.get_locations_in_range(
        person=person,
        from_ts=year_start_ts,
        to_ts=year_end_ts,
    )
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


geocoder = Geocoder()


def print_top_locations(person, year=str(localtime().tm_year)):
    places = cluster_locations_by_time(person, year)
    print(f"{'Place Name':<30} {'City':<20} {'State':<15} {'Country':<15} {'Time Spent (hours)':>18}")
    print("-" * 102)
    for point, hours in filter(lambda x: x[1] > 24, places):
        place_info = geocoder.get_place_info(point.lat, point.lon)
        name = (place_info.name or "")[:30]
        city = (getattr(place_info, "city", "") or "")[:20]
        state = (getattr(place_info, "state", "") or "")[:15]
        country = (getattr(place_info, "country", "") or "")[:15]
        print(f"{name:<30} {city:<20} {state:<15} {country:<15} {hours:>18.2f}")


# Example usage:
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        person = sys.argv[1]
        year = sys.argv[2] if len(sys.argv) > 2 else str(localtime().tm_year)
    else:
        print("Usage: uv run places.py <person> <year=current year>")
        sys.exit(1)
    places = cluster_locations_by_time(person, year)

    print(f"{'Place Name':<30} {'City':<20} {'State':<15} {'Country':<15} {'Time Spent (hours)':>18}")
    print("-" * 102)
    for point, hours in filter(lambda x: x[1] > 24, places):
        place_info = geocoder.get_place_info(point.lat, point.lon)
        name = (place_info.name or "")[:30]
        city = (getattr(place_info, "city", "") or "")[:20]
        state = (getattr(place_info, "state", "") or "")[:15]
        country = (getattr(place_info, "country", "") or "")[:15]
        print(f"{name:<30} {city:<20} {state:<15} {country:<15} {hours:>18.2f}")
