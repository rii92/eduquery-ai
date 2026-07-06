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


def _fmt_beban_level_staf(payload, result):
    if not result:
        return "Data beban level staf tidak ditemukan."
    total = sum(r.get("TOTAL_BEBAN", 0) for r in result)
    return f"**Total Beban Level Staf**: {total} dokumen"


def _fmt_dalam_jam_kerja(payload, result):
    if not result:
        return "Data aktivitas dalam jam kerja tidak ditemukan."
    total = sum(r.get("JUMLAH", 0) for r in result)
    return f"**Aktivitas Dalam Jam Kerja**: {total} aktivitas"


def _fmt_luar_jam_kerja(payload, result):
    if not result:
        return "Data aktivitas luar jam kerja tidak ditemukan."
    total = sum(r.get("JUMLAH", 0) for r in result)
    return f"**Aktivitas Luar Jam Kerja**: {total} aktivitas"


def _fmt_beban_dokumen_per_staf(payload, result):
    if not result:
        return "Data beban dokumen per staf tidak ditemukan."
    lines = []
    for r in result[:10]:
        nama = _val(r.get("NAMA_STAF", ""))
        total = r.get("TOTAL_DOKUMEN", 0)
        selesai = r.get("SELESAI", 0)
        ditolak = r.get("DITOLAK", 0)
        proses = r.get("DALAM_PROSES", 0)
        lines.append(f"- {nama}: {total} dokumen (Selesai: {selesai}, Ditolak: {ditolak}, Proses: {proses})")
    if len(result) > 10:
        lines.append(f"- ... dan {len(result) - 10} staf lainnya")
    return "**Beban Dokumen per Staf**:\n" + "\n".join(lines)


def _fmt_komposisi_waktu_kerja(payload, result):
    if not result:
        return "Data komposisi waktu kerja tidak ditemukan."
    lines = []
    for r in result:
        kategori = _val(r.get("KATEGORI_WAKTU", ""))
        jumlah = r.get("JUMLAH", 0)
        lines.append(f"- {kategori}: {jumlah}")
    return "**Komposisi Waktu Kerja Staf**:\n" + "\n".join(lines)


def _fmt_rapor_evaluasi_staf(payload, result):
    if not result:
        return "Data rapor evaluasi staf tidak ditemukan."
    lines = []
    for r in result[:10]:
        nama = _val(r.get("NAMA_STAF", ""))
        total = r.get("TOTAL_DOKUMEN", 0)
        selesai = r.get("SELESAI", 0)
        persen = r.get("PERSEN_SELESAI", 0)
        analisis = _val(r.get("ANALISIS_BEBAN", ""))
        lines.append(f"- {nama}: {total} dokumen, {selesai} selesai ({persen}%), {analisis}")
    if len(result) > 10:
        lines.append(f"- ... dan {len(result) - 10} staf lainnya")
    return "**Rapor Evaluasi Level Staf**:\n" + "\n".join(lines)


def _fmt_total_masuk_reklame(payload, result):
    if not result:
        return "Data total masuk reklame tidak ditemukan."
    total = sum(r.get("JUMLAH", 0) for r in result)
    return f"**Total Masuk Reklame**: {total} permohonan"


def _fmt_kadaluarsa_reklame(payload, result):
    if not result:
        return "Data reklame kadaluarsa tidak ditemukan."
    total = sum(r.get("JUMLAH", 0) for r in result)
    return f"**Reklame Kadaluarsa**: {total}"


def _fmt_tanggal_kosong_reklame(payload, result):
    if not result:
        return "Data reklame tanggal kosong tidak ditemukan."
    total = sum(r.get("JUMLAH", 0) for r in result)
    return f"**Reklame Tanggal Kosong**: {total}"


def _fmt_rasio_masa_berlaku_reklame(payload, result):
    if not result:
        return "Data rasio masa berlaku reklame tidak ditemukan."
    lines = []
    for r in result:
        kategori = _val(r.get("KATEGORI", ""))
        jumlah = r.get("JUMLAH", 0)
        lines.append(f"- {kategori}: {jumlah}")
    return "**Rasio Masa Berlaku Reklame**:\n" + "\n".join(lines)


def _fmt_daftar_tagihan_perpanjangan(payload, result):
    if not result:
        return "Data tagihan perpanjangan tidak ditemukan."
    lines = []
    for r in result[:10]:
        nama = _val(r.get("NAMA_PERUSAHAAN", ""))
        no_sk = _val(r.get("NOMOR_SK_REKLAME", ""))
        tgl = _val(r.get("TANGGAL_BERAKHIR", ""))
        status = _val(r.get("STATUS", ""))
        sisa = r.get("SISA_HARI_BERLAKU", "")
        lines.append(f"- {nama} ({no_sk}) — Berakhir: {tgl}, Status: {status}, Sisa: {sisa} hari")
    if len(result) > 10:
        lines.append(f"- ... dan {len(result) - 10} tagihan lainnya")
    return "**Daftar Tagihan Perpanjangan (Prioritas)**:\n" + "\n".join(lines)


_FORMATTERS = {
    "bp_total_masuk": _fmt_total_masuk,
    "bp_izin_terbit_per_bulan": _fmt_izin_terbit,
    "bp_total_backlog_per_bulan": _fmt_backlog,
    "bp_dalam_proses": _fmt_dalam_proses,
    "bp_sebaran_jenis_izin": _fmt_sebaran,
    "bp_komposisi_status": _fmt_komposisi,
    "bp_beban_level_staf": _fmt_beban_level_staf,
    "bp_dalam_jam_kerja": _fmt_dalam_jam_kerja,
    "bp_luar_jam_kerja": _fmt_luar_jam_kerja,
    "bp_beban_dokumen_per_staf": _fmt_beban_dokumen_per_staf,
    "bp_komposisi_waktu_kerja": _fmt_komposisi_waktu_kerja,
    "bp_rapor_evaluasi_staf": _fmt_rapor_evaluasi_staf,
    "bp_total_masuk_reklame": _fmt_total_masuk_reklame,
    "bp_kadaluarsa_reklame": _fmt_kadaluarsa_reklame,
    "bp_tanggal_kosong_reklame": _fmt_tanggal_kosong_reklame,
    "bp_rasio_masa_berlaku_reklame": _fmt_rasio_masa_berlaku_reklame,
    "bp_daftar_tagihan_perpanjangan": _fmt_daftar_tagihan_perpanjangan,
}


def format_bp_reply(payload: dict, result: list[dict]) -> str:
    intent = payload.get("intent", "")
    formatter = _FORMATTERS.get(intent)
    if formatter:
        return formatter(payload, result)
    return "Maaf, data untuk laporan tersebut belum tersedia."
