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

    # ── Explicit non-query / test words → bail out (biar embedding/LLM yg handle) ──
    if re.search(r"^(test|tes|coba|testing|hello?|awali|mulai)$", q.strip(".!? ")):
        return None

    # Greetings (dual order: "kamu siapa" dan "siapa kamu")
    if re.search(r"\b(kamu|lu|kau|anda)\s*(siapa|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(siapa)\s+(kamu|lu|kau|anda|ini)\b", q):
        return {"intent": "_greeting", "_reply": "Aku adalah <b>EduQuery AI</b>, asisten data warehouse BP Batam."}
    if re.search(r"\b(halo|hai|hey|hi|selamat\s+\w+)\b", q):
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu?"}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu|nama\s*anda)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Asisten data warehouse BP Batam."}

    # ── KPI Card ──
    if re.search(r"kpi|ringkasan.*permohonan|seluruh.*izin", q):
        return {"intent": "bp_all_kpi_card"}

    # ── Flow / Sankey ──
    if re.search(r"flow|sankey|alur.*permohonan|alur.*izin", q):
        return {"intent": "bp_flow_permohonan"}

    # ── Tren Inflow vs Outflow ──
    if re.search(r"tren.*inflow|tren.*outflow|inflow.*outflow|masuk.*terbit.*hari|perbandingan.*masuk.*terbit|perbandingan.*inflow.*outflow|total.*terbit.*hari|terbit.*hari\s*ini|masuk.*dan.*terbit", q):
        return {"intent": "bp_tren_inflow_outflow"}

    # ── Gauge Performa ──
    if re.search(r"gauge|performa.*penyelesaian|tingkat.*penyelesaian", q):
        return {"intent": "bp_gauge_performa"}

    # ── Kepatuhan SLA ──
    if re.search(r"sla|kepatuhan.*sla|ketepatan.*sla", q):
        return {"intent": "bp_kepatuhan_sla"}

    # ── Funnel / Kemacetan ──
    if re.search(r"funnel|kemacetan|bottleneck|tahapan.*proses|analisis.*macet", q):
        return {"intent": "bp_funnel_kemacetan"}

    # ── Proporsi Kerja ──
    if re.search(r"proporsi.*kerja|jam.*kerja|waktu.*kerja|dalam.*luar.*jam", q):
        return {"intent": "bp_proporsi_kerja"}

    # ── Rapor Staf ──
    if re.search(r"rapor.*staf|evaluasi.*staf|kinerja.*verifikator|skor.*staf|nilai.*staf", q):
        return {"intent": "bp_rapor_staf"}

    # ── Perizinan PB/PD Scorecard ──
    if re.search(r"(pb|pd).*(scorecard|ringkasan|total)|perizinan.*(pb|pd)|ringkasan.*pb|ringkasan.*pd", q):
        return {"intent": "bp_perizinan_scorecard"}

    # ── Perizinan PB/PD Gauge ──
    if re.search(r"(pb|pd).*(gauge|performa)|performa.*(pb|pd)", q):
        return {"intent": "bp_perizinan_gauge"}

    # ── Perizinan PB/PD Komposisi Status ──
    if re.search(r"(pb|pd).*(komposisi|sebaran|stacked)|komposisi.*(pb|pd)", q):
        return {"intent": "bp_perizinan_komposisi"}

    # ── Perizinan PB/PD Sankey ──
    if re.search(r"(pb|pd).*(sankey|flow|alur)|alur.*(pb|pd)", q):
        return {"intent": "bp_perizinan_sankey"}

    # ── Perizinan PB/PD Tren ──
    if re.search(r"(pb|pd).*(tren|inflow|outflow)|tren.*(pb|pd)", q):
        return {"intent": "bp_perizinan_tren"}

    # ── Perizinan PB/PD Funnel ──
    if re.search(r"(pb|pd).*(funnel|kemacetan|bottleneck|tahapan)|funnel.*(pb|pd)", q):
        return {"intent": "bp_perizinan_funnel"}

    # ── Perizinan PB/PD SLA ──
    if re.search(r"(pb|pd).*(sla|kepatuhan)|sla.*(pb|pd)", q):
        return {"intent": "bp_perizinan_sla"}

    # ── Perizinan PB/PD Leaderboard Verifikator ──
    if re.search(r"(pb|pd).*(leaderboard|verifikator|beban.*staf)|verifikator.*(pb|pd)", q):
        return {"intent": "bp_perizinan_leaderboard_verifikator"}

    # ── Perizinan PB/PD Countdown SLA ──
    if re.search(r"(pb|pd).*(countdown|deadline|mendekati.*sla)", q):
        return {"intent": "bp_perizinan_countdown"}

    # ── Perizinan PB/PD Jam Kerja ──
    if re.search(r"(pb|pd).*(jam.*kerja|waktu.*kerja)|jam.*kerja.*(pb|pd)", q):
        return {"intent": "bp_perizinan_jam_kerja"}

    # ── Perizinan PB/PD Rapor Staf ──
    if re.search(r"(pb|pd).*(rapor|evaluasi.*staf|kinerja.*staf)", q):
        return {"intent": "bp_perizinan_rapor"}

    # ── Perizinan PB/PD Detail ──
    if re.search(r"(pb|pd).*(detail|tabel.*permohonan|rincian)", q):
        return {"intent": "bp_perizinan_detail"}

    # ── Izin Keluar Masuk Barang ──
    if re.search(r"keluar.*masuk.*barang|ikel|komoditas.*barang|barang.*komoditas", q):
        return {"intent": "bp_ikel_komoditas"}
    if re.search(r"perusahaan.*(ikel|keluar.*masuk|barang)", q):
        return {"intent": "bp_ikel_perusahaan"}
    if re.search(r"detail.*(ikel|keluar.*masuk)|tabel.*(ikel|barang)", q):
        return {"intent": "bp_ikel_detail"}

    # ── Reklame ──
    if re.search(r"reklame.*(masuk|total|rekap)", q):
        return {"intent": "bp_reklame_masuk"}
    if re.search(r"reklame.*(status|komposisi)", q):
        return {"intent": "bp_reklame_status"}
    if re.search(r"reklame.*(kadaluarsa|kadaluwarsa|lewat.*masa|expired)", q):
        return {"intent": "bp_reklame_kadaluarsa"}
    if re.search(r"reklame.*(tanpa.*tanggal|tanggal.*kosong|null)", q):
        return {"intent": "bp_reklame_tanggal_kosong"}
    if re.search(r"reklame.*(rasio|masa.*berlaku|lama.*berlaku)", q):
        return {"intent": "bp_reklame_rasio"}
    if re.search(r"reklame.*(tagihan|perpanjangan|bayar|retribusi)", q):
        return {"intent": "bp_reklame_tagihan"}
    if re.search(r"reklame.*(detail|tabel|rincian|data)", q):
        return {"intent": "bp_reklame_detail"}

    # ── Pengaduan ──
    if re.search(r"pengaduan.*(masuk|total|rekap)", q):
        return {"intent": "bp_pengaduan_masuk"}
    if re.search(r"pengaduan.*(status|komposisi|sebaran)", q):
        return {"intent": "bp_pengaduan_status"}
    if re.search(r"pengaduan.*(detail|tabel|rincian|data)", q):
        return {"intent": "bp_pengaduan_detail"}

    # ── Tracking ──
    if re.search(r"tracking|lacak|cek.*permohonan|status.*permohonan", q):
        return {"intent": "bp_tracking"}

    # ── Profil Usaha ──
    if re.search(r"profil.*(usaha|perusahaan)|riwayat.*perizinan|data.*perusahaan", q):
        return {"intent": "bp_profil_usaha"}

    # ── Fallback: kalau mengandung kata kunci BP Batam + izin → KPI Card ──
    has_bp = re.search(r"\bbp\b|bp[\s_]?batam|data.?warehouse", q)
    has_izin = re.search(r"izin|perizinan|permohonan", q)
    has_total = re.search(r"total|jumlah|ringkasan|rekap|dashboard", q)

    if has_bp and has_izin:
        return {"intent": "bp_all_kpi_card"}
    if has_bp and has_total:
        return {"intent": "bp_all_kpi_card"}
    if has_izin and has_total:
        return {"intent": "bp_all_kpi_card"}

    return None  # biar embedding / LLM fallback yg handle
