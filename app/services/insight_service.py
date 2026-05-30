"""AI Insight generator — analisis hasil query via Ollama."""

import json

import httpx

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT
from app.core.json_util import serialize_dates
from app.intents.loader import get_intent


def _compute_stats(data: list[dict]) -> dict:
    if not data:
        return {}
    keys = list(data[0].keys())
    stats = {"total_rows": len(data)}
    for k in keys:
        vals = [r[k] for r in data if isinstance(r.get(k), (int, float))]
        if vals:
            stats[f"{k}_total"] = sum(vals)
            stats[f"{k}_avg"] = round(sum(vals) / len(vals), 1)
            stats[f"{k}_min"] = min(vals)
            stats[f"{k}_max"] = max(vals)
    return stats


def _sample_data(data: list[dict], max_rows: int = 5) -> list[dict]:
    if len(data) <= max_rows:
        return data
    head = data[:3]
    tail = data[-2:]
    return head + [{"...": "(...)"}] + tail


def _build_prompt(
    intent_id: str,
    question: str,
    data: list[dict],
    formatted_reply: str,
) -> str:
    meta = get_intent(intent_id)
    intent_desc = meta["description"] if meta else intent_id

    stats = _compute_stats(data)
    stats_str = ", ".join(f"{k}: {v}" for k, v in stats.items())

    sample = _sample_data(data)
    sample_json = json.dumps(serialize_dates(sample), indent=2, ensure_ascii=False)

    numerical_key = next((k for k in stats if k.endswith("_total") and k != "total_rows"), None)
    total_value = stats.get(numerical_key, "") if numerical_key else ""

    return f"""Kamu adalah asisten analis BP Batam. Beri insight 1-2 kalimat saja, langsung ke inti.

Laporan: {intent_desc}
Pertanyaan: {question}
Total data: {stats.get('total_rows', len(data))} baris
Total nilai: {total_value}
Statistik: {stats_str}

Contoh data (sample):
```json
{sample_json}
```

INSTRUKSI: Jawab dalam 1-2 kalimat Bahasa Indonesia. Langsung ke insight utama: tren naik/turun, angka penting, atau rekomendasi singkat. JANGAN pake format, daftar, atau markdown."""


async def _check_ollama(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


async def generate_insight(
    intent_id: str,
    question: str,
    data: list[dict],
    formatted_reply: str,
) -> str:
    if not data:
        return ""

    prompt = _build_prompt(intent_id, question, data, formatted_reply)

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            if not await _check_ollama(client):
                return f"🤖 AI Insight tidak tersedia — Ollama tidak terhubung. Pastikan Ollama sudah berjalan di `{OLLAMA_HOST}`."

            resp = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 512,
                    },
                },
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "").strip()
    except httpx.TimeoutException:
        return "🤖 AI Insight tidak tersedia — waktu tunggu Ollama habis."
    except Exception:
        return "🤖 AI Insight tidak tersedia — terjadi kesalahan saat menghubungi Ollama."
