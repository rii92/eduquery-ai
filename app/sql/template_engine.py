from typing import Any, Dict, Optional
import re
from app.intents.loader import get_intent


def _resolve_template(intent: str) -> Optional[str]:
    item = get_intent(intent)
    if item and item.get("active"):
        return item.get("sql_template")
    return None


def _remove_empty_in(sql: str) -> str:
    """Remove entire lines that contain IN ('') (empty filter).

    AND g.academic_year IN ('')  →  (removed)
    """
    return re.sub(r"^\s+AND\s+\S+\s+IN\s*\(\s*''\s*\).*\n?", "", sql, flags=re.MULTILINE)


class SQLTemplateEngine:
    def generate(self, payload: Dict[str, Any]) -> str:
        intent = payload.get("intent")
        if not intent:
            return ""
        template = _resolve_template(intent)
        if not template:
            return ""
        result = template
        for key, value in payload.items():
            if key == "intent":
                continue
            result = result.replace(f"{{{key}}}", str(value))
        result = re.sub(r"'\{(\w+)\}'", "''", result)
        result = re.sub(r"\{(\w+)\}", "", result)
        result = _remove_empty_in(result)
        return result
