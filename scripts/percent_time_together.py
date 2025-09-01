"""
Script to run percent_minutes_spent_together analysis.
Usage:
    uv run scripts/percent_time_together.py [start_date] [end_date]
    # Dates in YYYY-MM-DD format
"""

import sys
from analysis.percent_time_together import percent_minutes_spent_together


def print_minutes_together(start_date, end_date):
    minutes_per_day = percent_minutes_spent_together(start_date, end_date)
    for day, minutes in minutes_per_day.items():
        pct = 100.0 * minutes / 1440
        bars = int(round(pct / 100 * 20))
        bar_str = "|" * bars + " " * (20 - bars)
        print(f"{day}: {minutes:4} minutes ({pct:6.2f}%) [{bar_str}]")


if __name__ == "__main__":
    start_date = None
    end_date = None
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    if len(sys.argv) > 2:
        end_date = sys.argv[2]
    print_minutes_together(start_date, end_date)
