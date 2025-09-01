"""
Travel episode detection module (stub).
"""

MILES_THRESHOLD = 10.0
MAX_WINDOW_SECONDS = 86400
MOVEMENT_MIN_DIST_MILES = 0.05
MINIMUM_SPEED_MPH = 5.0


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


def _is_moving(start: Location, end: Location) -> bool:
    """
    Determine whether the two locations could represent a moving segment during a trip:
    - They could be less than 10 minutes apart (meaning two points in the same place), OR:

    - They must be at least MOVEMENT_MIN_DIST_MILES miles apart AND
    - The speed must be at least MINIMUM_SPEED_MPH
    """
    distance = _haversine_miles(start, end)
    time_in_hours = (end["timestamp_from"] - start["timestamp_from"]) / 60.0 / 60.0

    if time_in_hours == 0.0:
        return False

    speed =(distance / time_in_hours)
    is_moving = time_in_hours < (10.0 / 60.0) or distance >= MOVEMENT_MIN_DIST_MILES and speed >= MINIMUM_SPEED_MPH
    return is_moving

def _is_travel(start: Location, end: Location) -> bool:
    """
    Determine whether two locations could represent a travel episode.

    - They must be less than 24 hours apart
    - They must be at least MILES_THRESHOLD miles apart
    - The average speed must be MINIMUM_SPEED_MPH
    """

    time_in_hours = (end["timestamp_from"] - start["timestamp_from"]) / 60.0 / 60.0

    if time_in_hours > 24.0:
        return False
    if time_in_hours == 0: # Two segments at the same time cannot be travel
        return False
    
    distance = _haversine_miles(start, end)
    speed = distance / time_in_hours

    return distance >= MILES_THRESHOLD and speed >= MINIMUM_SPEED_MPH


def _find_travel_locations(start_location: int, locations: List[Location]) -> Optional[Tuple[Location, Location]]:
    """
    Given a start index in locations, finds the corresponding end index that defines a travel episode.
    Returns a Travel object or None if no valid travel episode is found.
    """
    start = locations[start_location]
    for i, end in enumerate(locations[start_location + 1:], start=start_location + 1):

        if _is_travel(start, end):
            # Expand until two consecutive locations indicate we are no longer traveling
            for j in range(i + 1, len(locations)):
                next_location = locations[j]
                if not _is_moving(end, next_location) or not _is_travel(start, next_location):
                    return (start, end)
                end = next_location

            return (start, end)
    return None


def _find_first_travel_locations(locations: List[Location]) -> Optional[Tuple[Location, Location]]:
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
        if not _is_moving(location, next_location):
            continue
        travel = _find_travel_locations(i, locations)
        if travel:
            return travel
    return None

def _find_all_travel_locations(locations: List[Location]) -> List[Tuple[Location, Location]]:
    travel_segments = []
    
    segment = _find_first_travel_locations(locations)
    while segment:
        travel_segments.append(segment)
        segment = _find_first_travel_locations(locations[locations.index(segment[1]) + 1:])
    return travel_segments


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

    travel_segments = _find_all_travel_locations(locations)
    for segment in travel_segments:
        distance = _haversine_miles(segment[0], segment[1])
        time_hours = (segment[1]['timestamp_from'] - segment[0]['timestamp_from']) / 60.0 / 60.0
        speed = distance / time_hours
        start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(segment[0]['timestamp_from']))
        end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(segment[1]['timestamp_from']))
        print(f"Start: {start_time}, End: {end_time}, Distance: {distance:.1f} miles, Hours: {time_hours:.1f}, Speed: {speed:.1f} mph")
