"""
distance_apart.py

Helper functions for calculating the distance between two people over time using Owntracks data.
"""

import math
from typing import Generator, List, Optional
from analysis.places import Point
from db.db import Location, LocationDB

DB = LocationDB()


# Haversine formula for distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def find_loc(intervals: List[Location], ts: int) -> Optional[Point]:
    """
    Find the location (latitude, longitude) for a given timestamp within a list of intervals.
    """
    for loc in intervals:
        if loc["timestamp_from"] <= ts < loc["timestamp_to"]:
            return Point(loc["lat"], loc["lon"])
    return None


def location_generator(
    intervals: List[Location], timestamps: List[int]
) -> Generator[Optional[Point], None, None]:
    """
    Yields the location for each timestamp, advancing the interval generator as needed.
    Assumes intervals are sorted by timestamp_from.
    """
    interval_iter = iter(intervals)
    current = next(interval_iter, None)
    for ts in timestamps:
        # Advance to the next interval if the current one is before ts
        while current and not (ts < current["timestamp_to"]):
            assert current["timestamp_to"] <= ts
            current = next(interval_iter, None)
        if current:
            yield Point(current["lat"], current["lon"])
        else:
            yield None


def distance_apart_per_minute(
    person_a: str, person_b: str, start_ts: int, end_ts: int
) -> List[float]:
    """
    Returns an array of the distance between person_a and person_b in each minute between start_ts and end_ts.
    start_ts and end_ts are epoch seconds.
    """
    intervals_a = DB.get_locations_in_range(person_a, start_ts, end_ts)
    print(f"Got {len(intervals_a)} intervals for {person_a}")
    intervals_b = DB.get_locations_in_range(person_b, start_ts, end_ts)
    print(f"Got {len(intervals_b)} intervals for {person_b}")

    minutes_in_range = [start_ts + 60 * i for i in range((end_ts - start_ts) // 60)]
    distances = []

    a_intervals = location_generator(intervals_a, minutes_in_range)
    b_intervals = location_generator(intervals_b, minutes_in_range)

    for ts, a_point, b_point in zip(minutes_in_range, a_intervals, b_intervals):
        if a_point and b_point:
            dist = haversine(a_point.lat, a_point.lon, b_point.lat, b_point.lon)
            distances.append(dist)
        else:
            distances.append(0.0)
    return distances
