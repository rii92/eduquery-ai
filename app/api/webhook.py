import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import generate_insight

router = APIRouter()


class WhatsAppMessage(BaseModel):
    sender: str
    message: str


bp_service = BPDatabaseService()


def _extract_intent(message: str) -> dict:
    from app.ai.keyword_classifier import classify_by_keyword
    return classify_by_keyword(message) or {"intent": ""}


@router.post("/webhook/whatsapp")
async def webhook(msg: WhatsAppMessage):
    t0 = time.time()

    payload = _extract_intent(msg.message)
    intent = payload.get("intent")

    if not intent:
        return {"reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.", "elapsed": round(time.time() - t0, 2)}

    sql = bp_service.generate_sql(payload)
    if not bp_service.validate_sql(sql):
        return {"reply": "Maaf, pertanyaan tersebut belum didukung sistem.", "elapsed": round(time.time() - t0, 2)}

    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError as e:
        return {"reply": f"[ERROR] {e}", "elapsed": round(time.time() - t0, 2)}

    if not result:
        return {"reply": "Data tidak ditemukan.", "elapsed": round(time.time() - t0, 2)}

    reply = format_bp_reply(payload, result)

    insight = ""
    if result:
        insight = await generate_insight(intent, msg.message, result, reply)

    return {"reply": reply, "insight": insight, "elapsed": round(time.time() - t0, 2)}
