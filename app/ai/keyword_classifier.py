from typing import Dict, Any, Optional
import re

from app.intents.loader import find_intent_by_keywords


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

    # Explicit non-query / test words
    if re.search(r"^(test|tes|coba|testing|hello?|awali|mulai)$", q.strip(".!? ")):
        return None

    # Greetings (system-level, not from intents.json)
    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(siapa)\s+(kamu|lu|kau|anda|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu?"}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu|nama\s*anda)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Asisten data warehouse BP Batam."}

    # Dynamic intent matching from intents.json
    result = find_intent_by_keywords(q)
    if result:
        return result

    return None
