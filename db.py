import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = "locations.db"

class LocationDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def insert_location(self, person: str, device: str, timestamp: int, lat: float, lon: float,
                        accuracy: Optional[float], battery: Optional[float], raw_json: str):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO locations (person, device, timestamp, lat, lon, accuracy, battery, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (person, device, timestamp, lat, lon, accuracy, battery, raw_json))
            conn.commit()

    def get_locations(self, person: Optional[str] = None, device: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.connect() as conn:
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
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def insert_locations_bulk(self, locations: list):
        """
        Bulk insert locations.
        locations: list of tuples (person, device, timestamp, lat, lon, accuracy, battery, raw_json)
        """
        with self.connect() as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT INTO locations (person, device, timestamp, lat, lon, accuracy, battery, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                locations
            )
            conn.commit()