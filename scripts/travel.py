"""
Script to invoke travel episode detection (stub).
Usage:
    uv run -m scripts.travel <person> [start_date] [end_date]
"""
import sys
from analysis.distance_apart import haversine
from analysis.travel import Travel, detect_travel
from datetime import datetime



def _print_travel_line(travel: Travel):
    # Format times
    start_dt = datetime.fromtimestamp(travel.start_ts)
    end_dt = datetime.fromtimestamp(travel.end_ts)
    start_date = start_dt.strftime('%Y-%m-%d')
    start_time = start_dt.strftime('%H:%M')
    end_date = end_dt.strftime('%Y-%m-%d')
    end_time = end_dt.strftime('%H:%M')

    # Place info
    PLACE_SIZE = 30
    STATE_SIZE = 15
    start_place = travel.start_place.name[:PLACE_SIZE]
    start_state = travel.start_place.state[:STATE_SIZE]
    end_place = travel.end_place.name[:PLACE_SIZE]
    end_state = travel.end_place.state[:STATE_SIZE]

    # Distance
    distance = haversine(travel.start_point.lat, travel.start_point.lon, travel.end_point.lat, travel.end_point.lon) * 0.000621371

    # Duration
    duration_seconds = travel.end_ts - travel.start_ts
    duration_hours = duration_seconds / 3600.0
    duration_hhmm = f"{int(duration_hours):02d}:{int((duration_hours%1)*60):02d}"

    # Speed
    speed = distance / duration_hours if duration_hours > 0 else 0.0

    print(f"{start_date:<12} {start_time:<8} {end_date:<12} {end_time:<8} {start_place:<30} {start_state:<15} {end_place:<30} {end_state:<15} {distance:>8.2f} miles  {duration_hhmm:>6} time {speed:>8.2f} mph")


def _print_travels(person, start_date, end_date):
    """
    Prints a table for Travel segments. 
    """
    travels = detect_travel(person, start_date, end_date)

    print(f"Travel segments for {person}:")
    print(f"{'Start Date':<12} {'Time':<8} {'End Date':<12} {'Time':<8} {'Start Place':<46} {'End Place':<46} {'Distance':>14} {'Time':>12} {'Speed':>12}")
    print("=" * 178)
    for segment in travels:
        _print_travel_line(segment)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run -m scripts.travel <person> [start_date] [end_date]")
        sys.exit(1)
    person = sys.argv[1]
    start_date = sys.argv[2] if len(sys.argv) > 2 else None
    end_date = sys.argv[3] if len(sys.argv) > 3 else None
    _print_travels(person, start_date, end_date)
