
import math
import logging
import sys
from db.db import LocationDB
from datetime import datetime, timedelta, date

PERSON_A = "jackie"
PERSON_B = "zach"
FEET_THRESHOLD = 2000
METER_THRESHOLD = FEET_THRESHOLD * 0.3048

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



def percent_minutes_spent_together(start_date=None, end_date=None):
    """
    Logs the daily percentage of minutes two people spent together (within a distance threshold) over a date range.
    Dates should be in YYYY-MM-DD format. Defaults to current year-to-date.
    """
    db = LocationDB()
    today = date.today()
    year_start = date(today.year, 1, 1)
    if not start_date:
        start_date = year_start.strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    days = get_days_in_range(start_date, end_date)

    for day in days:
        minutes = get_minutes_in_day(day)
        dt = datetime.strptime(day, "%Y-%m-%d")
        start_ts = int(dt.timestamp())
        end_ts = int((dt + timedelta(days=1)).timestamp())
        intervals_a = db.get_locations_in_range(PERSON_A, start_ts, end_ts)
        intervals_b = db.get_locations_in_range(PERSON_B, start_ts, end_ts)

        def find_loc(intervals, ts):
            for loc in intervals:
                if loc["timestamp_from"] <= ts < loc["timestamp_to"]:
                    return loc["lat"], loc["lon"]
            return None

        together_count = 0
        total_count = 0
        for ts in minutes:
            loc_a = find_loc(intervals_a, ts)
            loc_b = find_loc(intervals_b, ts)
            if loc_a and loc_b:
                total_count += 1
                dist = haversine(loc_a[0], loc_a[1], loc_b[0], loc_b[1])
                if dist <= METER_THRESHOLD:
                    together_count += 1
        pct = 100.0 * together_count / total_count if total_count else 0.0
        bars = int(round(pct / 100 * 20))
        bar_str = "|" * bars + " " * (20 - bars)
        logging.info(
            f"{day}: together {together_count:4}/{total_count} minutes ({pct:.2f}%) [{bar_str}]"
        )


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
