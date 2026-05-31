"""Insight Service — deterministic stats + LLM narration."""

import json
from typing import Any, Optional

from app.core.json_util import serialize_dates
from app.intents.loader import get_intent


class InsightService:
    def deterministic(self, payload: dict, data: list[dict]) -> str:
        if not data:
            return ""
        numeric_cols = self._find_numeric_cols(data)
        if not numeric_cols:
            return ""
        col = numeric_cols[0]
        vals = [r[col] for r in data if isinstance(r.get(col), (int, float))]
        if not vals:
            return ""
        total = sum(vals)
        avg = round(total / len(vals), 1)
        high = max(vals)
        low = min(vals)
        period_col = self._find_date_col(data) or "periode"
        periods = len(data)
        return f"**Ringkasan Data**: {periods} periode, total {total}, rata-rata {avg}/periode, tertinggi {high}, terendah {low}."

    def _find_numeric_cols(self, data: list[dict]) -> list[str]:
        if not data:
            return []
        exclude = {"PERIODE", "PERIOD", "TANGGAL", "DATE", "PERIODE", "periode", "tanggal"}
        return [k for k in data[0] if k.upper() not in {x.upper() for x in exclude} and isinstance(data[0].get(k), (int, float))]

    def _find_date_col(self, data: list[dict]) -> Optional[str]:
        if not data:
            return None
        date_keywords = ["PERIODE", "TANGGAL", "DATE", "PERIOD", "periode", "tanggal"]
        for k in date_keywords:
            if k in data[0]:
                return k
        return None

    async def llm_narration(
        self, llm_client: Any, intent_id: str,
        question: str, data: list[dict],
        deterministic_summary: str,
    ) -> str:
        meta = get_intent(intent_id)
        intent_desc = meta["description"] if meta else intent_id

        sample = data[:5] if len(data) > 5 else data
        data_json = json.dumps(serialize_dates(sample), indent=2, ensure_ascii=False)

        prompt = f"""Kamu adalah asisten analis BP Batam.

Laporan: {intent_desc}
Pertanyaan: {question}
Total baris data: {len(data)}

Ringkasan statistik:
{deterministic_summary}

Contoh data (sample):
```json
{data_json}
```

Beri insight narasi 1-2 kalimat dalam Bahasa Indonesia. Langsung ke inti: tren, angka penting, atau rekomendasi singkat."""

        try:
            return await llm_client.generate(prompt, temperature=0.3, num_predict=512)
        except Exception:
            return ""
