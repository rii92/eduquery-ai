"""Formatter untuk hasil query BP Batam."""

from typing import Any


def _val(v: Any) -> str:
    if v is None:
        return "Tanpa Tanggal"
    return str(v)


def _period_lines(result: list[dict], key: str, label: str, max_lines: int = 10) -> list[str]:
    lines = []
    for r in result[:max_lines]:
        p = _val(r.get("PERIODE", ""))
        v = r.get(key, 0)
        lines.append(f"- {p}: {v} {label}")
    if len(result) > max_lines:
        extra = sum(r.get(key, 0) for r in result[max_lines:])
        lines.append(f"- ... dan {len(result) - max_lines} periode lainnya ({extra} {label})")
    return lines


def _fmt_total_masuk(payload, result):
    if not result:
        return "Data total masuk tidak ditemukan."
    total = sum(r.get("TOTAL_MASUK", 0) for r in result)
    lines = _period_lines(result, "TOTAL_MASUK", "masuk")
    return f"**Total Masuk**: {total} permohonan\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_izin_terbit(payload, result):
    if not result:
        return "Data izin terbit tidak ditemukan."
    total = sum(r.get("IZIN_TERBIT", 0) for r in result)
    lines = _period_lines(result, "IZIN_TERBIT", "izin")
    return f"**Izin Terbit**: {total} izin\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_backlog(payload, result):
    if not result:
        return "Data backlog tidak ditemukan."
    total = sum(r.get("TOTAL_BACKLOG", 0) for r in result)
    lines = _period_lines(result, "TOTAL_BACKLOG", "backlog")
    return f"**Total Backlog**: {total} permohonan\n\nRincian per minggu:\n" + "\n".join(lines)


def _fmt_dalam_proses(payload, result):
    if not result:
        return "Tidak ada permohonan dalam proses."
    total = sum(r.get("JUMLAH_PERMOHONAN", 0) for r in result)
    lines = _period_lines(result, "JUMLAH_PERMOHONAN", "proses")
    return f"**Dalam Proses**: {total} permohonan\n\nRincian per hari:\n" + "\n".join(lines)


def _fmt_sebaran(payload, result):
    if not result:
        return "Data sebaran izin tidak ditemukan."
    lines = []
    for r in result[:10]:
        jenis = _val(r.get("JENIS_IZIN", ""))
        status = _val(r.get("KELOMPOK_STATUS", ""))
        jumlah = r.get("JUMLAH", 0)
        lines.append(f"- {jenis} — {status}: {jumlah}")
    if len(result) > 10:
        lines.append(f"- ... dan {len(result) - 10} kombinasi lainnya")
    return "**Sebaran Berdasarkan Jenis Izin**:\n" + "\n".join(lines)


def _fmt_komposisi(payload, result):
    if not result:
        return "Data komposisi status tidak ditemukan."
    groups = {}
    for r in result:
        periode = _val(r.get("PERIODE", ""))
        status = r.get("KELOMPOK_STATUS", "")
        jumlah = r.get("JUMLAH", 0)
        if periode not in groups:
            groups[periode] = {}
        groups[periode][status] = groups[periode].get(status, 0) + jumlah
    lines = []
    for periode, statuses in list(groups.items())[:10]:
        parts = [f"{s}: {j}" for s, j in statuses.items()]
        lines.append(f"- {periode}: {', '.join(parts)}")
    if len(groups) > 10:
        lines.append(f"- ... dan {len(groups) - 10} periode lainnya")
    return "**Komposisi Keseluruhan Status**:\n" + "\n".join(lines)


_FORMATTERS = {
    "bp_total_masuk": _fmt_total_masuk,
    "bp_izin_terbit_per_bulan": _fmt_izin_terbit,
    "bp_total_backlog_per_bulan": _fmt_backlog,
    "bp_dalam_proses": _fmt_dalam_proses,
    "bp_sebaran_jenis_izin": _fmt_sebaran,
    "bp_komposisi_status": _fmt_komposisi,
}


def format_bp_reply(payload: dict, result: list[dict]) -> str:
    intent = payload.get("intent", "")
    formatter = _FORMATTERS.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, data untuk laporan tersebut belum tersedia."
