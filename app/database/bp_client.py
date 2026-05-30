"""Database client untuk BP Batam Data Warehouse (Oracle).

Menggunakan python-oracledb dalam thin mode (tanpa Oracle Instant Client).
Engine dibuat lazy — koneksi hanya terjadi saat execute() dipanggil.
"""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.core.config import BP_DB_HOST, BP_DB_PASSWORD, BP_DB_SERVICE_NAME, BP_DB_USER


def _bp_oracle_url() -> str:
    user = quote_plus(BP_DB_USER)
    pw = quote_plus(BP_DB_PASSWORD)
    return f"oracle+oracledb://{user}:{pw}@{BP_DB_HOST}/?service_name={BP_DB_SERVICE_NAME}"


class BPClient:
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                _bp_oracle_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def execute(self, sql: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            return [{str(k).upper(): v for k, v in row._mapping.items()} for row in rows]
