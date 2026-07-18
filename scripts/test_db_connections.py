"""Test all database connections.

Usage:
    uv run python scripts/test_db_connections.py

Each database is tested independently. Continue to next if one fails.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import (
    DB_TYPE,
    BP_DB_USER, BP_DB_PASSWORD, BP_DB_HOST, BP_DB_SERVICE_NAME,
    IBOSS_DB_USER, IBOSS_DB_PASSWORD, IBOSS_DB_HOST, IBOSS_DB_SERVICE_NAME,
    VOSS_DB_USER, VOSS_DB_PASSWORD, VOSS_DB_HOST, VOSS_DB_SERVICE_NAME,
    BCARE_DB_HOST, BCARE_DB_PORT, BCARE_DB_NAME, BCARE_DB_USER, BCARE_DB_PASSWORD,
)


def test_oracle(label, user, password, host, service):
    print(f"  [{label}] Connecting Oracle {user}@{host}/{service} ...", end=" ")
    try:
        from sqlalchemy import create_engine, text
        from urllib.parse import quote_plus
        url = f"oracle+oracledb://{quote_plus(user)}:{quote_plus(password)}@{host}/?service_name={service}"
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM DUAL"))
            row = result.fetchone()
        engine.dispose()
        print(f"OK ({row[0]})")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_postgres(label, host, port, name, user, password):
    print(f"  [{label}] Connecting PostgreSQL {user}@{host}:{port}/{name} ...", end=" ")
    try:
        from sqlalchemy import create_engine, text
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
        engine.dispose()
        print(f"OK ({row[0]})")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def main():
    print(f"\n{'='*60}")
    print(f"  Database Connection Tests")
    print(f"  DB_TYPE = {DB_TYPE}")
    print(f"{'='*60}\n")

    results = []

    # 1. BP Batam Oracle
    print("[1/4] BP Batam (US_DWH)")
    ok = test_oracle("BP", BP_DB_USER, BP_DB_PASSWORD, BP_DB_HOST, BP_DB_SERVICE_NAME)
    results.append(("BP Batam", ok))

    print()
    print("[2/4] iBOSS (US_oss via us_si)")
    ok = test_oracle("iBOSS", IBOSS_DB_USER, IBOSS_DB_PASSWORD, IBOSS_DB_HOST, IBOSS_DB_SERVICE_NAME)
    results.append(("iBOSS", ok))

    print()
    print("[3/4] vOSS (BSWBY via us_voss)")
    ok = test_oracle("vOSS", VOSS_DB_USER, VOSS_DB_PASSWORD, VOSS_DB_HOST, VOSS_DB_SERVICE_NAME)
    results.append(("vOSS", ok))

    print()
    print("[4/4] BCARE (PostgreSQL)")
    ok = test_postgres("BCARE", BCARE_DB_HOST, BCARE_DB_PORT, BCARE_DB_NAME, BCARE_DB_USER, BCARE_DB_PASSWORD)
    results.append(("BCARE", ok))

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    all_ok = True
    for name, ok in results:
        status = "OK" if ok else "FAIL"
        all_ok = all_ok and ok
        print(f"  [{status}] {name}")
    print(f"{'='*60}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
