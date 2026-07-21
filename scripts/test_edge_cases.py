import json, urllib.request, base64, time

BASE = "http://172.18.32.172:8000"
AUTH = base64.b64encode(b"admin:12345").decode()

def send(msg, session=None):
    body = json.dumps({"message": msg, "session_id": session or ""}).encode()
    req = urllib.request.Request(
        BASE + "/api/query", data=body,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

SID = f"edge_{int(time.time())}"

print("=== EDGE CASE 1: Empty session_id (auto-generate) ===")
r = send("total izin bp batam tahun 2025")
sid = r.get("session_id", "NONE")
print(f"  session_id: {sid}")
print(f"  Intent: {r['intent']}")
print(f"  Reply: {r['reply'][:80]}...")
assert sid and sid != "NONE", "session_id should not be empty"

print("\n=== EDGE CASE 2: Follow-up with auto-generated session ===")
r2 = send("iya", session=sid)
print(f"  Intent: {r2.get('intent', 'NONE')} (should= bp_all_kpi_card)")
print(f"  Reply: {r2['reply'][:80]}...")

print("\n=== EDGE CASE 3: Follow-up without history (fresh session) ===")
r3 = send("iya", session="fresh_session_no_history")
print(f"  Intent: {r3.get('intent', 'NONE')} (should be empty)")
print(f"  Reply: {r3['reply'][:80]}... (should be LLM fallback or error)")

print("\n=== EDGE CASE 4: Multiple follow-ups in a row ===")
s = f"multi_{int(time.time())}"
r = send("total izin bp batam tahun 2025", session=s)
print(f"  [1] Intent: {r['intent']} | Reply: {r['reply'][:60]}...")
r = send("iya", session=s)
print(f"  [2] Intent: {r.get('intent','?')} | Reply: {r['reply'][:60]}...")
r = send("lanjut", session=s)
print(f"  [3] Intent: {r.get('intent','?')} | Reply: {r['reply'][:60]}...")
# 4th follow-up should still work (history kept at 3)
r = send("ya", session=s)
print(f"  [4] Intent: {r.get('intent','?')} | Reply: {r['reply'][:60]}...")

print("\n=== EDGE CASE 5: New question after follow-up, then follow-up again ===")
s2 = f"newq_{int(time.time())}"
r = send("total izin bp batam tahun 2025", session=s2)
print(f"  [1] {r['intent']}: {r['reply'][:60]}...")
r = send("iya", session=s2)
print(f"  [2] follow-up: {r['reply'][:60]}...")
r = send("kpi oss", session=s2)
print(f"  [3] new q (oss): {r.get('intent','?')} | {r['reply'][:60]}...")
r = send("iya", session=s2)
print(f"  [4] follow-up after oss: {r.get('intent','?')} | {r['reply'][:60]}...")

print("\n=== EDGE CASE 6: Negative follow-up at different stages ===")
s3 = f"neg_{int(time.time())}"
r = send("total izin bp batam tahun 2025", session=s3)
print(f"  [1] {r['intent']}")
r = send("tidak", session=s3)
print(f"  [2] Reply: {r['reply'][:80]}...")
# After "tidak", session continues - next query should work fresh
r = send("total izin PL bp batam", session=s3)
print(f"  [3] after tidak: {r.get('intent','?')} | {r['reply'][:60]}... (should be PL data)")

print("\n=== ALL EDGE CASE TESTS COMPLETE ===")
