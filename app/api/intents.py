"""CRUD API for managing intents."""
import csv
import io
import json

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional

from app.intents.loader import (
    list_intents,
    get_intent,
    create_intent,
    update_intent,
    delete_intent,
)

router = APIRouter()


class IntentCreate(BaseModel):
    id: Optional[str] = None
    description: str
    sql_template: str
    params: Dict[str, str] = {}
    examples: List[str] = []
    active: bool = True
    keyword_patterns: List[str] = []
    llm_label: str = ""
    insight_template: Dict = {}
    intent_rules: Dict = {}
    format_config: Dict = {}


class IntentUpdate(BaseModel):
    description: Optional[str] = None
    sql_template: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    examples: Optional[List[str]] = None
    active: Optional[bool] = None
    keyword_patterns: Optional[List[str]] = None
    llm_label: Optional[str] = None
    insight_template: Optional[Dict] = None
    intent_rules: Optional[Dict] = None
    format_config: Optional[Dict] = None


@router.get("/api/intents")
def get_intents():
    return list_intents()


@router.get("/api/intents/{intent_id}")
def get_intent_by_id(intent_id: str):
    item = get_intent(intent_id)
    if item is None:
        raise HTTPException(404, "Intent not found")
    return item


@router.post("/api/intents", status_code=201)
def add_intent(data: IntentCreate):
    return create_intent(data.model_dump())


@router.put("/api/intents/{intent_id}")
def edit_intent(intent_id: str, data: IntentUpdate):
    cleaned = {k: v for k, v in data.model_dump().items() if v is not None}
    if not cleaned:
        raise HTTPException(400, "No fields to update")
    result = update_intent(intent_id, cleaned)
    if result is None:
        raise HTTPException(404, "Intent not found")
    return result


@router.delete("/api/intents/{intent_id}")
def remove_intent(intent_id: str):
    if not delete_intent(intent_id):
        raise HTTPException(404, "Intent not found")
    return {"ok": True}


# ── CSV Export ──

@router.get("/api/intents/export/csv")
def export_intents_csv():
    """Export all intents as CSV (also serves as download template)."""
    intents = list_intents()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "description", "sql_template", "params", "examples",
        "keyword_patterns", "llm_label", "insight_template", "format_config", "active",
    ])

    for item in intents:
        writer.writerow([
            item.get("id", ""),
            item.get("description", ""),
            item.get("sql_template", ""),
            json.dumps(item.get("params", {}), ensure_ascii=False),
            json.dumps(item.get("examples", []), ensure_ascii=False),
            json.dumps(item.get("keyword_patterns", []), ensure_ascii=False),
            item.get("llm_label", ""),
            json.dumps(item.get("insight_template", {}), ensure_ascii=False),
            json.dumps(item.get("format_config", {}), ensure_ascii=False),
            str(item.get("active", True)).lower(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intents_template.csv"},
    )


# ── CSV Import ──

@router.post("/api/intents/import/csv")
async def import_intents_csv(file: UploadFile = File(...)):
    """Import intents from a CSV file. Returns count of imported + errors."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    results = {"imported": 0, "skipped": 0, "errors": []}

    for row in reader:
        try:
            data = {
                "id": row.get("id", "").strip() or None,
                "description": row.get("description", "").strip(),
                "sql_template": row.get("sql_template", "").strip(),
                "params": json.loads(row.get("params", "{}") or "{}"),
                "examples": json.loads(row.get("examples", "[]") or "[]"),
                "keyword_patterns": json.loads(row.get("keyword_patterns", "[]") or "[]"),
                "llm_label": row.get("llm_label", "").strip(),
                "insight_template": json.loads(row.get("insight_template", "{}") or "{}"),
                "format_config": json.loads(row.get("format_config", "{}") or "{}"),
                "active": row.get("active", "true").strip().lower() == "true",
            }

            if not data["description"] or not data["sql_template"]:
                results["skipped"] += 1
                results["errors"].append(f"Baris {reader.line_num}: description atau sql_template kosong")
                continue

            create_intent(data)
            results["imported"] += 1

        except Exception as e:
            results["errors"].append(f"Baris {reader.line_num}: {e}")

    return results
