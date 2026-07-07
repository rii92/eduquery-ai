from typing import Dict, Any, Optional
import re


_BLACKLIST = [
    r"\b(drop|delete|truncate|alter|insert|update|create|exec|execute|shutdown)\b",
]


def is_blacklisted(question: str) -> bool:
    q = question.lower()
    for pat in _BLACKLIST:
        if re.search(pat, q):
            return True
    return False


def classify_by_keyword(question: str) -> Optional[Dict[str, Any]]:
    q = question.lower().strip()

    # Greetings
    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu?"}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Asisten data warehouse BP Batam."}

    # ── KPI Card — satu-satunya intent ──
    has_bp = re.search(r"\bbp\b|bp[\s_]?batam|data.?warehouse", q)
    has_izin = re.search(r"izin|perizinan|permohonan", q)
    has_total = re.search(r"total|jumlah|ringkasan|kpi|rekap|dashboard", q)

    if has_bp or has_izin or has_total:
        return {"intent": "bp_all_kpi_card"}

    return {"intent": "bp_all_kpi_card"}
