import logging
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.keyword_classifier import classify_by_keyword, is_blacklisted
from app.ai.embedding_classifier import classify_by_embedding
from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import InsightService
from app.services.reply_service import generate_llm_reply

logger = logging.getLogger("webhook")

router = APIRouter()


class WhatsAppMessage(BaseModel):
    sender: str
    message: str


bp_service = BPDatabaseService()


@router.get("/webhook/health")
async def webhook_health():
    """Diagnostik: test koneksi ke Ornith dari dalam container."""
    import httpx
    from app.core.config import LLAMACPP_API_URL, LLAMACPP_MODEL
    from openai import AsyncOpenAI

    result = {"ornith_api_url": LLAMACPP_API_URL, "ornith_model": LLAMACPP_MODEL}

    # Test 1: HTTP GET /v1/models
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{LLAMACPP_API_URL}/models")
            result["http_models"] = {"status": r.status_code, "ok": r.status_code == 200}
    except Exception as e:
        result["http_models"] = {"status": "error", "error": str(e)}

    # Test 2: Chat completion dummy
    try:
        client = AsyncOpenAI(api_key="sk-no-key-required", base_url=LLAMACPP_API_URL, timeout=10)
        resp = await client.chat.completions.create(
            model=LLAMACPP_MODEL,
            messages=[{"role": "user", "content": "Katakan halo dalam 1 kata"}],
            temperature=0.1,
            max_tokens=10,
        )
        result["chat_test"] = {"status": "ok", "reply": resp.choices[0].message.content.strip()}
    except Exception as e:
        result["chat_test"] = {"status": "error", "error": str(e)}

    return result


@router.post("/webhook/whatsapp")
async def webhook(msg: WhatsAppMessage):
    t0 = time.time()

    # Step 1-2: Blacklist + Keyword
    if is_blacklisted(msg.message):
        return {"reply": "Maaf, pertanyaan mengandung perintah yang tidak diizinkan.", "elapsed": round(time.time() - t0, 2)}
    payload = classify_by_keyword(msg.message) or {"intent": ""}
    intent = payload.get("intent")

    # Step 3: Greeting
    if intent == "_greeting":
        return {"reply": payload.get("_reply", "Halo!"), "elapsed": round(time.time() - t0, 2)}

    # Step 4: Embedding Classifier (fallback)
    if not intent:
        emb = classify_by_embedding(msg.message)
        if emb:
            payload = emb
            intent = payload["intent"]

    if not intent:
        return {"reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.", "elapsed": round(time.time() - t0, 2)}

    sql = bp_service.generate_sql(payload)
    if not sql or not bp_service.validate_sql(sql):
        return {"reply": "Maaf, pertanyaan tersebut belum didukung sistem.", "elapsed": round(time.time() - t0, 2)}

    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError:
        return {"reply": "Maaf, database sedang tidak tersedia. Silakan coba lagi nanti.", "elapsed": round(time.time() - t0, 2)}

    if not result:
        return {"reply": "Data tidak ditemukan.", "elapsed": round(time.time() - t0, 2)}

    det_insight = InsightService().deterministic(payload, result)

    # Coba llamacpp dulu, fallback ke local, terakhir deterministic
    reply = ""
    for prov in ("llamacpp", "local"):
        logger.info("Mencoba LLM provider=%s untuk intent=%s", prov, intent)
        reply = await generate_llm_reply(msg.message, intent, result, payload, llm_provider=prov, timeout=120)
        if reply:
            logger.info("Berhasil pakai provider=%s — %d chars", prov, len(reply))
            break
        logger.warning("Provider=%s gagal, coba provider berikutnya", prov)

    if not reply:
        logger.warning("Semua LLM gagal, fallback ke format deterministik")
        reply = format_bp_reply(payload, result)

    return {"reply": reply, "elapsed": round(time.time() - t0, 2)}
