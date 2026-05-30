# EduQuery AI — BP Batam Data Warehouse

EduQuery AI adalah sistem tanya-jawab database **BP Batam Data Warehouse** berbasis bahasa alami. Mengakses data perizinan dari Oracle DB (`US_DWH.BI_MART_STATUS_PERIZINAN`) melalui antarmuka web dan endpoint API.

## Fitur

- **Intent-based SQL**: 6+ intent pertanyaan perizinan dengan template SQL
- **Keyword Classifier**: Deteksi intent cepat (tanpa LLM) untuk pertanyaan umum seperti total masuk, izin terbit, backlog
- **LLM Fallback**: Ollama (`gemma3:1b`) untuk pertanyaan kompleks yang tidak cocok keyword
- **Filter Tanggal & Jenis Izin**: Parameter filter `tgl_status_terakhir`, `perizinan`, `kategori_status`
- **SSE Streaming**: Progress real-time saat memproses pertanyaan
- **Riwayat Pertanyaan**: Tersimpan di localStorage browser
- **Intent Management**: Halaman `/intents` untuk melihat/mengeditt intent
- **Oracle Database**: Koneksi langsung ke BP Batam Oracle DB via python-oracledb (thin mode)

## Quick Start

```bash
# Install dependencies
uv sync

# Salin .env dari .env.example, sesuaikan dengan kredensial Oracle BP Batam
cp .env.example .env

# Jalankan server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Buka `http://localhost:8000` setelah server berjalan.

### Testing

```bash
uv run pytest
```

## Antarmuka Web

Buka `http://localhost:8000`:

- Kotak teks untuk mengetik pertanyaan seputar data perizinan BP Batam
- Filter tanggal (`tgl_status_terakhir`) dan jenis izin (`perizinan`)
- Timer elapsed realtime selama loading
- Progress bar + step indicator (SSE streaming)
- Menampilkan SQL query yang dihasilkan, hasil mentah (tabel/JSON), dan balasan natural
- **AI Insight**: Analisis otomatis dari hasil query oleh LLM (toggle on/off), muncul di card terpisah
- Riwayat pertanyaan tersimpan di localStorage (klik untuk menjalankan ulang)

## Endpoint API

### `POST /api/query`

Mengembalikan SQL, hasil mentah, balasan natural.

```json
{
  "message": "Total masuk izin BP Batam",
  "tgl_status_terakhir": "",
  "perizinan": "",
  "kategori_status": ""
}
```

### `GET /api/query/stream`

SSE endpoint dengan progress real-time.

```
GET /api/query/stream?message=Total+masuk+izin+BP+Batam&tgl_status_terakhir=&perizinan=
```

### `GET /api/config`

Mengembalikan konfigurasi publik (model Ollama, daftar intent source).

### `GET /api/intents`

Daftar intent, template SQL, contoh, dan parameter.

## Intent Tersedia

| Intent ID | Deskripsi |
|-----------|-----------|
| `bp_total_masuk` | Total permohonan izin masuk per minggu |
| `bp_izin_terbit_per_bulan` | Izin terbit per minggu |
| `bp_total_backlog_per_bulan` | Total backlog (belum terbit) per minggu |
| `bp_dalam_proses` | Permohonan dalam proses per hari |
| `bp_sebaran_jenis_izin` | Sebaran permohonan berdasarkan jenis izin & status |
| `bp_komposisi_status` | Komposisi keseluruhan status perizinan per minggu |

Intent dikelola secara dinamis melalui file `prompts/intents.json` dan dapat ditambah/diedit melalui halaman `/intents`.

## Environment Variables

Konfigurasi via `.env` (lihat `.env.example` untuk template):

| Variabel | Wajib | Default | Deskripsi |
|----------|-------|---------|-----------|
| `OLLAMA_HOST` | ✅ | `http://localhost:11434` | URL Ollama API |
| `OLLAMA_MODEL` | | `gemma3:1b` | Model LLM |
| `OLLAMA_TIMEOUT` | | `60` | Timeout panggilan Ollama (detik) |
| `APP_HOST` | | `0.0.0.0` | Bind address FastAPI |
| `APP_PORT` | | `8000` | Port FastAPI |
| `BP_DB_USER` | ✅ | `us_dwh` | User Oracle BP Batam |
| `BP_DB_PASSWORD` | ✅ | — | Password Oracle BP Batam |
| `BP_DB_HOST` | ✅ | `bpdb-scan.bpbatam.go.id:1521` | Host:port Oracle |
| `BP_DB_SERVICE_NAME` | ✅ | `begs` | Service name Oracle |

## Project Structure

```
├── app/                          # Aplikasi FastAPI
│   ├── main.py                   # Entry point, serve static + API
│   ├── api/
│   │   ├── config.py             # GET /api/config
│   │   ├── intents.py            # GET /api/intents
│   │   ├── query.py              # POST /api/query + GET /api/query/stream
│   │   └── webhook.py            # Webhook endpoint
│   ├── ai/
│   │   ├── intent_extractor.py   # Intent extraction via Ollama
│   │   └── keyword_classifier.py # Deterministic keyword → intent (fast path)
│   ├── sql/
│   │   ├── template_engine.py    # Intent → SQL templates
│   │   └── validator.py          # SELECT-only validator
│   ├── database/
│   │   └── bp_client.py          # Oracle DB client via SQLAlchemy + oracledb
│   ├── intents/
│   │   └── loader.py             # Load/manage intents from prompts/intents.json
│   ├── services/
│   │   ├── bp_database_service.py # DB service (generate SQL, validate, execute)
│   │   └── bp_formatter_service.py # DB result → natural language
│   └── core/config.py            # Konfigurasi dari .env
├── static/                       # Frontend (Bootstrap)
│   ├── index.html
│   ├── intents.html
│   ├── app.css
│   └── app.js
├── prompts/
│   └── intents.json              # Intent definitions with SQL templates
├── tests/
├── Dockerfile / docker-compose.yml
├── .env.example
├── pyproject.toml
└── uv.lock
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: Oracle via SQLAlchemy + python-oracledb (thin mode)
- **LLM**: Ollama (gemma3:1b)
- **Frontend**: Bootstrap 5, vanilla JS, CodeMirror, marked
- **Package Manager**: uv
