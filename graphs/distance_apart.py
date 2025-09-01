import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from analysis.distance_apart import distance_apart_per_minute


import time

import matplotlib.ticker as ticker


def minute_to_hhmm(x, pos):
    h = int(x) // 60
    m = int(x) % 60
    return f"{h:02d}:{m:02d}"


def plot_distance_apart_for_day(person_a: str, person_b: str, day: str):
    """
    Plots the per-minute distance apart for two people on a given day, adjusted for system local timezone.
    day: string in YYYY-MM-DD format
    """
    # Convert local date to local midnight timestamp
    dt_local = datetime.strptime(day, "%Y-%m-%d")
    start_ts = int(time.mktime(dt_local.timetuple()))
    end_ts = int(time.mktime((dt_local + timedelta(days=1)).timetuple()))
    distances = distance_apart_per_minute(person_a, person_b, start_ts, end_ts)
    minutes = list(range(1440))
    # Format x-axis as HH:MM
    plt.figure(figsize=(12, 4))
    plt.plot(minutes, distances, label=f"Distance apart ({person_a} vs {person_b})")
    plt.xlabel("Time of day (local, HH:MM)")
    plt.ylabel("Distance apart (meters)")
    plt.title(
        f"Distance Apart Per Minute: {person_a} & {person_b} on {day} (local time)"
    )
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(60))
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(minute_to_hhmm))
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run -m graphs.distance_apart <day YYYY-MM-DD> [person_a] [person_b]")
        sys.exit(1)
    day = sys.argv[1]
    person_a = sys.argv[2] if len(sys.argv) > 2 else "jackie"
    person_b = sys.argv[3] if len(sys.argv) > 3 else "zach"
    plot_distance_apart_for_day(person_a, person_b, day)
