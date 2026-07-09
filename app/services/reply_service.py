"""LLM-based reply generator — menghasilkan jawaban natural dari data query."""

import json
from typing import Optional

from app.llm.client import LLMClient
from app.core.json_util import serialize_dates


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

    prompt = f"""Kamu adalah asisten data warehouse BP Batam. Jawab dengan bahasa Indonesia yang natural, ringkas, dan informatif.

LAPORAN: {label}
PERTANYAAN: {question}
TOTAL BARIS DATA: {total_rows}

DATA (JSON):
{data_json}

FILTER AKTIF:
{json.dumps(filters, indent=2, ensure_ascii=False) if filters else "Tidak ada filter"}

INSTRUKSI:
1. Jawab langsung inti dari laporan tersebut dalam 2-3 kalimat pertama.
2. Sebutkan angka-angka penting dari data.
3. Jika ada filter yang aktif, sebutkan.
4. Jika hasil hanya 1 baris, deskripsikan nilai-nilai pentingnya.
5. Jika data kosong, bilang bahwa data tidak ditemukan (jangan mengarang).
6. Jangan gunakan markdown atau formatting berlebihan. Gunakan teks biasa.
7. Akhiri dengan saran singkat jika relevan.
"""

    try:
        llm = LLMClient(provider=llm_provider)
        raw = await llm.generate(prompt, temperature=0.4, max_tokens=1024, timeout=timeout)
        return raw.strip()
    except Exception:
        return ""
