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


def _fmt_flow_permohonan(payload, result):
    if not result:
        return "Data flow permohonan tidak ditemukan."
    lines = []
    for r in result[:15]:
        src = _val(r.get("SOURCE", ""))
        tgt = _val(r.get("TARGET", ""))
        val = r.get("VALUE", 0)
        lines.append(f"- {src} → {tgt}: {val}")
    if len(result) > 15:
        lines.append(f"- ... dan {len(result) - 15} aliran lainnya")
    return "**Alur Permohonan (Sankey)**:\n" + "\n".join(lines)


def _fmt_tren_inflow_outflow(payload, result):
    if not result:
        return "Data tren inflow outflow tidak ditemukan."
    lines = []
    for r in result[:10]:
        tgl = _val(r.get("TANGGAL", ""))
        inflow = r.get("INFLOW_MASUK", 0)
        outflow = r.get("OUTFLOW_TERBIT", 0)
        lines.append(f"- {tgl}: Masuk {inflow}, Terbit {outflow}")
    if len(result) > 10:
        sisa = sum(r.get("INFLOW_MASUK", 0) for r in result[10:])
        lines.append(f"- ... dan {len(result) - 10} hari lainnya ({sisa} masuk)")
    return "**Tren Inflow vs Outflow**:\n" + "\n".join(lines)


def _fmt_gauge_performa(payload, result):
    if not result:
        return "Data performa tidak ditemukan."
    r = result[0]
    skor = r.get("PERFORMA_PENYELESAIAN", 0) or 0
    pct = round(skor * 100, 2)
    return f"**Performa Penyelesaian**: {pct}%"


def _fmt_kepatuhan_sla(payload, result):
    if not result:
        return "Data kepatuhan SLA tidak ditemukan."
    r = result[0]
    skor = r.get("KEPATUHAN_SLA", 0) or 0
    pct = round(skor * 100, 2)
    return f"**Kepatuhan SLA**: {pct}%"


def _fmt_funnel_kemacetan(payload, result):
    if not result:
        return "Data funnel tidak ditemukan."
    lines = []
    for r in result:
        tahap = _val(r.get("TAHAPAN_PROSES", ""))
        jumlah = r.get("JUMLAH_DOKUMEN", 0)
        lines.append(f"- {tahap}: {jumlah}")
    return "**Analisis Kemacetan (Funnel)**:\n" + "\n".join(lines)


def _fmt_proporsi_kerja(payload, result):
    if not result:
        return "Data proporsi kerja tidak ditemukan."
    lines = []
    for r in result:
        kategori = _val(r.get("KATEGORI_WAKTU", ""))
        jumlah = r.get("JUMLAH_DOKUMEN", 0)
        lines.append(f"- {kategori}: {jumlah}")
    return "**Proporsi Kerja Staf**:\n" + "\n".join(lines)


def _fmt_rapor_staf(payload, result):
    if not result:
        return "Data rapor staf tidak ditemukan."
    lines = []
    for r in result[:5]:
        nama = _val(r.get("NAMA_STAF", ""))
        skor = r.get("SKOR_AKHIR", 0) or 0
        performa = r.get("NILAI_PERFORMA", 0) or 0
        produktivitas = r.get("NILAI_PRODUKTIVITAS", 0) or 0
        sla = r.get("NILAI_SLA", 0) or 0
        total = r.get("TOTAL_DOKUMEN_KERJA", 0) or 0
        lines.append(
            f"- {nama}: Skor {skor} "
            f"(Performa {performa}%, Produktivitas {produktivitas}%, "
            f"SLA {sla}%, Total {total} dokumen)"
        )
    return "**Rapor Staf (Top 5)**:\n" + "\n".join(lines)


_FORMATTERS = {
    "bp_all_kpi_card": _fmt_kpi_card,
    "bp_flow_permohonan": _fmt_flow_permohonan,
    "bp_tren_inflow_outflow": _fmt_tren_inflow_outflow,
    "bp_gauge_performa": _fmt_gauge_performa,
    "bp_kepatuhan_sla": _fmt_kepatuhan_sla,
    "bp_funnel_kemacetan": _fmt_funnel_kemacetan,
    "bp_proporsi_kerja": _fmt_proporsi_kerja,
    "bp_rapor_staf": _fmt_rapor_staf,
}


def format_bp_reply(payload: dict, result: list[dict]) -> str:
    intent = payload.get("intent", "")
    formatter = _FORMATTERS.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, data untuk laporan tersebut belum tersedia."
