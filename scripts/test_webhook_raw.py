import httpx
import json

BASE = "http://172.18.32.172:8000"
SESSION = "test_deploy_999"

r = httpx.post(
    f"{BASE}/webhook/whatsapp",
    json={"sender": "test1", "message": "total izin BP"},
    timeout=120,
)
print("Status:", r.status_code)
print("Body:", r.text[:500])
