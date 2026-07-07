"""Executive Summary — seluruh query untuk sub-menu Executive Summary BP Batam.

Setiap query menggunakan placeholder {{param}} yang akan di-replace
dengan nilai filter saat eksekusi.
"""

_PERMIT_TYPES = "'PB', 'PBUMKU', 'PL', 'PKKPRL', 'PPKH'"

_QUERY_RAW = {
    "semua_kpi_card": {
        "label": "all_KPI CARD",
        "sql": """\
        SELECT 
            -- 1. Total Seluruh Permohonan
            COUNT(NO_PERMOHONAN) AS TOTAL_DOKUMEN,
            
            -- 2. Total Terbit
            COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'TERBIT' THEN 1 ELSE 0 END), 0) AS TOTAL_TERBIT,
            
            -- 3. Total Ditolak
            COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'TOLAK' THEN 1 ELSE 0 END), 0) AS TOTAL_TOLAK,
            
            -- 4. Total Dalam Proses (Sistem / Verifikator)
            COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'DALAM PROSES' THEN 1 ELSE 0 END), 0) AS TOTAL_DALAM_PROSES,
            
            -- 5. Total Lainnya (Proses Pelaku Usaha untuk PB/PD & Cabut untuk Lalin)
            COALESCE(SUM(CASE WHEN KATEGORI_STATUS IN ('PROSES PELAKU USAHA', 'CABUT') THEN 1 ELSE 0 END), 0) AS TOTAL_LAINNYA,
            
            -- 6. Total Overdue (Statusnya masih proses, tapi SLA sudah lewat)
            COALESCE(SUM(
                CASE 
                    -- A. Logika Overdue Standar (Memperbaiki Typo menjadi 'LEWAT SLA')
                    WHEN UPPER(JENIS_IZIN) != 'LALIN' AND KATEGORI_STATUS = 'DALAM PROSES' AND STATUS_PENCAPAIAN_SLA = 'LEWAT SLA' THEN 1 
                    
                    -- B. Logika Overdue Real-time KHUSUS LALIN (Diadopsi dari kueri OSS)
                    WHEN UPPER(JENIS_IZIN) = 'LALIN' AND KATEGORI_STATUS = 'DALAM PROSES' AND (
                        SYSDATE - 
                        CASE 
                            WHEN (CAST(TGL_BAYAR_LALIN AS DATE) - TRUNC(CAST(TGL_BAYAR_LALIN AS DATE))) > (16.5 / 24) 
                                THEN TRUNC(CAST(TGL_BAYAR_LALIN AS DATE)) + 1 + (8 / 24)
                            WHEN (CAST(TGL_BAYAR_LALIN AS DATE) - TRUNC(CAST(TGL_BAYAR_LALIN AS DATE))) < (8 / 24) 
                                THEN TRUNC(CAST(TGL_BAYAR_LALIN AS DATE)) + (8 / 24)
                            ELSE CAST(TGL_BAYAR_LALIN AS DATE)
                        END
                    ) * 24 > 24 THEN 1
                    
                    ELSE 0 
                END
            ), 0) AS TOTAL_OVERDUE

        FROM US_DWH.BI_T_ALL
        WHERE 1=1""",
    },
}


def _build_queries() -> dict:
    out = {}
    for qid, meta in _QUERY_RAW.items():
        sql = meta["sql"].replace("{{PERMIT_TYPES}}", _PERMIT_TYPES)
        out[qid] = {"label": meta["label"], "sql": sql, "params": dict(meta["params"])}
    return out


QUERIES = _build_queries()


def get_query(query_id: str) -> dict | None:
    return QUERIES.get(query_id)


def list_queries() -> list[dict]:
    return [
        {"id": qid, "label": meta["label"], "params": list(meta["params"].keys())}
        for qid, meta in QUERIES.items()
    ]
