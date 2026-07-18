import re

from app.core.config import DB_TYPE
from app.database.bp_client import BPClient
from app.database.iboss_client import IbossClient
from app.database.voss_client import VossClient
from app.database.bcare_client import BcareClient
from app.database.sqlite_client import SQLiteClient
from app.intents.loader import get_intent
from app.sql.validator import SQLValidator


class DatabaseConnectionError(Exception):
    pass


class BPDatabaseService:
    def __init__(self):
        self._clients = {}
        self._current_source = "bp"

    def _get_client(self, source: str):
        if source not in self._clients:
            if source == "iboss":
                self._clients[source] = IbossClient()
            elif source == "voss":
                self._clients[source] = VossClient()
            elif source == "bcare":
                self._clients[source] = BcareClient()
            elif DB_TYPE == "sqlite":
                self._clients[source] = SQLiteClient()
            else:
                self._clients[source] = BPClient()
        return self._clients[source]

    def generate_sql(self, payload: dict) -> str:
        intent_id = payload.get("intent", "")
        meta = get_intent(intent_id)
        if not meta:
            self._current_source = "bp"
            return ""
        self._current_source = meta.get("source", "bp")
        sql = meta["sql_template"]
        for key, value in payload.items():
            if key in ("intent",):
                continue
            sql = sql.replace(f"{{{key}}}", str(value))
        sql = re.sub(r"\{\w+\}", "1 = 1", sql)
        return sql

    def validate_sql(self, sql: str) -> bool:
        validator = SQLValidator(source=self._current_source)
        return bool(sql) and validator.validate(sql)

    def execute(self, sql: str, source: str = None):
        if source:
            self._current_source = source
        try:
            return self._get_client(self._current_source).execute(sql)
        except Exception as e:
            db_name = self._current_source.upper()
            raise DatabaseConnectionError(
                f"Gagal terhubung ke database {db_name}: {e}"
            ) from e
