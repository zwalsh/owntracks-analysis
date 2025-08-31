# Owntracks Analysis

This project analyzes location history exported from Owntracks, using Python and SQLite. It supports importing, clustering, reverse geocoding, and time-based analysis.

## Directory Structure

- `owntracks-json/` — Place your exported Owntracks JSON files here. (e.g., `2021.json`, `2022.json`, ...)
- `db/` — Database interface and schema logic (`db.py`).
- `geocode/` — Reverse geocoding and place info (`geocode.py`).
- `analysis/` — Analysis scripts (e.g., clustering, time spent, etc.).
- `import/` — Import script for building the SQLite database from Owntracks JSON (`import.py`).
- `locations.db` — The generated SQLite database (created by import script).
- `geocode_cache.json` — Disk cache for geocoding responses.

## Setup

1. **Install dependencies**
   ```bash
   uv pip install .
   ```

2. **Place Owntracks JSON files**
   - Copy your exported files into the `owntracks-json/` directory.
   - Export from the Owntracks frontend by selecting a time period and clicking the download button in the top right. 

3. **Import data into SQLite**
   - Run from the project root:
     ```bash
     uv run -m import.import
     ```
   - This will create `locations.db` in the project root.

## Analysis

- Example: Cluster locations by time spent
  ```bash
  uv run -m analysis.places <person> [year]
  ```
  - Replace `<person>` with the name used in your Owntracks export.

- Other analysis scripts are in the `analysis/` directory. See their docstrings for usage.

## Geocoding
- Reverse geocoding is cached in `geocode_cache.json`.
- The geocoding logic is in `geocode/geocode.py`.
