# Tutorial Menjalankan EduQuery AI

EduQuery AI adalah sistem tanya-jawab database BP Batam (Oracle) & database sekolah berbasis bahasa alami.

## Daftar Isi

1. [Prasyarat](#1-prasyarat)
2. [Setup Project](#2-setup-project)
3. [Konfigurasi Environment](#3-konfigurasi-environment)
4. [Virtual Environment & Dependencies](#4-virtual-environment--dependencies)
5. [Menjalankan dengan Docker](#5-menjalankan-dengan-docker)
6. [Menjalankan secara Lokal (Tanpa Docker)](#6-menjalankan-secara-lokal-tanpa-docker)
7. [Menggunakan Aplikasi](#7-menggunakan-aplikasi)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prasyarat

| Tool | Minimal Versi | Keterangan |
|------|---------------|------------|
| Python | 3.11+ | [Download](https://www.python.org/downloads/) |
| uv | 0.5+ | Installer: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` |
| Git | any | [Download](https://git-scm.com/) |
| Ollama | any | [Download](https://ollama.com/) — opsional untuk LLM fallback |
| Docker | any | [Download](https://www.docker.com/) — opsional, untuk deployment container |

> **Catatan**: Ollama bersifat opsional. Sistem berjalan 100% menggunakan keyword classifier tanpa LLM. Jika Ollama tidak tersedia, fallback LLM akan dilewati.

---

## 2. Setup Project

```bash
# Clone repository
git clone <url-repository> eduquery-ai
cd eduquery-ai

# Copy environment file
cp .env.example .env
```

---

## 3. Konfigurasi Environment

Edit file `.env` sesuai lingkungan Anda:

```ini
# ── Database Sekolah ──────────────────────────────────
DB_IS_LOCAL=true              # true = SQLite, false = MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=db_eduquery
DB_USER=root
DB_PASSWORD=p@ssw0rd!

# ── Ollama LLM (opsional) ─────────────────────────────
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
OLLAMA_TIMEOUT=30

# ── Server ────────────────────────────────────────────
APP_HOST=0.0.0.0
APP_PORT=8000

# ── SQLite ────────────────────────────────────────────
SQLITE_PATH=database/eduquery.db

# ── Tahun Ajaran ──────────────────────────────────────
ACADEMIC_YEARS=2023/2024,2024/2025,2025/2026

# ── BP Batam Data Warehouse (Oracle) ──────────────────
BP_DB_USER=us_dwh
BP_DB_PASSWORD=DeWeHaRS20DuaFive
BP_DB_HOST=bpdb-scan.bpbatam.go.id:1521
BP_DB_SERVICE_NAME=begs
```

### Variabel Penting

| Variabel | Fungsi |
|----------|--------|
| `DB_IS_LOCAL=true` | Pakai SQLite (tidak perlu install MySQL) |
| `DB_IS_LOCAL=false` | Pakai MySQL, harus ada MySQL server |
| `OLLAMA_HOST` | URL Ollama server. Kosongkan jika tidak pakai LLM |
| `BP_DB_*` | Koneksi Oracle BP Batam. Biarkan default, akan error otomatis jika di luar jaringan BP |

---

## 4. Virtual Environment & Dependencies

```bash
# Buat virtual environment dan install dependencies
uv sync

# Aktifkan virtual environment
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Mac/Linux
```

### Inisialisasi Database Sekolah

```bash
# Jalankan migrasi (buat tabel + seed data)
uv run python -m app.database.migrate
```

### Pull Model Ollama (Opsional)

```bash
# Cek apakah model sudah ada
ollama list

# Pull model (wajib sekali)
ollama pull gemma3:1b
```

---

## 5. Menjalankan dengan Docker

Cara termudah — semua service berjalan dalam container:

```bash
# Build & jalankan semua service
docker compose up --build
```

Atau via script helper:

```bash
scripts/run.sh docker
```

Perintah akan menjalankan:
1. **mysql** — Database MySQL 8.0
2. **ollama** — Ollama server (pull model otomatis)
3. **init** — Migrasi database (sekali jalan, lalu selesai)
4. **app** — FastAPI server di `http://localhost:8000`

### Perintah Docker Lainnya

```bash
# Restart app container (ambil perubahan kode)
docker compose restart app

# Lihat log
docker compose logs -f app

# Hentikan semua
docker compose down

# Jalankan ulang migrasi
docker compose run --rm init
```

---

## 6. Menjalankan secara Lokal (Tanpa Docker)

### a. Persiapan (cukup sekali)

```bash
# 1. Install dependencies
uv sync

# 2. Pull model Ollama (jika pakai LLM)
ollama pull gemma3:1b

# 3. Migrasi database sekolah
uv run python -m app.database.migrate
```

### b. Jalankan Server

```bash
# Mode development (hot-reload)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Mode production
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Atau via script helper:

```bash
scripts/run.sh start
```

### c. Jalankan Server di Port Berbeda

Jika port 8000 sudah dipakai:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### d. Matikan Server

Tekan `Ctrl + C` di terminal.

Jika port masih terpakai (zombie process di Windows):

```bash
# Cari PID pemilik port
netstat -ano | findstr :8000

# Matikan paksa
taskkill /F /PID <PID_DARI_NETSTAT>
```

---

## 7. Menggunakan Aplikasi

### Halaman Web

| URL | Halaman |
|-----|---------|
| `http://localhost:8000` | **BP Batam Executive Summary** — dashboard perizinan |
| `http://localhost:8000/sekolah` | **Sekolah** — query data siswa, guru, nilai |
| `http://localhost:8000/intents` | **Intent Management** — kelola daftar intent & SQL template |

### Contoh Query BP Batam

Kirim via URL (GET):

```
http://localhost:8000/api/query/stream?message=Jumlah+izin+yang+sudah+terbit
```

Atau via POST:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Jumlah izin yang sudah terbit"}'
```

Response:

```json
{
  "reply": "[ERROR] Gagal terhubung ke database BP Batam: [Errno 11001] getaddrinfo failed",
  "sql": "SELECT ... FROM US_DWH.BI_MART_STATUS_PERIZINAN ...",
  "result": [],
  "elapsed": 1.63
}
```

> **Catatan**: Query BP Batam hanya berhasil jika dijalankan dari dalam jaringan BP Batam. Di luar jaringan, akan muncul error koneksi — ini normal.

### Contoh Query Sekolah

```
http://localhost:8000/api/query/stream?message=Berapa+jumlah+siswa
```

### Halaman Intent Management

`http://localhost:8000/intents`

- Lihat semua intent (30 sekolah + 6 BP Batam)
- Tambah intent baru
- Edit SQL template, parameter, contoh pertanyaan
- Nonaktifkan/aktifkan intent
- Hapus intent

---

## 8. Testing

```bash
# Jalankan semua test
uv run pytest

# Atau via script
scripts/run.sh test
```

---

## 9. Troubleshooting

### Port 8000 sudah dipakai

```
ERROR: [Errno 10048] error while attempting to bind on address ...
```

Solusi:
```bash
# 1. Matikan proses yang memakai port 8000
netstat -ano | findstr :8000    # lihat PID
taskkill /F /PID 2744           # ganti dengan PID yang terlihat

# 2. Atau gunakan port lain
uv run uvicorn app.main:app --port 8080 --reload
```

### Database error (Oracle BP Batam)

```
[Errno 11001] getaddrinfo failed
```

Penyebab: Anda berada di luar jaringan BP Batam.
Solusi: Tidak perlu solusi — error ini sudah ditangani dengan pesan yang informatif. Fitur sekolah tetap berfungsi normal.

### Database error (SQLite/MySQL)

```
sqlalchemy.exc.OperationalError: no such table: students
```

Solusi: Jalankan migrasi database:
```bash
uv run python -m app.database.migrate
```

### Module not found

```
ModuleNotFoundError: No module named 'app'
```

Solusi: Pastikan Anda menjalankan perintah dari root project (`eduquery-ai/`), bukan dari subfolder.

### Ollama tidak merespons

```
Error: Ollama connection refused
```

Solusi:
- Pastikan Ollama sudah berjalan: `ollama serve`
- Atau nonaktifkan LLM fallback dengan mengosongkan `OLLAMA_HOST` di `.env`

### Virtual Environment tidak aktif

```
uv: command not found
```

Solusi:
```bash
# Install uv (Windows PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install uv (Mac/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Encoding error (Windows)

```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f6a8'
```

Solusi: Pastikan `.env` tidak menggunakan emoji. Sistem sudah dirancang untuk kompatibel dengan cp1252 (Windows).

---

## 10. Arsitektur Singkat

```
Pertanyaan (Web/API)
    │
    ▼
Intent Service
    │
    ├── Keyword Classifier → intent (fast path, tanpa LLM)
    └── Intent Extractor → intent via Ollama (fallback)
    │
    ▼
Pilih Database:
    ├── bp_ prefix → BP Batam (Oracle) → BPDatabaseService
    └── lainnya   → Database Sekolah (SQLite/MySQL) → DatabaseService
    │
    ▼
Generate SQL → Validasi SELECT → Eksekusi → Format → Response
```

### Alur Data BP Batam

1. User mengetik "Jumlah izin terbit"
2. Keyword classifier mencocokkan → intent `bp_izin_terbit_per_bulan`
3. Template SQL digenerate dengan filter dari parameter
4. SQL dikirim ke Oracle `US_DWH.BI_MART_STATUS_PERIZINAN`
5. Hasil diformat dalam bahasa alami
6. Ditampilkan di halaman dengan SQL + tabel + balasan

---

## 11. File Penting

| File | Fungsi |
|------|--------|
| `.env` | Konfigurasi environment |
| `prompts/intents.json` | Database intent (30 sekolah + 6 BP) |
| `app/core/config.py` | Pembaca konfigurasi dari `.env` |
| `app/main.py` | Entry point FastAPI |
| `app/database/bp_client.py` | Koneksi Oracle BP Batam |
| `app/database/client.py` | Koneksi database sekolah |
| `app/ai/keyword_classifier.py` | Deteksi intent cepat tanpa LLM |
| `app/services/bp_database_service.py` | Generate & eksekusi SQL BP |
| `static/index.html` | Frontend BP Batam |
| `static/sekolah.html` | Frontend sekolah |

---

## 12. Catatan untuk Developer

- **File-based intent**: Intent disimpan di `prompts/intents.json`, bisa diedit langsung atau via halaman `/intents`
- **Tambah intent BP**: Copy intent sekolah, ubah `source` jadi `"bp"`, prefix id dengan `bp_`
- **Format reply**: Edit `app/services/bp_formatter_service.py` untuk intent BP, `app/formatter/response.py` untuk sekolah
- **Tambah keyword**: Tambahkan pattern di `app/ai/keyword_classifier.py` (baris terbawah)
