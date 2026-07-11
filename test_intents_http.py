import json, urllib.request, base64, sys

URL = "http://192.168.200.177:8000/api/query"
AUTH = base64.b64encode(b"admin:12345").decode()

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

TESTS = [
    ("bp_all_kpi_card", {"message": "total izin bp batam"}),
    ("bp_flow_permohonan", {"message": "flow permohonan", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_tren_inflow_outflow", {"message": "tren inflow outflow", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')", "filter_tahun": "TAHUN = '2026'", "filter_bulan": "BULAN = '01'"}),
    ("bp_gauge_performa", {"message": "performa penyelesaian", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_kepatuhan_sla", {"message": "kepatuhan sla", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_funnel_kemacetan", {"message": "funnel kemacetan", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_proporsi_kerja", {"message": "proporsi kerja"}),
    ("bp_rapor_staf", {"message": "rapor staf", "pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
]

for intent_id, params in TESTS:
    body = json.dumps({**params, "reply_provider": "deterministic"}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Basic {AUTH}",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        reply = data.get("reply", "")
        intent = data.get("intent", "?")
        if reply and reply != "Maaf, pertanyaan tersebut belum didukung sistem.":
            print(f"OK     {intent_id} (matched={intent}) → {reply[:150]}")
        else:
            print(f"FAILED {intent_id} (matched={intent}) → {reply[:200]}")
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"HTTP   {intent_id}: {e.code}")
    except Exception as e:
        print(f"ERROR  {intent_id}: {e}")
