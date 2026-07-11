"""Custom JSON encoder untuk menangani datetime dari Oracle."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def serialize_dates(obj: Any) -> Any:
    """Convert datetime/date/Decimal objects to JSON-serializable types recursively."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_dates(v) for v in obj]
    return obj
