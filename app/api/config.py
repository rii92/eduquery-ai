"""API endpoint exposing runtime configuration to the frontend."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import (
    OLLAMA_MODEL, OLLAMA_HOST,
    CLOUD_MODEL, CLOUD_API_URL, CLOUD_API_KEY, CLOUD_REFERER,
    EMBEDDING_MODEL,
    DB_TYPE, SQLITE_DB_PATH,
    BP_DB_HOST, BP_DB_SERVICE_NAME,
)

router = APIRouter()


class ConfigResponse(BaseModel):
    local_model: str
    local_host: str
    cloud_model: str
    cloud_api_url: str
    cloud_configured: bool
    cloud_referer: str
    embedding_model: str
    db_type: str
    sqlite_path: str
    bp_host: str
    bp_service: str


@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    return ConfigResponse(
        local_model=OLLAMA_MODEL,
        local_host=OLLAMA_HOST,
        cloud_model=CLOUD_MODEL,
        cloud_api_url=CLOUD_API_URL,
        cloud_configured=bool(CLOUD_API_KEY),
        cloud_referer=CLOUD_REFERER,
        embedding_model=EMBEDDING_MODEL.split("/")[-1] if "/" in EMBEDDING_MODEL else EMBEDDING_MODEL,
        db_type=DB_TYPE,
        sqlite_path=SQLITE_DB_PATH,
        bp_host=BP_DB_HOST,
        bp_service=BP_DB_SERVICE_NAME,
    )
