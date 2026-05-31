"""Semantic intent classifier via sentence-transformers embeddings."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL

_INTENTS_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "intents.json"

_model: Optional[SentenceTransformer] = None
_intent_embeddings: Optional[np.ndarray] = None
_intent_ids: list[str] = []


def _load_intents() -> list[Dict[str, Any]]:
    with open(_INTENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_embeddings() -> tuple[np.ndarray, list[str]]:
    global _intent_embeddings, _intent_ids
    if _intent_embeddings is None:
        intents = _load_intents()
        _intent_ids = [i["id"] for i in intents if i.get("active", True)]
        texts = [f"{i['description']}. Contoh: {' '.join(i.get('examples', []))}" for i in intents if i.get("active", True)]
        model = _get_model()
        _intent_embeddings = model.encode(texts, normalize_embeddings=True)
    return _intent_embeddings, _intent_ids


def classify_by_embedding(question: str, threshold: float = 0.45) -> Optional[Dict[str, Any]]:
    model = _get_model()
    q_emb = model.encode([question], normalize_embeddings=True)[0]
    intent_embs, intent_ids = _get_embeddings()

    scores = np.dot(intent_embs, q_emb)
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    if best_score >= threshold:
        return {"intent": intent_ids[best_idx], "score": round(best_score, 3)}
    return None
