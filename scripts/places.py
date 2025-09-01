"""
Script to run places clustering analysis.
Usage:
    uv run scripts/places.py <person> [year]
"""

from time import localtime
import sys
from analysis.places import top_locations


def print_top_locations(person, year):
    places = top_locations(person, year)
    print(
        f"{'Place Name':<30} {'City':<20} {'State':<15} {'Country':<15} {'Time Spent (hours)':>18}"
    )
    print("-" * 102)
    for place_info, hours in places:
        name = (place_info.name or "")[:30]
        city = (getattr(place_info, "city", "") or "")[:20]
        state = (getattr(place_info, "state", "") or "")[:15]
        country = (getattr(place_info, "country", "") or "")[:15]
        print(f"{name:<30} {city:<20} {state:<15} {country:<15} {hours:>18.2f}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        person = sys.argv[1]
        year = sys.argv[2] if len(sys.argv) > 2 else str(localtime().tm_year)
    else:
        print("Usage: uv run scripts/places.py <person> [year]")
        sys.exit(1)
    print_top_locations(person, year)
