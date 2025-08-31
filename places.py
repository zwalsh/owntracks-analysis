from geocode import Geocoder
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


geocoder = Geocoder()

# Example usage:
if __name__ == "__main__":
    person = "jackie"
    places = cluster_locations_by_time(person)

    print(f"{'Place Name':<30} {'City':<20} {'State':<10} {'Time Spent (hours)':>18}")
    print("-" * 80)
    for point, hours in filter(lambda x: x[1] > 24, places):
        place_info = geocoder.get_place_info(point.lat, point.lon)
        name = (place_info.name or "")[:30]
        city = (getattr(place_info, "city", "") or "")[:20]
        state = (getattr(place_info, "state", "") or "")[:15]
        print(f"{name:<30} {city:<20} {state:<15} {hours:>18.2f}")
