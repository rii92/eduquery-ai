import json
import re
from typing import Any, Dict

from app.ai.keyword_classifier import classify_by_keyword


class IntentExtractor:
    def extract(self, question: str) -> Dict[str, Any]:
        fallback = classify_by_keyword(question)
        if fallback is not None:
            return fallback
        return {"intent": "unknown"}