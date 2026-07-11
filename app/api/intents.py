"""CRUD API for managing intents."""
from fastapi import APIRouter, HTTPException
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
