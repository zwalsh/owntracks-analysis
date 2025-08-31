import sqlite3
from typing import List, Dict, Any, Optional, TypedDict


DB_PATH = "locations.db"


class Location(TypedDict):
    person: str
    device: str
    timestamp_from: int
    timestamp_to: int
    lat: float
    lon: float
    accuracy: Optional[float]
    battery: Optional[float]
    raw_json: str


class LocationDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def create_schema(self):
        """
        Create the locations table schema in the database.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person TEXT,
                    device TEXT,
                    timestamp_from INTEGER,
                    timestamp_to INTEGER,
                    lat REAL,
                    lon REAL,
                    accuracy REAL,
                    battery REAL,
                    raw_json TEXT
                )
            """)
            conn.commit()

    def insert_location(
        self,
        person: str,
        device: str,
        timestamp: int,
        lat: float,
        lon: float,
        accuracy: Optional[float],
        battery: Optional[float],
        raw_json: str,
    ):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO locations (person, device, timestamp, lat, lon, accuracy, battery, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (person, device, timestamp, lat, lon, accuracy, battery, raw_json),
            )
            conn.commit()

    def get_locations(
        self, person: Optional[str] = None, device: Optional[str] = None
    ) -> List[Location]:
        with self._connect() as conn:
            cur = conn.cursor()
            query = "SELECT person, device, timestamp, lat, lon, accuracy, battery, raw_json FROM locations"
            params = []
            conditions = []
            if person:
                conditions.append("person = ?")
                params.append(person)
            if device:
                conditions.append("device = ?")
                params.append(device)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [Location(**dict(zip(columns, row))) for row in cur.fetchall()]

    def insert_locations_bulk(self, locations: List[Location]):
        """
        Bulk insert locations.
        locations: list of Location dicts
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT INTO locations (person, device, timestamp_from, timestamp_to, lat, lon, accuracy, battery, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        loc["person"],
                        loc["device"],
                        loc["timestamp_from"],
                        loc["timestamp_to"],
                        loc["lat"],
                        loc["lon"],
                        loc["accuracy"],
                        loc["battery"],
                        loc["raw_json"],
                    )
                    for loc in locations
                ],
            )
            conn.commit()
