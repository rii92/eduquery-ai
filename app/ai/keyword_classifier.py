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

    # ── Tren Inflow vs Outflow (sebelum Flow/Sankey karena lebih spesifik) ──
    if re.search(r"tren.*inflow|tren.*outflow|inflow.*outflow|masuk.*terbit.*hari|perbandingan.*masuk.*terbit|perbandingan.*inflow.*outflow|total.*terbit.*hari|terbit.*hari\s*ini|masuk.*dan.*terbit", q):
        return {"intent": "bp_tren_inflow_outflow"}

    # ── KPI Card ──
    if re.search(r"kpi|ringkasan.*permohonan|seluruh.*izin", q):
        return {"intent": "bp_all_kpi_card"}

    # ── Flow / Sankey ──
    if re.search(r"flow|sankey|alur.*permohonan|alur.*izin", q):
        return {"intent": "bp_flow_permohonan"}

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

    return None
