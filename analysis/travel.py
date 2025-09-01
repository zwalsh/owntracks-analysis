"""
Travel episode detection module (stub).
"""

MILES_THRESHOLD = 10.0
MAX_WINDOW_SECONDS = 86400
MOVEMENT_MIN_DIST_MILES = 0.05
STATIONARY_RADIUS_MILES = 0.10


from db.db import LocationDB
import time
from datetime import datetime, date

DB = LocationDB()

def _date_to_ts(d: str) -> int:
    # Converts YYYY-MM-DD to local midnight timestamp
    return int(time.mktime(datetime.strptime(d, "%Y-%m-%d").timetuple()))

def detect_travel(person: str, start_date: str = None, end_date: str = None):
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
    print(f"Queried {len(locations)} location intervals for {person} in {start_date} to {end_date}")
    return []
