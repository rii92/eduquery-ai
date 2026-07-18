from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from app.core.config import IBOSS_DB_HOST, IBOSS_DB_PASSWORD, IBOSS_DB_SERVICE_NAME, IBOSS_DB_USER


def _iboss_oracle_url() -> str:
    user = quote_plus(IBOSS_DB_USER)
    pw = quote_plus(IBOSS_DB_PASSWORD)
    return f"oracle+oracledb://{user}:{pw}@{IBOSS_DB_HOST}/?service_name={IBOSS_DB_SERVICE_NAME}"


class IbossClient:
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                _iboss_oracle_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def execute(self, sql: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            return [{str(k).upper(): v for k, v in row._mapping.items()} for row in rows]
