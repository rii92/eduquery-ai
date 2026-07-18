from sqlalchemy import create_engine, text

from app.core.config import BCARE_DB_HOST, BCARE_DB_PORT, BCARE_DB_NAME, BCARE_DB_USER, BCARE_DB_PASSWORD


def _bcare_postgres_url() -> str:
    return f"postgresql+psycopg2://{BCARE_DB_USER}:{BCARE_DB_PASSWORD}@{BCARE_DB_HOST}:{BCARE_DB_PORT}/{BCARE_DB_NAME}"


class BcareClient:
    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                _bcare_postgres_url(),
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def execute(self, sql: str):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            return [{str(k).upper(): v for k, v in row._mapping.items()} for row in rows]
