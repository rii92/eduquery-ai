import os

import dotenv

dotenv.load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

BP_DB_USER = os.getenv("BP_DB_USER", "us_dwh")
BP_DB_PASSWORD = os.getenv("BP_DB_PASSWORD", "DeWeHaRS20DuaFive")
BP_DB_HOST = os.getenv("BP_DB_HOST", "bpdb-scan.bpbatam.go.id:1521")
BP_DB_SERVICE_NAME = os.getenv("BP_DB_SERVICE_NAME", "begs")