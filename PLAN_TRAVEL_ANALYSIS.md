# Travel Detection Feature Plan

## 1. Goal

Identify and list "travel episodes" for a single person over a date span: any occurrence where the person moved more than a threshold distance (hard‑coded 10 miles) within less than a maximum time window (hard‑coded < 1 day = 86,400 seconds). Interface:

```
uv run -m scripts.travel <person> [start_date] [end_date]
```

Dates optional (YYYY-MM-DD). Defaults: start of current year to today (local or UTC – see Time Handling).

## 2. Requirements

- CLI script: `scripts/travel.py` (entry point only – all logic resides in `analysis/travel.py`).
- Hard‑coded constants: `MILES_THRESHOLD = 10.0`, `MAX_WINDOW_SECONDS = 86400`.
- Defaults: `start_date = Jan 1 current year`, `end_date = today` (consistent with existing percent time together logic).
- Output: human-readable table of detected travel episodes.
- Each episode fields:
  - start_time (ISO / local readable)
  - end_time
  - duration_hours
  - start_lat, start_lon (rounded 4)
  - end_lat, end_lon (rounded 4)
  - distance_miles (2 decimals)
- Summary footer: number of episodes, max distance, average distance.
- Avoid duplicate overlapping episodes (merge / reduce logic).
- Performance acceptable for typical yearly dataset (< ~100k points). No premature optimization unless required.

## 3. Data Source & Existing APIs

- Use `LocationDB.get_locations_in_range(person, from_ts, to_ts)` from `db/db.py`.
- Returned items (interval rows) include `timestamp_from`, `timestamp_to`, `lat`, `lon`.
- We only need representative points. Strategy: use each interval's `timestamp_from` & (lat, lon). Ignore rows with `timestamp_to` near int max (open-ended) for window end logic.

## 4. Time Handling

- Current codebase treats DB timestamps as Unix epoch seconds (UTC). Some newer graph code converts _local_ dates to timestamps using `time.mktime` (localtime). To stay consistent:
  - For now, interpret input dates as _local_ day boundaries (reuse approach in graph code) and convert via `time.mktime`.
  - Document this in the new module.
  - Provide easy future switch to UTC (wrap conversion helper).

## 5. Core Algorithm (Sliding Window + Start Contraction)

Goal: Detect sustained travel episodes where endpoint distance ≥ MILES_THRESHOLD within ≤ MAX_WINDOW_SECONDS, and ensure the episode start reflects the _actual departure_, not earlier idle time.

### Key Concepts

_Initial threshold crossing_ identifies that travel occurred; _start contraction_ rewinds the start to the last stationary point before genuine movement. This prevents hours of pre-trip idleness from inflating duration.

### Additional Constants

- `MOVEMENT_MIN_DIST_MILES = 0.05` — minimum step distance to count as movement (filters jitter)
- `STATIONARY_RADIUS_MILES = 0.10` (optional) — maximum radius to consider prior points stationary cluster

### Steps (Refined)

1. Fetch intervals in [start_ts, end_ts).
2. Build sorted `points = [(ts_from, lat, lon), ...]`.

- Optionally drop consecutive duplicates / micro‑jitter (rounded coords).

3. Two‑pointer scan to find first threshold crossing:

- For each candidate start index `i`:
  - Advance `j` while `ts_j - ts_i <= MAX_WINDOW_SECONDS`.
  - If `distance(points[i], points[j]) >= MILES_THRESHOLD`, record crossing (i, j) and proceed to contraction.
  - If window exceeded without crossing, increment `i`.

4. Start contraction (refine episode start):

- Walk backwards from `j-1` down to `i+1`.
- Find the earliest index `k` where segment distance(points[k], points[k+1]) ≥ MOVEMENT_MIN_DIST_MILES.
- Set `start_idx = k` (departure begins after stationary jitter). If none found, keep `start_idx = i`.
- (Optional) Verify all points between original `i` and `start_idx` lie within STATIONARY_RADIUS_MILES of the anchor; otherwise skip contraction.

