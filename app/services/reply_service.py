"""LLM-based reply generator — jawaban natural + insight dari data query."""

import json
import logging
import os
from typing import Optional

from app.llm.client import LLMClient
from app.core.json_util import serialize_dates

logger = logging.getLogger("reply_service")


_INTENT_LABELS = {
    "bp_all_kpi_card": "Ringkasan KPI seluruh permohonan izin",
    "bp_flow_permohonan": "Diagram alur/Sankey permohonan izin",
    "bp_tren_inflow_outflow": "Tren inflow (masuk) vs outflow (terbit) per hari",
    "bp_gauge_performa": "Gauge performa penyelesaian permohonan",
    "bp_kepatuhan_sla": "Kepatuhan SLA permohonan izin",
    "bp_funnel_kemacetan": "Analisis kemacetan/funnel per tahapan proses",
    "bp_proporsi_kerja": "Proporsi kerja staf dalam vs luar jam kerja",
    "bp_rapor_staf": "Rapor evaluasi staf (skor akhir, performa, produktivitas, SLA)",
}

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")

_INSIGHT_TEMPLATES: dict = {}
_templates_path = os.path.join(_TEMPLATES_DIR, "insight_templates.json")
if os.path.exists(_templates_path):
    with open(_templates_path, encoding="utf-8") as f:
        _INSIGHT_TEMPLATES = json.load(f)


def _extract_columns(result: list[dict]) -> str:
    seen = set()
    parts = []
    for row in result[:3]:
        for k, v in row.items():
            if k not in seen:
                seen.add(k)
                parts.append(f"{k} = {v}")
    return "\n".join(parts)


async def generate_llm_reply(
    question: str,
    intent: str,
    result: list[dict],
    payload: dict,
    llm_provider: str = "llamacpp",
    timeout: int = 120,
) -> str:
    label = _INTENT_LABELS.get(intent, intent)
    data_json = json.dumps(serialize_dates(result[:20]), indent=2, ensure_ascii=False)
    total_rows = len(result)

    filters = {k: v for k, v in payload.items() if v and k not in ("intent", "_reply")}
    column_values = _extract_columns(result)

    domain = _INSIGHT_TEMPLATES.get(intent, {})
    template_insight = domain.get("insight", "")
    template_rekomendasi = domain.get("rekomendasi", "")

    prompt = f"""Kamu adalah analis data BP Batam yang sedang menjelaskan temuan kepada rekan kerja. Jawab dengan bahasa natural, mengalir, dan penuh insight — seperti ngobrol santai tapi berbasis data.

JUDUL LAPORAN: {label}
PERTANYAAN: {question}
JUMLAH BARIS: {total_rows}

DATA (JSON):
{data_json}

NILAI KOLOM:
{column_values}

FILTER:
{json.dumps(filters, indent=2, ensure_ascii=False) if filters else "Tidak ada"}

CONTOH GAYA INSIGHT (sesuaikan dengan data asli):
{template_insight}

CONTOH GAYA REKOMENDASI:
{template_rekomendasi}

PANDUAN:
- Buka dengan angka utama atau temuan paling menarik.
- Jelaskan proporsi, tren, atau pola yang terlihat — apa arti angka-angka ini?
- Jika ada data SLA/overdue, beri konteks dampaknya.
- Jika data staf, soroti yang menonjol (positif/negatif).
- Akhiri dengan 1 rekomendasi praktis yang bisa langsung ditindaklanjuti.
- Gunakan bahasa Indonesia natural, seperti seorang analis senior bicara. Jangan kaku.
- JANGAN markdown, JANGAN emoji, JANGAN bullet.
- JANGAN mengarang angka — jika data kosong, bilang saja.
"""

    try:
        llm = LLMClient(provider=llm_provider)
        raw = await llm.generate(prompt, temperature=0.4, max_tokens=2048, timeout=timeout)
        stripped = raw.strip()
        logger.info("generate_llm_reply OK — %d chars, provider=%s", len(stripped), llm_provider)
        return stripped
    except Exception as e:
        logger.error("generate_llm_reply GAGAL — provider=%s, error=%s", llm_provider, e)
        return ""
