import json
import time
import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.keyword_classifier import classify_by_keyword, is_blacklisted, is_followup, is_affirmative, needs_context
from app.ai.embedding_classifier import classify_by_embedding
from app.ai.filter_resolver import FilterResolver
from app.llm.client import LLMClient
from app.services.bp_database_service import BPDatabaseService, DatabaseConnectionError
from app.services.bp_formatter_service import format_bp_reply
from app.services.insight_service import InsightService
from app.services.reply_service import generate_llm_reply
from app.core.json_util import DateTimeEncoder, serialize_dates
from app.core.memory import get_memory, history_to_text

router = APIRouter()
bp_service = BPDatabaseService()


class QueryRequest(BaseModel):
    message: str
    session_id: str = ""
    intent_provider: str = "local"
    insight_provider: str = "deterministic"
    insight_llm_provider: str = "local"
    tgl_status_terakhir: str = ""
    perizinan: str = ""
    kategori_status: str = ""
    tahun: str = ""
    bulan: str = ""
    tgl_status: str = ""
    staff: str = ""
    action_time: str = ""
    tgl_daftar: str = ""
    jenis_reklame: str = ""
    tgl_jatuh_tempo: str = ""
    pilih_izin: str = ""
    rentang_tgl_masuk: str = ""
    filter_tahun: str = ""
    filter_bulan: str = ""
    reply_provider: str = "llm"
    reply_llm_provider: str = "llamacpp"


class QueryResponse(BaseModel):
    reply: str
    sql: str = ""
    result: list = []
    intent: str = ""
    session_id: str = ""
    ai_insight: str = ""
    deterministic_insight: str = ""
    elapsed: float = 0.0


