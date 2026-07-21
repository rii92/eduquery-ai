from typing import Dict, Any, Optional
import re

from app.intents.loader import find_intent_by_keywords


_BLACKLIST = [
    r"\b(drop|delete|truncate|alter|insert|update|create|exec|execute|shutdown)\b",
]

_FOLLOWUP_WORDS = [
    r"^iya$", r"^ya$", r"^y$", r"^ya\b",
    r"^tentu$", r"^tentu\b",
    r"^lanjut$",
    r"^boleh$", r"^bisa$", r"^silakan$", r"^silahkan$",
    r"^ok$", r"^oke$", r"^okee?$", r"^ok\.?$",
    r"^siap$", r"^baik$", r"^setuju$", r"^iya dong$",
    r"^tidak$", r"^nggak$", r"^gak$", r"^ga$", r"^enggak$",
    r"^ga usah$", r"^tidak usah$",
    r"^kagak$", r"^ndak$",
]


def is_blacklisted(question: str) -> bool:
    q = question.lower()
    for pat in _BLACKLIST:
        if re.search(pat, q):
            return True
    return False


def is_followup(question: str) -> bool:
    """Check if question is a short follow-up word (iya/tidak/lanjut/etc)."""
    q = question.lower().strip().strip(".!? ")
    for pat in _FOLLOWUP_WORDS:
        if re.search(pat, q):
            return True
    return False


def needs_context(question: str) -> bool:
    """Check if question likely needs conversation context — short or contains follow-up indicators.

    Returns True if message is short (< 8 words) or contains indicator words
    like 'rekomendasi', 'selanjutnya', 'detail', 'terus', 'lalu', etc.
    This is used as a secondary check when is_followup() returns False
    but the question might still be a continuation.
    """
    q = question.lower().strip().strip(".!? ")
    words = q.split()

    # Very short messages with no intent match are almost certainly follow-ups
    if len(words) < 4:
        return True

    # Check for continuation/recommendation indicator words
    indicators = [
        r"\brekomendasi\b", r"\b(saran|masukan|usul)\b",
        r"\bselanjutnya\b", r"\bberikutnya\b", r"\blanjut\w*\b",
        r"\bdetail\b", r"\bdetil\b", r"\brinci\b", r"\brincian\b",
        r"\bterus\b", r"\blalu\b", r"\bkemudian\b",
        r"\blebih\b", r"\btambah\b", r"\blagi\b",
        r"\bjelas\w*\b", r"\bterang\w*\b",
        r"\bseperti\b", r"\bcontoh\b",
        r"\blain\b", r"\blainnya\b",
        r"\bperbandingan\b", r"\bbanding\b",
        r"\bgrafik\b", r"\bchart\b", r"\bdiagram\b",
        r"\btabel\b", r"\btampilkan\b",
    ]
    for pat in indicators:
        if re.search(pat, q):
            return True

    return False


def is_affirmative(question: str) -> bool:
    """Check if follow-up is affirmative (iya/ya/lanjut) vs negative (tidak/nggak)."""
    q = question.lower().strip().strip(".!? ")
    neg = [r"^tidak", r"^nggak", r"^gak$", r"^ga$", r"^enggak", r"^kagak", r"^ndak", r"^ga usah", r"^tidak usah"]
    for pat in neg:
        if re.search(pat, q):
            return False
    return True


def classify_by_keyword(question: str) -> Optional[Dict[str, Any]]:
    q = question.lower().strip()

    # Explicit non-query / test words
    if re.search(r"^(test|tes|coba|testing|hello?|awali|mulai)$", q.strip(".!? ")):
        return None

    # Greetings (system-level, not from intents.json)
    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>BP Batam Ai</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(siapa)\s+(kamu|lu|kau|anda|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>BP Batam Ai</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu?"}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu|nama\s*anda)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>BP Batam Ai</b>! Asisten data warehouse BP Batam."}

    # Dynamic intent matching from intents.json
    result = find_intent_by_keywords(q)
    if result:
        return result

    return None
