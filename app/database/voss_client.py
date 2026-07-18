from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.core.config import VOSS_DB_HOST, VOSS_DB_PASSWORD, VOSS_DB_SERVICE_NAME, VOSS_DB_USER


def _voss_oracle_url() -> str:
    user = quote_plus(VOSS_DB_USER)
    pw = quote_plus(VOSS_DB_PASSWORD)
    return f"oracle+oracledb://{user}:{pw}@{VOSS_DB_HOST}/?service_name={VOSS_DB_SERVICE_NAME}"


class VossClient:
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                _voss_oracle_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def execute(self, sql: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            return [{str(k).upper(): v for k, v in row._mapping.items()} for row in rows]
