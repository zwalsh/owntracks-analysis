
import math
import logging
import sys
from typing import Dict, List, Optional
from analysis.places import Point
from db.db import LocationDB
from datetime import datetime, timedelta, date

PERSON_A = "jackie"
PERSON_B = "zach"
FEET_THRESHOLD = 2000
METER_THRESHOLD = FEET_THRESHOLD * 0.3048
DB = LocationDB()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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


def get_minutes_in_day(date):
    from datetime import datetime, timedelta

    dt = datetime.strptime(date, "%Y-%m-%d")
    start = int(dt.timestamp())
    end = int((dt + timedelta(days=1)).timestamp())
    return [start + 60 * i for i in range((end - start) // 60)]



def get_days_in_range(start_date, end_date):
    days = []
    d = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
    while d <= end_d:
        days.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return days


def find_loc(intervals, ts) -> Optional[Point]:
    """
    Find the location (latitude, longitude) for a given timestamp within a list of intervals.
    """
    for loc in intervals:
        if loc["timestamp_from"] <= ts < loc["timestamp_to"]:
            return Point(loc["lat"], loc["lon"])
    return None


def distance_apart_per_minute(start_ts: int, end_ts: int) -> List[float]:
    """
    Returns an array of the distance between PERSON_A and PERSON_B in each minute between start_ts and end_ts.

    start_ts and end_ts are epoch seconds.
    """
    intervals_a = DB.get_locations_in_range(PERSON_A, start_ts, end_ts)
    intervals_b = DB.get_locations_in_range(PERSON_B, start_ts, end_ts)

    minutes_in_range = [start_ts + 60 * i for i in range((end_ts - start_ts) // 60)]
    distances = []
    for ts in minutes_in_range:
        loc_a = find_loc(intervals_a, ts)
        loc_b = find_loc(intervals_b, ts)
        if loc_a and loc_b:
            dist = haversine(loc_a.lat, loc_a.lon, loc_b.lat, loc_b.lon)
            distances.append(dist)
        else:
            distances.append(0.0)
    return distances


def percent_minutes_spent_together(start_date=None, end_date=None) -> Dict[str, int]:
    """
    Logs the daily percentage of minutes two people spent together (within a distance threshold) over a date range.
    Dates should be in YYYY-MM-DD format. Defaults to current year-to-date.
    """
    today = date.today()
    year_start = date(today.year, 1, 1)
    if not start_date:
        start_date = year_start.strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    days = get_days_in_range(start_date, end_date)

    minutes_per_day = {}

    for day in days:
        dt = datetime.strptime(day, "%Y-%m-%d")
        start_ts = int(dt.timestamp())
        end_ts = int((dt + timedelta(days=1)).timestamp())
       
        distances_apart = distance_apart_per_minute(start_ts, end_ts)
        minutes = sum(1 for d in distances_apart if d <= METER_THRESHOLD)
        pct = 100.0 * minutes / 1440
        bars = int(round(pct / 100 * 20))
        bar_str = "|" * bars + " " * (20 - bars)
        logging.info(
            f"{day}: together {minutes:4}/1440 minutes ({pct:.2f}%) [{bar_str}]"
        )
        minutes_per_day[day] = minutes
    return minutes_per_day

if __name__=="__main__":
    # Usage: python -m analysis.analysis [start_date] [end_date]
    # Dates in YYYY-MM-DD format
    start_date = None
    end_date = None
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    if len(sys.argv) > 2:
        end_date = sys.argv[2]
    percent_minutes_spent_together(start_date, end_date)
