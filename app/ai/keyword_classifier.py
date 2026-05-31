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
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu? Tanyakan soal perizinan BP Batam."}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Aku siap membantu menjawab pertanyaan seputar data perizinan BP Batam."}

    # BP Batam intents
    has_izin = re.search(r"izin", q)
    has_bp = re.search(r"\bbp\b|bp[\s_]?batam|data.?warehouse", q)
    has_perizinan = re.search(r"perizinan|permohonan|backlog", q)
    has_status = re.search(r"status\s*perizinan", q)

    if has_bp or has_perizinan or has_status or has_izin:
        if re.search(r"(?:total|jumlah).*(?:masuk|masuk.*izin)", q):
            return {"intent": "bp_total_masuk"}
        if re.search(r"backlog|belum.*terbit|menunggu", q):
            return {"intent": "bp_total_backlog_per_bulan"}
        if re.search(r"izin.*terbit|terbit.*izin|jumlah.*izin.*terbit", q):
            return {"intent": "bp_izin_terbit_per_bulan"}
        if re.search(r"dalam.*proses|proses.*izin|masih.*diproses|sedang.*proses", q):
            return {"intent": "bp_dalam_proses"}
        if re.search(r"komposisi.*status|rekap.*status|status.*perizinan", q):
            return {"intent": "bp_komposisi_status"}
        if re.search(r"sebaran|jenis.*izin", q):
            return {"intent": "bp_sebaran_jenis_izin"}
        if re.search(r"izin", q):
            return {"intent": "bp_izin_terbit_per_bulan"}
        return {"intent": "bp_total_masuk"}

    return None