async def _sse_process(req_data: dict):
    t0 = time.time()

    def _event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False, cls=DateTimeEncoder)}\n\n"

    message = req_data.get("message", "")
    intent_provider = req_data.get("intent_provider", "local")
    insight_provider = req_data.get("insight_provider", "deterministic")
    insight_llm_provider = req_data.get("insight_llm_provider", "local")

    memory = get_memory()
    session_id = req_data.get("session_id", "") or f"anon_{int(t0)}"
    history = memory.get_history(session_id)

    if not message:
        yield _event({"done": True, "reply": "Pertanyaan kosong.", "elapsed": 0, "progress": 100})
        return

    # ── Step 1: Analisis ──
    yield _event({"step": "Menganalisis pertanyaan...", "progress": 5})
    loop = asyncio.get_event_loop()

    # ── Step 2: Blacklist ──
    if is_blacklisted(message):
        yield _event({
            "done": True,
            "reply": "Maaf, pertanyaan mengandung perintah yang tidak diizinkan.",
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    # ── Step 3: Keyword Classifier ──
    yield _event({"step": "Mencocokkan kata kunci...", "progress": 10})
    payload = classify_by_keyword(message) or {}
    intent = payload.get("intent", "")

    # ── Step 3.5: Follow-up / needs-context detection ──
    if not intent and history:
        is_follow = is_followup(message)
        needs_ctx = needs_context(message)
        if is_follow or needs_ctx:
            last = history[-1]
            if is_follow and not is_affirmative(message):
                yield _event({
                    "done": True,
                    "reply": "Baik, ada pertanyaan lain yang bisa saya bantu?",
                    "intent": "", "session_id": session_id,
                    "elapsed": round(time.time() - t0, 2), "progress": 100,
                })
                return
            yield _event({"step": "Melanjutkan percakapan sebelumnya...", "progress": 15})
            payload = {
                "intent": last.intent,
                **last.payload,
            }
            intent = last.intent

    # ── Step 4: Embedding Classifier (fallback jika keyword tidak cocok) ──
    if not intent or intent == "_greeting":
        if intent == "_greeting":
            reply = payload.get("_reply", "Halo!")
            yield _event({
                "done": True, "reply": reply, "intent": "_greeting",
                "session_id": session_id, "sql": "", "result": [],
                "elapsed": round(time.time() - t0, 2), "progress": 100,
            })
            return

        yield _event({"step": "Mencocokkan semantik (embedding)...", "progress": 20})
        emb_result = await loop.run_in_executor(None, classify_by_embedding, message)
        if emb_result:
            payload = emb_result
            intent = payload["intent"]

    # ── Step 5: LLM Provider (fallback) ──
    if not intent:
        yield _event({"step": f"Menggunakan LLM ({intent_provider})...", "progress": 30})
        try:
            llm = LLMClient(provider=intent_provider)
            health = await llm.check_health()
            if not health:
                yield _event({
                    "done": True,
                    "reply": f"Maaf, LLM {intent_provider} tidak tersedia.",
                    "elapsed": round(time.time() - t0, 2), "progress": 100,
                })
                return
            intent_prompt = f"Classify this question into one of the available intents: {message}"
            intent_text = await llm.generate(intent_prompt, temperature=0.1)
            payload = {"intent": intent_text.strip().lower().replace(" ", "_")}
            intent = payload["intent"]
        except Exception:
            yield _event({
                "done": True,
                "reply": "Maaf, tidak dapat memproses pertanyaan.",
                "elapsed": round(time.time() - t0, 2), "progress": 100,
            })
            return

    # ── Step 5.5: FilterResolver (temporal keyword → SQL params) ──
    if intent and intent not in ("_greeting",):
        is_follow = is_followup(message)
        needs_ctx = needs_context(message)
        if not ((is_follow or needs_ctx) and history):
            resolver = FilterResolver()
            resolved = resolver.apply(message, intent)
            if resolved:
                payload.update(resolved)
                for k in resolved:
                    if k in req_data and not req_data.get(k):
                        req_data[k] = resolved[k]

    # ── Step 6: Terapkan filter ──
    for k in ("tgl_status_terakhir", "perizinan", "kategori_status", "tahun", "bulan",
              "tgl_status", "staff", "action_time", "tgl_daftar", "jenis_reklame", "tgl_jatuh_tempo",
              "pilih_izin", "rentang_tgl_masuk", "filter_tahun", "filter_bulan"):
        v = req_data.get(k, "")
        if v:
            payload[k] = v

    # ── Step 7: Generate SQL ──
    yield _event({"step": "Menyusun query SQL...", "progress": 40})
    sql = bp_service.generate_sql(payload)

    if not sql:
        yield _event({
            "done": True, "reply": "Maaf, pertanyaan tersebut belum didukung sistem.",
            "sql": "", "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    # ── Step 8: Validate SQL ──
    yield _event({"step": "Memvalidasi SQL...", "progress": 55})
    if not bp_service.validate_sql(sql):
        yield _event({
            "done": True, "reply": "Maaf, pertanyaan tersebut belum didukung sistem.",
            "sql": sql, "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    # ── Step 9: Execute SQL ──
    yield _event({"step": "Menjalankan query ke database...", "progress": 70})
    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError:
        yield _event({
            "done": True, "reply": "Maaf, database sedang tidak tersedia. Silakan coba lagi nanti.", "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    if not result:
        yield _event({
            "done": True, "reply": "Data tidak ditemukan.", "sql": sql, "result": [],
            "elapsed": round(time.time() - t0, 2), "progress": 100,
        })
        return

    # ── Step 10: Insight Deterministik ──
    insight_service = InsightService()
    det_insight = insight_service.deterministic(payload, result)

    # ── Step 11: Insight Narration (LLM opsional / otomatis di Natural mode) ──
    llm_insight = ""
    reply_provider_val = req_data.get("reply_provider", "llm")
    should_insight = insight_provider == "llm" or reply_provider_val == "llm"
    insight_prov = insight_llm_provider if insight_provider == "llm" else req_data.get("reply_llm_provider", "llamacpp")
    if should_insight:
        yield _event({"step": f"Menganalisis insight ({insight_prov})...", "progress": 85})
        llm_client = LLMClient(provider=insight_prov)
        llm_insight = await insight_service.llm_narration(llm_client, intent, message, result, det_insight)

    # ── Step 12: Reply Formatter (with history context) ──
    reply_llm_provider = req_data.get("reply_llm_provider", "llamacpp")
    if reply_provider_val == "llm":
        yield _event({"step": f"Menyusun jawaban natural ({reply_llm_provider})...", "progress": 90})
        reply = await generate_llm_reply(message, intent, result, payload, llm_provider=reply_llm_provider, timeout=120, history=history)
        if not reply:
            reply = format_bp_reply(payload, result)
    else:
        reply = format_bp_reply(payload, result)

    memory.add(session_id, message, reply, intent, sql, payload)

    yield _event({"step": "Menyusun jawaban...", "progress": 95})
    yield _event({
        "done": True, "reply": reply, "sql": sql,
        "result": serialize_dates(result),
        "intent": intent,
        "session_id": session_id,
        "ai_insight": llm_insight,
        "deterministic_insight": det_insight,
        "elapsed": round(time.time() - t0, 2), "progress": 100,
    })


@router.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    t0 = time.time()
    loop = asyncio.get_event_loop()
    memory = get_memory()
    session_id = req.session_id or f"anon_{int(t0)}"
    history = memory.get_history(session_id)

    # Step 1-2: Blacklist + Keyword
    if is_blacklisted(req.message):
        return QueryResponse(reply="Maaf, pertanyaan mengandung perintah yang tidak diizinkan.", elapsed=round(time.time() - t0, 2))
    payload = classify_by_keyword(req.message) or {}
    intent = payload.get("intent", "")

    # Step 3: Greeting (fast return)
    if intent == "_greeting":
        return QueryResponse(reply=payload.get("_reply", "Halo!"), intent="_greeting", session_id=session_id, elapsed=round(time.time() - t0, 2))

    # Step 4: Follow-up / needs-context handling
    if not intent and history:
        is_follow = is_followup(req.message)
        needs_ctx = needs_context(req.message)
        if is_follow or needs_ctx:
            last = history[-1]
            if is_follow and not is_affirmative(req.message):
                return QueryResponse(
                    reply="Baik, ada pertanyaan lain yang bisa saya bantu?",
                    session_id=session_id, elapsed=round(time.time() - t0, 2),
                )
            payload = {
                "intent": last.intent,
                **last.payload,
            }
            intent = last.intent

    # Step 5: Embedding Classifier (fallback, thread executor agar tidak block event loop)
    if not intent:
        try:
            emb = await asyncio.wait_for(
                loop.run_in_executor(None, classify_by_embedding, req.message),
                timeout=30.0,
            )
            if emb:
                payload = emb
                intent = payload["intent"]
        except (asyncio.TimeoutError, Exception):
            pass

    # Step 6: LLM Fallback (user-selected provider)
    if not intent:
        llm = LLMClient(provider=req.intent_provider)
        try:
            llm_health = await llm.check_health()
            if not llm_health:
                return QueryResponse(reply=f"Maaf, LLM {req.intent_provider} tidak tersedia.", session_id=session_id, elapsed=round(time.time() - t0, 2))
            intent_text = await llm.generate(f"Classify: {req.message}", temperature=0.1)
            payload = {"intent": intent_text.strip().lower().replace(" ", "_")}
            intent = payload["intent"]
        except Exception:
            return QueryResponse(reply="Maaf, tidak dapat memproses pertanyaan.", session_id=session_id, elapsed=round(time.time() - t0, 2))

    if not intent:
        return QueryResponse(reply="Maaf, tidak dapat memahami pertanyaan.", session_id=session_id, elapsed=round(time.time() - t0, 2))

    # Step 6.5: FilterResolver (temporal keyword -> SQL params)
    if intent and intent not in ("_greeting",):
        # Only run resolver if NOT a follow-up (payload already has filters)
        is_follow = is_followup(req.message)
        needs_ctx = needs_context(req.message)
        if not ((is_follow or needs_ctx) and history):
            resolver = FilterResolver()
            resolved = resolver.apply(req.message, intent)
            if resolved:
                payload.update(resolved)

    # Step 7: Apply explicit request filters
    for k in ("tgl_status_terakhir", "perizinan", "kategori_status", "tahun", "bulan",
              "tgl_status", "staff", "action_time", "tgl_daftar", "jenis_reklame", "tgl_jatuh_tempo",
              "pilih_izin", "rentang_tgl_masuk", "filter_tahun", "filter_bulan"):
        v = getattr(req, k, "")
        if v:
            payload[k] = v

    # Step 8: Generate SQL
    sql = bp_service.generate_sql(payload)
    if not sql:
        return QueryResponse(reply="Maaf, pertanyaan tersebut belum didukung sistem.", sql=sql, session_id=session_id, elapsed=round(time.time() - t0, 2))

    # Step 9: Validate SQL
    if not bp_service.validate_sql(sql):
        return QueryResponse(reply="Maaf, pertanyaan tersebut belum didukung sistem.", sql=sql, session_id=session_id, elapsed=round(time.time() - t0, 2))

    # Step 10: Execute SQL
    try:
        result = bp_service.execute(sql)
    except DatabaseConnectionError:
        return QueryResponse(reply="Maaf, database sedang tidak tersedia. Silakan coba lagi nanti.", sql=sql, result=[], session_id=session_id, elapsed=round(time.time() - t0, 2))

    if not result:
        return QueryResponse(reply="Data tidak ditemukan.", sql=sql, result=[], session_id=session_id, elapsed=round(time.time() - t0, 2))

    # Step 11: Insight deterministic
    insight_service = InsightService()
    det_insight = insight_service.deterministic(payload, result)

    # Step 12: Insight narration (opsional)
    llm_insight = ""
    if req.insight_provider == "llm":
        llm_client = LLMClient(provider=req.insight_llm_provider)
        llm_insight = await insight_service.llm_narration(llm_client, intent, req.message, result, det_insight)

    # Step 13: Reply formatter (with conversation history context)
    if req.reply_provider == "llm":
        reply = await generate_llm_reply(
            req.message, intent, result, payload,
            llm_provider=req.reply_llm_provider,
            timeout=120, history=history,
        )
        if not reply:
            reply = format_bp_reply(payload, result)
    else:
        reply = format_bp_reply(payload, result)

    # Store in memory
    memory.add(session_id, req.message, reply, intent, sql, payload)

    return QueryResponse(
        reply=reply, sql=sql, result=serialize_dates(result),
        intent=intent, session_id=session_id, ai_insight=llm_insight,
        deterministic_insight=det_insight,
        elapsed=round(time.time() - t0, 2),
    )


@router.get("/api/query/stream")
async def query_stream(
    message: str = Query(..., description="Pertanyaan dalam bahasa alami"),
    intent_provider: str = Query("local", description="Provider LLM untuk intent: local/cloud"),
    insight_provider: str = Query("deterministic", description="Provider insight: deterministic/llm"),
    insight_llm_provider: str = Query("local", description="Provider LLM untuk insight narration: local/cloud"),
    tgl_status_terakhir: str = Query("", description="Filter tanggal (BP Batam)"),
    perizinan: str = Query("", description="Filter jenis izin (BP Batam)"),
    kategori_status: str = Query("", description="Filter kategori status (BP Batam)"),
    tahun: str = Query("", description="Filter tahun (contoh: 2025)"),
    bulan: str = Query("", description="Filter bulan (contoh: 01)"),
    tgl_status: str = Query("", description="Filter tanggal status (Monitoring Staf)"),
    staff: str = Query("", description="Filter nama staf/verifikator"),
    action_time: str = Query("", description="Filter waktu aksi (OSS)"),
    tgl_daftar: str = Query("", description="Filter tanggal daftar (Reklame)"),
    jenis_reklame: str = Query("", description="Filter jenis reklame"),
    tgl_jatuh_tempo: str = Query("", description="Filter tanggal jatuh tempo (Reklame)"),
    pilih_izin: str = Query("", description="Filter pilih jenis izin (full SQL clause)"),
    rentang_tgl_masuk: str = Query("", description="Filter rentang tanggal masuk (full SQL clause)"),
    filter_tahun: str = Query("", description="Filter tahun (contoh: TAHUN = '2025')"),
    filter_bulan: str = Query("", description="Filter bulan (contoh: BULAN = '01')"),
    reply_provider: str = Query("llm", description="Gaya jawaban: deterministic / llm"),
    reply_llm_provider: str = Query("llamacpp", description="Provider LLM untuk jawaban natural: local / cloud / llamacpp"),
):
    req_data = {
        "message": message,
        "intent_provider": intent_provider,
        "insight_provider": insight_provider,
        "insight_llm_provider": insight_llm_provider,
        "tgl_status_terakhir": tgl_status_terakhir,
        "perizinan": perizinan,
        "kategori_status": kategori_status,
        "tahun": tahun,
        "bulan": bulan,
        "tgl_status": tgl_status,
        "staff": staff,
        "action_time": action_time,
        "tgl_daftar": tgl_daftar,
        "jenis_reklame": jenis_reklame,
        "tgl_jatuh_tempo": tgl_jatuh_tempo,
        "pilih_izin": pilih_izin,
        "rentang_tgl_masuk": rentang_tgl_masuk,
        "filter_tahun": filter_tahun,
        "filter_bulan": filter_bulan,
        "reply_provider": reply_provider,
        "reply_llm_provider": reply_llm_provider,
    }
    return StreamingResponse(_sse_process(req_data), media_type="text/event-stream")
