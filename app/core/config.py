import os

import dotenv

dotenv.load_dotenv()

# ── App ──
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# ── Dashboard Auth ──
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# ── Local LLM (Ollama) ──
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# ── Cloud LLM (OpenAI-compatible — OpenRouter / OpenAI / dll) ──
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY", "")
CLOUD_API_URL = os.getenv("CLOUD_API_URL", "https://openrouter.ai/api/v1")
CLOUD_MODEL = os.getenv("CLOUD_MODEL", "gpt-4o-mini")
CLOUD_REFERER = os.getenv("CLOUD_REFERER", "http://localhost:8000")
CLOUD_TITLE = os.getenv("CLOUD_TITLE", "BP Batam Ai")

# ── llama.cpp (Local GPU Server) ──
LLAMACPP_API_URL = os.getenv("LLAMACPP_API_URL", "http://172.18.32.172:8080/v1")
LLAMACPP_MODEL = os.getenv("LLAMACPP_MODEL", "ornith-1.0-35b-Q6_K.gguf")
LLAMACPP_TIMEOUT = int(os.getenv("LLAMACPP_TIMEOUT", "120"))

# ── Embedding Model ──
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# ── Database ──
DB_TYPE = os.getenv("DB_TYPE", "oracle")  # "oracle" | "sqlite"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/biquery.db")

# ── BP Batam Oracle (US_DWH + US_DT) ──
BP_DB_USER = os.getenv("BP_DB_USER", "us_dwh")
BP_DB_PASSWORD = os.getenv("BP_DB_PASSWORD", "")
BP_DB_HOST = os.getenv("BP_DB_HOST", "bpdb-scan.bpbatam.go.id:1521")
BP_DB_SERVICE_NAME = os.getenv("BP_DB_SERVICE_NAME", "begs")

# ── iBOSS Oracle (US_oss via us_si) ──
IBOSS_DB_USER = os.getenv("IBOSS_DB_USER", "us_si")
IBOSS_DB_PASSWORD = os.getenv("IBOSS_DB_PASSWORD", "")
IBOSS_DB_HOST = os.getenv("IBOSS_DB_HOST", "bpdb-scan.bpbatam.go.id:1521")
IBOSS_DB_SERVICE_NAME = os.getenv("IBOSS_DB_SERVICE_NAME", "begs")

# ── vOSS Oracle (BSWBY via us_voss) ──
VOSS_DB_USER = os.getenv("VOSS_DB_USER", "us_voss")
VOSS_DB_PASSWORD = os.getenv("VOSS_DB_PASSWORD", "")
VOSS_DB_HOST = os.getenv("VOSS_DB_HOST", "172.16.101.81:1521")
VOSS_DB_SERVICE_NAME = os.getenv("VOSS_DB_SERVICE_NAME", "BSWBY")

# ── BCARE PostgreSQL ──
BCARE_DB_HOST = os.getenv("BCARE_DB_HOST", "172.16.10.126")
BCARE_DB_PORT = int(os.getenv("BCARE_DB_PORT", "5181"))
BCARE_DB_NAME = os.getenv("BCARE_DB_NAME", "bcare")
BCARE_DB_USER = os.getenv("BCARE_DB_USER", "us_ro_pg")
BCARE_DB_PASSWORD = os.getenv("BCARE_DB_PASSWORD", "")
