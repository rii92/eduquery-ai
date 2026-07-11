import asyncio, json, sys
from app.services.bp_database_service import BPDatabaseService

srv = BPDatabaseService()

TEST_SUITE = [
    ("bp_all_kpi_card", "total izin bp batam", {}),
    ("bp_flow_permohonan", "flow permohonan izin", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_tren_inflow_outflow", "tren inflow outflow", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')", "filter_tahun": "TAHUN = '2026'", "filter_bulan": "BULAN = '01'"}),
    ("bp_gauge_performa", "performa penyelesaian", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_kepatuhan_sla", "kepatuhan sla", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_funnel_kemacetan", "funnel kemacetan", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
    ("bp_proporsi_kerja", "proporsi kerja", {}),
    ("bp_rapor_staf", "rapor staf", {"pilih_izin": "UPPER(JENIS_IZIN) = UPPER('PB')"}),
]

for intent_id, question, params in TEST_SUITE:
    payload = {"intent": intent_id, **params}
    try:
        sql = srv.generate_sql(payload)
        valid = srv.validate_sql(sql) if sql else False
        if not sql:
            print(f"FAIL {intent_id}: no SQL generated")
            continue
        if not valid:
            print(f"FAIL {intent_id}: SQL invalid")
            continue
        result = srv.execute(sql)
        if result:
            row_count = len(result)
            first = {k: str(v)[:60] for k, v in result[0].items()}
            print(f"OK   {intent_id}: {row_count} rows | {json.dumps(first, ensure_ascii=False)}")
        else:
            print(f"EMPTY {intent_id}: 0 rows returned")
    except Exception as e:
        print(f"ERROR {intent_id}: {e}")
