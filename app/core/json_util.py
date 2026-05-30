"""Custom JSON encoder untuk menangani datetime dari Oracle."""

import json
from datetime import date, datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def serialize_dates(obj: Any) -> Any:
    """Convert datetime/date objects to ISO strings recursively."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_dates(v) for v in obj]
    return obj
