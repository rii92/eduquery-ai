import re

class SQLValidator:
    ALLOWED_TABLES = [
        "bi_t_all",
        "bi_h_all",
    ]
    FORBIDDEN = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]

    def validate(self, sql: str) -> bool:
        s = sql.strip().lower()
        if not s:
            return False
        if not s.startswith("select") and not s.startswith("with"):
            return False
        for kw in self.FORBIDDEN:
            if kw.lower() in s:
                return False
        tables = re.findall(r"(?:from|join)\s+(\w+(?:\.\w+)?)", sql, re.I)
        tables = [t for t in tables if t.lower() not in self._cte_aliases(sql)]
        return all(self._normalize(t) in self.ALLOWED_TABLES for t in tables)

    def _normalize(self, name: str) -> str:
        return name.split(".")[-1].lower()

    def _cte_aliases(self, sql: str) -> set:
        aliases = set()
        for m in re.finditer(r"\bwith\s+(\w+)\s+as\s*\(", sql, re.I):
            aliases.add(m.group(1).lower())
        for m in re.finditer(r",\s*(\w+)\s+as\s*\(", sql, re.I):
            aliases.add(m.group(1).lower())
        return aliases