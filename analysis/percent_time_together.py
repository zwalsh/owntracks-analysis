import logging
import sys
from typing import Dict
from db.db import LocationDB
from datetime import datetime, timedelta, date
from analysis.distance_apart import distance_apart_per_minute

PERSON_A = "jackie"
PERSON_B = "zach"
FEET_THRESHOLD = 2000
METER_THRESHOLD = FEET_THRESHOLD * 0.3048
DB = LocationDB()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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


def percent_minutes_spent_together(start_date=None, end_date=None) -> Dict[str, int]:
    today = date.today()
    year_start = date(today.year, 1, 1)
    if not start_date:
        start_date = year_start.strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    days = get_days_in_range(start_date, end_date)

    # Pull all distances in one query
    dt_start = datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.strptime(end_date, "%Y-%m-%d")
    start_ts = int(dt_start.timestamp())
    end_ts = int((dt_end + timedelta(days=1)).timestamp())
    all_distances = distance_apart_per_minute(PERSON_A, PERSON_B, start_ts, end_ts)

    minutes_per_day = {}
    minutes_per_day_list = [
        all_distances[i : i + 1440] for i in range(0, len(all_distances), 1440)
    ]
    for idx, day in enumerate(days):
        distances_apart = (
            minutes_per_day_list[idx] if idx < len(minutes_per_day_list) else []
        )
        minutes = sum(1 for d in distances_apart if d <= METER_THRESHOLD)
        minutes_per_day[day] = minutes
    return minutes_per_day


if __name__ == "__main__":
    # Usage: python -m analysis.analysis [start_date] [end_date]
    # Dates in YYYY-MM-DD format
    start_date = None
    end_date = None
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    if len(sys.argv) > 2:
        end_date = sys.argv[2]
    percent_minutes_spent_together(start_date, end_date)
