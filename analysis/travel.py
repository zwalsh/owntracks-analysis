"""
Travel episode detection module (stub).
"""

MILES_THRESHOLD = 10.0
MAX_WINDOW_SECONDS = 86400
MOVEMENT_MIN_DIST_MILES = 0.05
STATIONARY_RADIUS_MILES = 0.10


from typing import List, NamedTuple, Optional, Tuple
from analysis.distance_apart import haversine
from analysis.places import Point
from db.db import Location, LocationDB
import time
from datetime import datetime, date

from geocode.geocode import PlaceInfo

DB = LocationDB()

def _date_to_ts(d: str) -> int:
    # Converts YYYY-MM-DD to local midnight timestamp
    return int(time.mktime(datetime.strptime(d, "%Y-%m-%d").timetuple()))

def _local_time(ts: int) -> str:
    """
    Takes epoch time and outputs local military time of day hh:mm
    """
    return time.strftime("%H:%M", time.localtime(ts))

def _haversine_miles(loc1: Location, loc2: Location) -> float:
    return haversine(loc1["lat"], loc1["lon"], loc2["lat"], loc2["lon"]) * 0.000621371

class Travel(NamedTuple):
    person: str
    start_point: Point
    end_point: Point
    start_ts: int
    end_ts: int
    start_place: PlaceInfo
    end_place: PlaceInfo


def _find_first_travel(locations: List[Location]) -> Optional[Tuple[Location, Location]]:
    """
    Finds the first instance of Travel in the sorted array of Locations, where:

    - the "start" is the last Location interval within MOVEMENT_MIN_DIST_MILES of the start point
    - the "end" is the first Location interval within MOVEMENT_MIN_DIST_MILES of the end point
    - the timestamp_from of start and end are within MAX_WINDOW_SECONDS
    """

    for i, location in enumerate(locations):
        if i + 1 >= len(locations):
            break
        next_location = locations[i + 1]
        distance = _haversine_miles(location, next_location)
        if distance < MOVEMENT_MIN_DIST_MILES:
            continue
        print(f"Potential start: {_local_time(location['timestamp_from'])}, next: {_local_time(next_location['timestamp_from'])}, distance: {distance}")


        # if travel:
        #     return travel
    return None


def detect_travel(person: str, start_date: str = None, end_date: str = None) -> List[Travel]:
    """
    Detects travel episodes for a given person within the specified date range.
    """
    # Default dates: start of current year to today
    today = date.today()
    year_start = date(today.year, 1, 1)
    if not start_date:
        start_date = year_start.strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    start_ts = _date_to_ts(start_date)
    end_ts = _date_to_ts(end_date) + 86400

    locations = DB.get_locations_in_range(person, start_ts, end_ts)
    return _find_first_travel(locations)
