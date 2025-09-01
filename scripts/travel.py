"""
Script to invoke travel episode detection (stub).
Usage:
    uv run -m scripts.travel <person> [start_date] [end_date]
"""
import sys
from analysis.travel import detect_travel

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run -m scripts.travel <person> [start_date] [end_date]")
        sys.exit(1)
    person = sys.argv[1]
    start_date = sys.argv[2] if len(sys.argv) > 2 else None
    end_date = sys.argv[3] if len(sys.argv) > 3 else None
    detect_travel(person, start_date, end_date)
