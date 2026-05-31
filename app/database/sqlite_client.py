"""SQLite client untuk development / fallback."""

import sqlite3
import os
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = os.getenv("SQLITE_DB_PATH", str(_DB_DIR / "eduquery.db"))


class SQLiteClient:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def execute(self, sql: str) -> list[dict]:
        conn = self._get_conn()
        cur = conn.execute(sql)
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        conn.commit()
        return [dict(zip(cols, row)) for row in rows]

    def execute_file(self, sql_path: str):
        conn = self._get_conn()
        with open(sql_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
