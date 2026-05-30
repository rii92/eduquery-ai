import json
import time
import asyncio

from app.core.json_util import DateTimeEncoder, serialize_dates

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import generate_insight
from app.intents.loader import get_intent

router = APIRouter()

bp_service = BPDatabaseService()


class QueryRequest(BaseModel):
    message: str
    tgl_status_terakhir: str = ""
    perizinan: str = ""
    kategori_status: str = ""


class QueryResponse(BaseModel):
    reply: str
    sql: str = ""
    result: list = []
    elapsed: float = 0.0
    ai_insight: str = ""


def _extract_intent(message: str) -> dict:
    from app.ai.keyword_classifier import classify_by_keyword
    return classify_by_keyword(message) or {"intent": ""}


def _execute(intent: str, payload: dict):
    sql = bp_service.generate_sql(payload)
    if not bp_service.validate_sql(sql):
        return None, sql, []
    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError as e:
        return f"[ERROR] {e}", sql, []
    reply = format_bp_reply(payload, result) if result else ""
    return reply, sql, result


@router.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    t0 = time.time()

    payload = _extract_intent(req.message)
    payload = _apply_filters(payload, req)
    intent = payload.get("intent")

    if not intent:
        return QueryResponse(
            reply="Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.",
            elapsed=round(time.time() - t0, 2),
        )

    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        return QueryResponse(reply=reply, elapsed=round(time.time() - t0, 2))

    reply, sql, result = _execute(intent, payload)
    if reply is None:
        return QueryResponse(
            reply="Maaf, pertanyaan tersebut belum didukung sistem.",
            sql=sql, elapsed=round(time.time() - t0, 2),
        )
    if reply.startswith("[ERROR]"):
        return QueryResponse(
            reply=reply, sql=sql, result=[],
            elapsed=round(time.time() - t0, 2),
        )
    if not result:
        return QueryResponse(
            reply="Data tidak ditemukan.", sql=sql, result=[],
            elapsed=round(time.time() - t0, 2),
        )

    insight = ""
    if result:
        insight = await generate_insight(intent, req.message, result, reply)

    return QueryResponse(
        reply=reply, sql=sql, result=serialize_dates(result),
        ai_insight=insight,
        elapsed=round(time.time() - t0, 2),
    )


def _apply_filters(payload: dict, req: QueryRequest) -> dict:
    if req.tgl_status_terakhir:
        payload["tgl_status_terakhir"] = req.tgl_status_terakhir
    if req.perizinan:
        payload["perizinan"] = req.perizinan
    if req.kategori_status:
        payload["kategori_status"] = req.kategori_status
    return payload


async def _sse_process(req_data: dict):
    t0 = time.time()

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False, cls=DateTimeEncoder)}\n\n"

    message = req_data.get("message", "")
    if not message:
        yield _event({"done": True, "reply": "Pertanyaan kosong.", "elapsed": 0, "progress": 100})
        return

    yield _event({"step": "Menganalisis pertanyaan...", "progress": 10})
    loop = asyncio.get_event_loop()
    payload = await loop.run_in_executor(None, _extract_intent, message)
    intent = payload.get("intent")

    if not intent:
        yield _event({
            "done": True,
            "reply": "Maaf, untuk pertanyaan tersebut data belum tersedia di sistem kami.",
            "sql": "", "result": [], "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    if intent == "_greeting":
        reply = payload.get("_reply", "Halo! Ada yang bisa saya bantu?")
        yield _event({
            "done": True, "reply": reply, "sql": "", "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    for k in ("tgl_status_terakhir", "perizinan", "kategori_status"):
        v = req_data.get(k, "")
        if v:
            payload[k] = v

    yield _event({"step": "Menyusun query SQL...", "progress": 25})
    reply, sql, result = await loop.run_in_executor(None, _execute, intent, payload)

    if reply is None:
        yield _event({
            "done": True,
            "reply": "Maaf, pertanyaan tersebut belum didukung sistem.",
            "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    if reply.startswith("[ERROR]"):
        yield _event({
            "done": True, "reply": reply, "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    yield _event({"step": "Memvalidasi SQL...", "progress": 40})
    if not result:
        yield _event({
            "done": True, "reply": "Data tidak ditemukan.", "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    yield _event({"step": "Menjalankan query ke database...", "progress": 60})
    insight = ""
    if result:
        yield _event({"step": "Menganalisis insight...", "progress": 80})
        insight = await generate_insight(intent, message, result, reply)

    yield _event({"step": "Menyusun jawaban...", "progress": 95})
    yield _event({
        "done": True, "reply": reply, "sql": sql, "result": result,
        "ai_insight": insight,
        "elapsed": round(time.time() - t0, 2), "progress": 100,
    })


@router.get("/api/query/stream")
async def query_stream(
    message: str = Query(..., description="Pertanyaan dalam bahasa alami"),
    tgl_status_terakhir: str = Query("", description="Filter tanggal (BP Batam)"),
    perizinan: str = Query("", description="Filter jenis izin (BP Batam)"),
    kategori_status: str = Query("", description="Filter kategori status (BP Batam)"),
):
    req_data = {
        "message": message,
        "tgl_status_terakhir": tgl_status_terakhir,
        "perizinan": perizinan,
        "kategori_status": kategori_status,
    }
    return StreamingResponse(_sse_process(req_data), media_type="text/event-stream")
