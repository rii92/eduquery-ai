from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.webhook import router as webhook_router
from app.api.query import router as query_router
from app.api.config import router as config_router
from app.api.intents import router as intents_router

app = FastAPI(title="EduQuery AI — BP Batam", version="2.0.0")

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def index():
    return FileResponse(str(static_dir / "index.html"))

app.include_router(webhook_router)
app.include_router(query_router)
app.include_router(config_router)
app.include_router(intents_router)

@app.get("/intents")
def intents_page():
    return FileResponse(str(static_dir / "intents.html"))
