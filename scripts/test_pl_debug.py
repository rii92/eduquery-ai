"""Debug PL filter on deployed server."""
import httpx

BASE = "http://172.18.32.172:8000"

# Test 1: Basic PL query via webhook
r = httpx.post(f"{BASE}/webhook/whatsapp", json={"sender": "debug_pl1", "message": "Berapa total izin PL?"}, timeout=120)
d = r.json()
print("=== PL query ===")
print(f"Reply: {d.get('reply', '')[:300]}")

# Test 2: PB query for comparison
r = httpx.post(f"{BASE}/webhook/whatsapp", json={"sender": "debug_pb1", "message": "Berapa total izin PB?"}, timeout=120)
d = r.json()
print("\n=== PB query ===")
print(f"Reply: {d.get('reply', '')[:300]}")

# Test 3: No filter (should return all)
r = httpx.post(f"{BASE}/webhook/whatsapp", json={"sender": "debug_all1", "message": "total izin BP batam"}, timeout=120)
d = r.json()
print("\n=== All permits (no filter) ===")
print(f"Reply: {d.get('reply', '')[:300]}")

# Test 4: PL with explicit year
r = httpx.post(f"{BASE}/webhook/whatsapp", json={"sender": "debug_pl2", "message": "total izin PL tahun 2026"}, timeout=120)
d = r.json()
print("\n=== PL 2026 ===")
print(f"Reply: {d.get('reply', '')[:300]}")
