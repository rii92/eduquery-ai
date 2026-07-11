"""Insight Service — deterministic stats + LLM narration, constrained by templates.json."""

import json
import re
from pathlib import Path
from typing import Any, Optional

from app.core.json_util import serialize_dates
from app.intents.loader import get_intent, get_intent_rules

_TEMPLATES_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "templates.json"


def _load_templates() -> dict:
    with open(_TEMPLATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["insight_template_guide"]


class InsightService:
    def __init__(self):
        self._templates: Optional[dict] = None

    @property
    def templates(self) -> dict:
        if self._templates is None:
            self._templates = _load_templates()
        return self._templates

    # ── Fact extraction ──

    def _extract_facts(self, payload: dict, data: list[dict]) -> dict:
        facts = {}
        facts["row_count"] = len(data)

        filters = {}
        for k in ("tgl_status_terakhir", "perizinan", "kategori_status"):
            v = payload.get(k, "")
            if v:
                filters[k] = v
        facts["filters"] = filters

        numeric_cols = self._find_numeric_cols(data)
        date_col = self._find_date_col(data)

        if numeric_cols and date_col:
            col = numeric_cols[0]
            series = []
            for r in data:
                date_val = r.get(date_col)
                num_val = r.get(col)
                if date_val is not None and isinstance(num_val, (int, float)):
                    series.append({"periode": str(date_val), "value": num_val})
            facts["series"] = series
            facts["latest_period"] = str(data[-1].get(date_col, "")) if data else ""
            facts["latest_value"] = data[-1].get(col, 0) if data else 0

        if numeric_cols:
            col = numeric_cols[0]
            vals = [r[col] for r in data if isinstance(r.get(col), (int, float))]
            if vals:
                facts["numeric"] = {
                    "total": sum(vals),
                    "avg": round(sum(vals) / len(vals), 1),
                    "min": min(vals),
                    "max": max(vals),
                }
                facts["total"] = sum(vals)
                facts["avg_value"] = round(sum(vals) / len(vals), 1)
                facts["min_value"] = min(vals)
                facts["max_value"] = max(vals)

        if data and numeric_cols:
            num_col = numeric_cols[0]
            label_candidates = [k for k in data[0] if k != num_col and k != date_col]
            if label_candidates:
                label_col = label_candidates[0]
                sorted_data = sorted(data, key=lambda r: r.get(num_col, 0) or 0, reverse=True)
                rankings = []
                for i, r in enumerate(sorted_data[:10], 1):
                    rankings.append({
                        "rank": i,
                        "entity": str(r.get(label_col, "")),
                        "value": r.get(num_col, 0),
                    })
                if rankings:
                    facts["ranking"] = rankings
                    facts["top_entity"] = rankings[0]["entity"]
                    facts["top_value"] = rankings[0]["value"]
                    if len(rankings) > 1:
                        facts["bottom_entity"] = rankings[-1]["entity"]
                        facts["bottom_value"] = rankings[-1]["value"]

        if data and numeric_cols and label_candidates:
            if len(label_candidates) >= 2:
                second_label = label_candidates[1]
                grouped = {}
                for r in data:
                    key = str(r.get(label_col, ""))
                    sub = str(r.get(second_label, ""))
                    val = r.get(num_col, 0)
                    if key not in grouped:
                        grouped[key] = {}
                    grouped[key][sub] = val
                facts["grouped"] = grouped

        if data:
            for k, v in data[0].items():
                if isinstance(v, (int, float)):
                    facts[k.lower()] = v
            td = facts.get("total_dokumen", 0) or 0
            tt = facts.get("total_terbit", 0) or 0
            facts["persen_terbit"] = round(tt / td * 100, 1) if td else 0

        facts["period_count"] = len(data)
        return facts

    def _find_numeric_cols(self, data: list[dict]) -> list[str]:
        if not data:
            return []
        exclude = {"PERIODE", "PERIOD", "TANGGAL", "DATE", "periode", "tanggal"}
        exclude_upper = {x.upper() for x in exclude}
        return [k for k in data[0]
                if k.upper() not in exclude_upper
                and isinstance(data[0].get(k), (int, float))]

    def _find_date_col(self, data: list[dict]) -> Optional[str]:
        if not data:
            return None
        for k in data[0]:
            if k.upper() in ("PERIODE", "TANGGAL", "DATE", "PERIOD"):
                return k
        return None

    # ── Intent rules lookup (data-driven via intents.json) ──

    def _get_intent_rules(self, intent_id: str) -> dict:
        rules = get_intent_rules(intent_id)
        if rules:
            return rules
        rules = self.templates.get("intent_rules", {})
        return rules.get(intent_id, rules.get("_default", {}))

    # ── Deterministic insight ──

    def deterministic(self, payload: dict, data: list[dict]) -> str:
        if not data:
            return ""
        facts = self._extract_facts(payload, data)
        intent_rules = self._get_intent_rules(payload.get("intent", ""))

        patterns = intent_rules.get("insight_patterns", ["{row_count} baris hasil."])
        bullets_src = intent_rules.get("bullet_patterns", [])

        lines = []
        for pat in patterns:
            filled = self._fill_pattern(pat, facts)
            if filled:
                lines.append(filled)

        if bullets_src:
            bullets = []
            for pat in bullets_src[:4]:
                filled = self._fill_pattern(pat, facts)
                if filled:
                    bullets.append(f"- {filled}")
            if bullets:
                lines.append("")
                lines.extend(bullets)

        return "\n".join(lines) if lines else ""

    def _fill_pattern(self, pattern: str, facts: dict) -> str:
        try:
            return pattern.format(**facts)
        except KeyError:
            return ""
        except Exception:
            return ""

    # ── LLM Narration (constrained by templates.json) ──

    async def llm_narration(
        self, llm_client: Any, intent_id: str,
        question: str, data: list[dict],
        deterministic_summary: str,
    ) -> str:
        meta = get_intent(intent_id)
        intent_desc = meta["description"] if meta else intent_id
        facts = self._extract_facts({"intent": intent_id}, data)
        intent_rules = self._get_intent_rules(intent_id)
        contract = self.templates.get("output_contract", {})
        global_rules = self.templates.get("global_rules", [])

        sample = data[:5]
        data_json = json.dumps(serialize_dates(sample), indent=2, ensure_ascii=False)
        facts_json = json.dumps(facts, indent=2, ensure_ascii=False)

        facts_to_use = intent_rules.get("facts_to_use", ["row_count", "numeric"])
        facts_summary = "\n".join(f"- {k}" for k in facts_to_use)

        bullets_hint = intent_rules.get("bullet_patterns", [])
        bullets_hint_str = "\n".join(f"  - {b}" for b in bullets_hint[:3]) if bullets_hint else ""

        prompt = f"""Kamu adalah asisten analis BP Batam.

Laporan: {intent_desc}
Pertanyaan: {question}

--- ATURAN GLOBAL ---
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(global_rules))}

--- FAKTA YANG TERSEDIA ---
{facts_json}

--- OUTPUT CONTRACT ---
Keluarkan JSON object dengan properti berikut:
- "insight": string (maksimal 2 kalimat, intisari utama)
- "bullets": array of string (maksimal 6 item, detail pendukung)
- "caveats": array of string (maksimal 4 item, keterbatasan data)

Contoh output:
{{
  "insight": "Total {facts.get('total', 'N/A')} catatan pada {facts.get('period_count', 'N/A')} periode.",
  "bullets": [
    "Terakhir ({facts.get('latest_period', 'N/A')}): {facts.get('latest_value', 'N/A')}.",
    "Saran: gunakan filter tanggal untuk data lebih spesifik."
  ],
  "caveats": [
    "Data hanya mencakup BP Batam."
  ]
}}

Gunakan hanya fakta dari INPUT di atas. Jawab dalam Bahasa Indonesia. Jangan tambahkan teks di luar JSON."""

        try:
            raw = await llm_client.generate(prompt, temperature=0.3, num_predict=512)
            return self._format_llm_response(raw)
        except Exception:
            return deterministic_summary

    def _format_llm_response(self, raw: str) -> str:
        json_str = self._extract_json(raw)
        if not json_str:
            return raw
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            return raw

        lines = []
        if parsed.get("insight"):
            lines.append(parsed["insight"])
        if parsed.get("bullets"):
            for b in parsed["bullets"][:6]:
                lines.append(f"- {b}")
        if parsed.get("caveats"):
            for c in parsed["caveats"][:4]:
                lines.append(f"> \u26a0 {c}")
        return "\n".join(lines) if lines else raw

    def _extract_json(self, text: str) -> Optional[str]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else None
