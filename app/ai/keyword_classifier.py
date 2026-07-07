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
        return {"intent": "_greeting", "_reply": "Halo! Ada yang bisa saya bantu?"}
    if re.search(r"\b(terima\s*kasih|makasih|thanks|trims)\b", q):
        return {"intent": "_greeting", "_reply": "Sama-sama! Senang bisa membantu."}
    if re.search(r"\b(siapa\s*nama|namamu|nama\s*kamu)\b", q):
        return {"intent": "_greeting", "_reply": "Namaku <b>EduQuery AI</b>! Asisten data warehouse BP Batam."}

    # ── KPI Card ──
    if re.search(r"kpi|ringkasan.*permohonan|seluruh.*izin", q):
        return {"intent": "bp_all_kpi_card"}

    # ── Flow / Sankey ──
    if re.search(r"flow|sankey|alur.*permohonan|alur.*izin", q):
        return {"intent": "bp_flow_permohonan"}

    # ── Tren Inflow vs Outflow ──
    if re.search(r"tren.*inflow|tren.*outflow|inflow.*outflow|masuk.*terbit.*hari", q):
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

    # ── Fallback: BP Batam → KPI Card ──
    has_bp = re.search(r"\bbp\b|bp[\s_]?batam|data.?warehouse", q)
    has_izin = re.search(r"izin|perizinan|permohonan", q)
    has_total = re.search(r"total|jumlah|ringkasan|rekap|dashboard", q)

    if has_bp or has_izin or has_total:
        return {"intent": "bp_all_kpi_card"}

    return {"intent": "bp_all_kpi_card"}
