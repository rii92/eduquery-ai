import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.keyword_classifier import classify_by_keyword, is_blacklisted
from app.ai.embedding_classifier import classify_by_embedding
from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import InsightService
from app.llm.client import LLMClient

router = APIRouter()


class WhatsAppMessage(BaseModel):
    sender: str
    message: str


bp_service = BPDatabaseService()


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

    insight_svc = InsightService()
    det_insight = insight_svc.deterministic(payload, result)

    llm_insight = ""
    if result:
        for prov in ("llamacpp", "local"):
            llm_client = LLMClient(provider=prov)
            if await llm_client.check_health():
                llm_insight = await insight_svc.llm_narration(llm_client, intent, msg.message, result, det_insight)
                break

    reply = format_bp_reply(payload, result)

    return {"reply": reply, "insight": llm_insight, "deterministic_insight": det_insight, "elapsed": round(time.time() - t0, 2)}