5. (Optional future) Episode expansion beyond `j` to include continued movement until a stationary gap or window limit. (Deferred for MVP.)
6. Record episode spanning `[start_idx, j]` if endpoint distance ≥ threshold.
7. Advance outer loop intelligently: set `i = j + 1` to avoid overlapping duplicates (simpler) or `i += 1` if exploring overlapping candidates (then deduplicate later).
8. Post‑process (if overlaps allowed): sort by (start_ts, -distance); greedily keep non‑contained episodes.
9. Format & output table plus summary.

### Complexity

Typical near O(n \* avg_window_density); contraction is O(window_size) worst case but negligible relative to scan. Adequate for yearly datasets. Optimizations (bounding box pruning, vectorization) can be added later if profiling shows hotspots.

## 6. Distance Utility

Reuse existing Haversine (currently in `analysis/distance_apart.py`). To avoid circular imports, copy or extract a shared utility (`analysis/utils.py`). Simpler initial path: reimplement small function inside `travel.py` (few lines) and optionally refactor later.

## 7. Edge Cases / Filtering

- Missing or sparse data: No episodes → print "No travel detected." with 0 summary.
- Large GPS jumps (teleport) due to bad data: Optionally mark episodes where implied speed > 300 mph and either (a) still list with a warning flag, or (b) exclude. For MVP: include but annotate if speed > 150 mph.
- Duplicate timestamps: if identical ts for different coords, treat as separate points (rare). Optionally deduplicate.
- Open-ended intervals (`timestamp_to` = large sentinel): still use `timestamp_from` as point.

## 8. Output Formatting Example

```
Travel Episodes (threshold 10.0 mi within <= 24.0 h)
Start                End                  Dur(h)  Start(lat,lon)      End(lat,lon)        Miles  Notes
2025-02-14 08:12     2025-02-14 16:45     8.55    41.1234,-72.1234    40.7128,-74.0060   112.4
...
Total episodes: 5 | Max distance: 452.3 mi | Avg distance: 134.7 mi
```

## 9. Module / Script Layout

- `analysis/travel.py`:
  - Constants: `MILES_THRESHOLD`, `MAX_WINDOW_SECONDS`.
  - `detect_travel(person: str, start_date: str | None, end_date: str | None) -> List[Episode]`.
  - `Episode` dataclass: start_ts, end_ts, start_lat, start_lon, end_lat, end_lon, distance_miles, duration_hours, speed_mph (optional), notes.
  - Helper functions: `_load_points`, `_haversine_meters`, `_format_ts`, `_merge_or_filter_episodes`.
- `scripts/travel.py`:
  - Parse args, call `detect_travel`, print formatted table.

## 10. Testing / Validation Plan

- Manual test: Run for person with known travel days; verify distances approximate real journeys (compare start/end coords).
- Edge test: Short date range with no movement → empty result.
- Synthetic test (optional future): Insert two points 11 miles apart within an hour → expect one episode.

## 11. Future Enhancements (Not in MVP)

- Parameterize threshold & window via CLI flags.
- Infer multi-leg journeys (chain points) and compute cumulative path distance instead of great-circle endpoints.
- Speed filtering & anomaly detection.
- Export to CSV / JSON.
- Visualization (distance over time or mapping with folium).

## 12. Implementation Order

1. Implement `analysis/travel.py` with detection logic + dataclass.
2. Add script `scripts/travel.py`.
3. Run basic manual tests (short ranges) to verify output.
4. Update README with usage snippet.

## 13. Open Questions / Assumptions

- Using local midnight boundaries for date inputs (consistent with existing graph script). Document this.
- Treat any qualified pair as an episode without chaining intermediate path distance.
- Accept performance as-is; optimize only if observed slow.

---

Prepared plan for implementing travel detection feature.
