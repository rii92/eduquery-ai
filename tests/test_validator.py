"""Unit tests for SQL validator."""
from app.sql.validator import SQLValidator


def test_valid_select():
    val = SQLValidator()
    assert val.validate("SELECT * FROM US_DWH.BI_MART_STATUS_PERIZINAN;") is True


def test_forbidden_keywords():
    val = SQLValidator()
    for kw in ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER"]:
        assert val.validate(f"{kw} FROM US_DWH.BI_MART_STATUS_PERIZINAN;") is False


def test_invalid_table():
    val = SQLValidator()
    assert val.validate("SELECT * FROM secret_table;") is False