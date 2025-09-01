from time import mktime, strptime
from geocode.geocode import Geocoder, PlaceInfo
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
GEOCODER = Geocoder()


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


def top_locations(
    person: str, year: int, hour_threshold=24
) -> List[Tuple[PlaceInfo, float]]:
    """
    Returns a list of all places the person spent more than hour_threshold hours at in the given year.

    Geocodes the places, returning a list of tuples containing the point, place name, and time spent.
    """
    places = cluster_locations_by_time(person, year)
    return [
        (GEOCODER.get_place_info(point.lat, point.lon), hours)
        for point, hours in filter(lambda x: x[1] > hour_threshold, places)
    ]
