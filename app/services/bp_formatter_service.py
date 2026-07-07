"""Formatter untuk hasil query BP Batam."""

from typing import Any


def _val(v: Any) -> str:
    if v is None:
        return "0"
    return str(v)


def _fmt_kpi_card(payload, result):
    if not result:
        return "Data KPI tidak ditemukan."
    r = result[0]
    total = r.get("TOTAL_DOKUMEN", 0) or 0
    terbit = r.get("TOTAL_TERBIT", 0) or 0
    tolak = r.get("TOTAL_TOLAK", 0) or 0
    proses = r.get("TOTAL_DALAM_PROSES", 0) or 0
    lainnya = r.get("TOTAL_LAINNYA", 0) or 0
    overdue = r.get("TOTAL_OVERDUE", 0) or 0
    persen_terbit = round(terbit / total * 100, 1) if total else 0

    return (
        f"**Ringkasan KPI Permohonan Izin BP Batam**\n\n"
        f"📋 **Total Dokumen**: {total}\n\n"
        f"✅ **Terbit**: {terbit} ({persen_terbit}%)\n"
        f"❌ **Ditolak**: {tolak}\n"
        f"🔄 **Dalam Proses**: {proses}\n"
        f"📌 **Lainnya**: {lainnya}\n"
        f"⚠️ **Overdue (Lewat SLA)**: {overdue}"
    )


_FORMATTERS = {
    "bp_all_kpi_card": _fmt_kpi_card,
}


def format_bp_reply(payload: dict, result: list[dict]) -> str:
    intent = payload.get("intent", "")
    formatter = _FORMATTERS.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, data untuk laporan tersebut belum tersedia."
