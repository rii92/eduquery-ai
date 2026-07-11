@echo off
set AUTH=admin:12345
set URL=http://192.168.200.177:8000/api/query

echo === bp_all_kpi_card ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"total izin bp batam\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_flow_permohonan ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"flow permohonan izin\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_tren_inflow_outflow ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"tren inflow outflow\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"filter_tahun\":\"TAHUN = '2026'\",\"filter_bulan\":\"BULAN = '01'\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_gauge_performa ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"performa penyelesaian\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_kepatuhan_sla ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"kepatuhan sla\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_funnel_kemacetan ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"funnel kemacetan\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_proporsi_kerja ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"proporsi kerja\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === bp_rapor_staf ===
curl -s -u %AUTH% -X POST %URL% -H "Content-Type: application/json" -d "{\"message\":\"rapor staf\",\"pilih_izin\":\"UPPER(JENIS_IZIN) = UPPER('PB')\",\"reply_provider\":\"deterministic\"}" | python -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {d[\"reply\"][:100]}...') if d.get('reply') else print(f'ERROR: {d}')"

echo === done ===
