"""LLM-based reply generator — jawaban natural + insight dari data query."""

import json
import os
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
    "bp_perizinan_scorecard": "Scorecard permohonan izin PB/PD",
    "bp_perizinan_gauge": "Gauge performa penyelesaian PB/PD",
    "bp_perizinan_komposisi": "Komposisi status permohonan PB/PD",
    "bp_perizinan_sankey": "Diagram Sankey alur PB/PD",
    "bp_perizinan_tren": "Tren inflow vs outflow PB/PD",
    "bp_perizinan_funnel": "Funnel tahapan proses PB/PD",
    "bp_perizinan_sla": "SLA per jenis izin PB/PD per bulan",
    "bp_perizinan_leaderboard_verifikator": "Leaderboard verifikator PB/PD",
    "bp_perizinan_countdown": "Countdown SLA permohonan PB/PD",
    "bp_perizinan_jam_kerja": "Proporsi kerja dalam/luar jam kerja PB/PD",
    "bp_perizinan_rapor": "Rapor evaluasi staf PB/PD",
    "bp_perizinan_detail": "Detail table permohonan izin PB/PD",
    "bp_ikel_komoditas": "Izin keluar masuk barang per komoditas",
    "bp_ikel_perusahaan": "Izin keluar masuk barang per perusahaan",
    "bp_ikel_detail": "Detail izin keluar masuk barang",
    "bp_reklame_masuk": "Total masuk reklame",
    "bp_reklame_status": "Komposisi status reklame",
    "bp_reklame_kadaluarsa": "Reklame kadaluarsa",
    "bp_reklame_tanggal_kosong": "Reklame tanpa tanggal/tanggal kosong",
    "bp_reklame_rasio": "Rasio masa berlaku reklame",
    "bp_reklame_tagihan": "Daftar tagihan perpanjangan reklame",
    "bp_reklame_detail": "Detail reklame",
    "bp_pengaduan_masuk": "Total masuk pengaduan",
    "bp_pengaduan_status": "Komposisi status pengaduan",
    "bp_pengaduan_detail": "Detail pengaduan",
    "bp_tracking": "Tracking permohonan",
    "bp_profil_usaha": "Profil usaha perizinan",
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
        return raw.strip()
    except Exception:
        return ""
