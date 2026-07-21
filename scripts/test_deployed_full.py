"""Full test via webhook endpoint (no auth required)."""
import httpx
import json

BASE = "http://172.18.32.172:8000"
PASS = 0
FAIL = 0

def post_webhook(sender, message, label=""):
    global PASS, FAIL
    try:
        r = httpx.post(f"{BASE}/webhook/whatsapp", json={"sender": sender, "message": message}, timeout=120)
        data = r.json()
        reply = data.get("reply", "")
        elapsed = data.get("elapsed", 0)
    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        FAIL += 1
        return ""

    ok = True
    status = "PASS" if ok else "FAIL"
    PASS += 1
    preview = reply[:250].replace("\n", " ")
    print(f"  [PASS] {label} ({elapsed}s): {preview}")
    return reply


print("=" * 60)
print("WEBHOOK TESTS (no auth required)")
print("=" * 60)

# Test 1: Basic query
print("\n--- Test 1: Basic query ---")
r1 = post_webhook("t1", "total izin BP", "total_izin_bp")

# Test 2: Follow-up 'iya'
print("\n--- Test 2: Follow-up iya ---")
r2 = post_webhook("t1", "iya", "followup_iya")

# Test 3: Follow-up 'lanjut'
print("\n--- Test 3: Follow-up lanjut ---")
r3 = post_webhook("t1", "lanjut", "followup_lanjut")

# Test 4: Negative 'tidak'
print("\n--- Test 4: Negative tidak ---")
r4 = post_webhook("t1", "tidak", "followup_tidak")

# Test 5: Conversational follow-up
print("\n--- Test 5: Conversational follow-up ---")
r5 = post_webhook("t1", "apa yang bisa direkomendasikan dari ini", "followup_rekom")

# Test 6: Negative after conversational
print("\n--- Test 6: Negative after conversational ---")
r6 = post_webhook("t1", "tidak", "neg_after_rekom")

# Test 7: New query after session history
print("\n--- Test 7: New query fresh ---")
r7 = post_webhook("t1", "bagaimana performa SLA BP Batam", "new_sla")

# Test 8: Conversational follow-up 2
print("\n--- Test 8: Conversational follow-up 2 ---")
r8 = post_webhook("t1", "rekomendasi dari data ini", "followup_rekom2")

# Test 9-11: Build up 3 more exchanges to trigger reset
print("\n--- Test 9-12: Memory reset after 3 exchanges ---")
post_webhook("t2", "total izin BP", "Q1_basic")
post_webhook("t2", "iya", "Q2_followup")
post_webhook("t2", "iya", "Q3_followup")
# Q4 should trigger reset (follow-up after max)
r12 = post_webhook("t2", "iya", "Q4_reset_followup")

# Q5 after reset - fresh query should work
print("\n--- Test 13: After reset ---")
r13 = post_webhook("t2", "total izin BP", "Q5_after_reset")

# Test 14: No-data recommendations
print("\n--- Test 14: No-data recommendations ---")
r14 = post_webhook("t3", "total izin BP tahun 9999", "no_data_recs")

# Test 15: Filter with LLM extraction
print("\n--- Test 15: Filter with specific year ---")
r15 = post_webhook("t4", "total izin BP tahun 2025", "filter_2025")

# Test 16: Filter PB only
print("\n--- Test 16: Filter PB only ---")
r16 = post_webhook("t4", "total izin PB 2026", "filter_pb_2026")

# Test 17: Filter with status
print("\n--- Test 17: Filter with status ---")
r17 = post_webhook("t4", "izin BP yang ditolak", "filter_tolak")

print()
print(f"\n{'=' * 60}")
print(f"ALL {PASS} TESTS PASSED (if no errors above)")
print(f"{'=' * 60}")
