"""Database service — Oracle (BP Batam) + SQLite (dev).

Menggabungkan template resolver, validator, dan DB client.
DB type dipilih via config DB_TYPE (oracle/sqlite).
"""

import re

from app.core.config import DB_TYPE
from app.database.bp_client import BPClient
from app.database.sqlite_client import SQLiteClient
from app.intents.loader import get_intent
from app.sql.validator import SQLValidator


class DatabaseConnectionError(Exception):
    pass


class BPDatabaseService:
    def __init__(self):
        self.validator = SQLValidator()
        self._oracle = None
        self._sqlite = None

    @property
    def client(self):
        if DB_TYPE == "sqlite":
            if self._sqlite is None:
                self._sqlite = SQLiteClient()
            return self._sqlite
        if self._oracle is None:
            self._oracle = BPClient()
        return self._oracle

    def generate_sql(self, payload: dict) -> str:
        intent_id = payload.get("intent", "")
        meta = get_intent(intent_id)
        if not meta:
            return ""
        sql = meta["sql_template"]
        for key, value in payload.items():
            if key in ("intent",):
                continue
            sql = sql.replace(f"{{{key}}}", str(value))
        sql = re.sub(r"\{\w+\}", "1 = 1", sql)
        return sql

    def validate_sql(self, sql: str) -> bool:
        return bool(sql) and self.validator.validate(sql)

    def execute(self, sql: str):
        try:
            return self.client.execute(sql)
        except Exception as e:
            db_name = "SQLite" if DB_TYPE == "sqlite" else "Oracle BP Batam"
            raise DatabaseConnectionError(
                f"Gagal terhubung ke database {db_name}: {e}"
            ) from e
