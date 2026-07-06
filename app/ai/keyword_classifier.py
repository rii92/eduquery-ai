from typing import Dict, Any, Optional
import re


_BLACKLIST = [
    r"\b(drop|delete|truncate|alter|insert|update|create|exec|execute|shutdown)\b",
]


def is_blacklisted(question: str) -> bool:
    q = question.lower()
    for pat in _BLACKLIST:
        if re.search(pat, q):
            return True
    return False


def classify_by_keyword(question: str) -> Optional[Dict[str, Any]]:
    q = question.lower().strip()

    # Greetings
    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu? Tanyakan soal perizinan BP Batam."}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Aku siap membantu menjawab pertanyaan seputar data perizinan BP Batam."}

    # ── DMT1 intents (chart/dashboard — total tunggal, tanpa GROUP BY) ──
    has_dmt = re.search(r"ringkasan|dashboard|chart|dmt", q)
    has_total = re.search(r"total|jumlah", q)
    has_stat = re.search(r"sebaran|komposisi|rekap", q)
    has_izin = re.search(r"izin", q)
    has_bp = re.search(r"\bbp\b|bp[\s_]?batam|data.?warehouse", q)
    has_perizinan = re.search(r"perizinan|permohonan|backlog", q)
    has_status = re.search(r"status\s*perizinan", q)

    dmt_trigger = has_dmt or (has_total and (has_izin or has_perizinan or has_bp)) or has_stat

    if dmt_trigger:
        if re.search(r"masuk|masuk.*izin", q):
            pass  # fall through ke BP — "total masuk" sesuai bp_total_masuk
        elif re.search(r"terbit", q):
            return {"intent": "DMT1_total_terbit"}
        elif re.search(r"tolak|ditolak|reject", q):
            return {"intent": "DMT1_total_tolak"}
        elif re.search(r"pelaku.?usaha|draft|menunggu.*pemohon|waiting.*user", q):
            return {"intent": "DMT1_total_proses_pelaku_usaha"}
        elif re.search(r"dalam.*proses|proses.*internal|sedang.*diproses", q):
            return {"intent": "DMT1_total_dalam_proses"}
        elif re.search(r"komposisi|rekap|kelompok.?status", q):
            return {"intent": "DMT1_komposisi_keseluruhan_izin"}
        elif re.search(r"sebaran|jenis.*izin|per.*jenis|by.*status", q):
            return {"intent": "DMT1_row_izin_by_status"}
        else:
            return {"intent": "DMT1_total_izin"}

    # ── BP Batam: Monitoring Staf / Verifikator ──
    has_staf = re.search(r"staf|verifikator|petugas|staff|beban.*kerja|kinerja", q)
    has_jam_kerja = re.search(r"jam.?kerja|kerja.*staf|waktu.*kerja|luar.*jam", q)
    has_evaluasi = re.search(r"evaluasi|rapor|raport|penilaian", q)
    has_dokumen = re.search(r"dokumen.*staf|beban.*dokumen|dokumen.*verifikator", q)

    if has_bp and (has_staf or has_evaluasi or has_dokumen or has_jam_kerja):
        if re.search(r"evaluasi|rapor|raport|penilaian.*staf|kinerja.*verifikator", q):
            return {"intent": "bp_rapor_evaluasi_staf"}
        if re.search(r"beban.*level|level.*staf|beban.*verifikator|total.*beban.*staf", q):
            return {"intent": "bp_beban_level_staf"}
        if re.search(r"dokumen.*staf|beban.*dokumen|dokumen.*per.*staf|dokumen.*verifikator", q):
            return {"intent": "bp_beban_dokumen_per_staf"}
        if re.search(r"dalam.*jam.*kerja|jam.*kerja", q):
            return {"intent": "bp_dalam_jam_kerja"}
        if re.search(r"luar.*jam.*kerja|di.*luar.*jam", q):
            return {"intent": "bp_luar_jam_kerja"}
        if re.search(r"komposisi.*waktu|waktu.*kerja|dalam.*luar.*jam", q):
            return {"intent": "bp_komposisi_waktu_kerja"}
        return {"intent": "bp_beban_level_staf"}

    # ── BP Batam: Reklame ──
    has_reklame = re.search(r"reklame|bsw|billboard|tagihan.*perpanjangan|masa.?berlaku", q)
    if has_bp and has_reklame:
        if re.search(r"tagihan.*perpanjangan|perpanjangan.*prioritas|segera.*habis", q):
            return {"intent": "bp_daftar_tagihan_perpanjangan"}
        if re.search(r"rasio.*masa.*berlaku|masa.*berlaku.*reklame|status.*masa.*berlaku", q):
            return {"intent": "bp_rasio_masa_berlaku_reklame"}
        if re.search(r"kadaluarsa|kedaluwarsa|kadaluwarsa.*reklame|reklame.*kadaluarsa", q):
            return {"intent": "bp_kadaluarsa_reklame"}
        if re.search(r"tanggal.*kosong|kosong.*reklame", q):
            return {"intent": "bp_tanggal_kosong_reklame"}
        if re.search(r"masuk.*reklame|total.*reklame|permohonan.*reklame", q):
            return {"intent": "bp_total_masuk_reklame"}
        return {"intent": "bp_total_masuk_reklame"}

    # ── BP Batam intents (time-series / eksekutif) ──
    if has_bp or has_perizinan or has_status or has_izin:
        if re.search(r"(?:total|jumlah).*(?:masuk|masuk.*izin)", q):
            return {"intent": "bp_total_masuk"}
        if re.search(r"backlog|belum.*terbit|menunggu", q):
            return {"intent": "bp_total_backlog_per_bulan"}
        if re.search(r"izin.*terbit|terbit.*izin|jumlah.*izin.*terbit", q):
            return {"intent": "bp_izin_terbit_per_bulan"}
        if re.search(r"dalam.*proses|proses.*izin|masih.*diproses|sedang.*proses", q):
            return {"intent": "bp_dalam_proses"}
        if re.search(r"komposisi.*status|rekap.*status|status.*perizinan", q):
            return {"intent": "bp_komposisi_status"}
        if re.search(r"sebaran|jenis.*izin", q):
            return {"intent": "bp_sebaran_jenis_izin"}
        if re.search(r"izin", q):
            return {"intent": "bp_izin_terbit_per_bulan"}
        return {"intent": "bp_total_masuk"}

    return None
