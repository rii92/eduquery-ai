"""Executive Summary — seluruh query untuk sub-menu Executive Summary BP Batam.

Setiap query menggunakan placeholder {{param}} yang akan di-replace
dengan nilai filter saat eksekusi.
"""

_QUERY_RAW = {
    "all_kpi_card": {
        "label": "Ringkasan KPI Card",
        "sql": """\
SELECT 
    COUNT(NO_PERMOHONAN) AS TOTAL_DOKUMEN,
    COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'TERBIT' THEN 1 ELSE 0 END), 0) AS TOTAL_TERBIT,
    COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'TOLAK' THEN 1 ELSE 0 END), 0) AS TOTAL_TOLAK,
    COALESCE(SUM(CASE WHEN KATEGORI_STATUS = 'DALAM PROSES' THEN 1 ELSE 0 END), 0) AS TOTAL_DALAM_PROSES,
    COALESCE(SUM(CASE WHEN KATEGORI_STATUS IN ('PROSES PELAKU USAHA', 'CABUT') THEN 1 ELSE 0 END), 0) AS TOTAL_LAINNYA,
    COALESCE(SUM(
        CASE 
            WHEN UPPER(JENIS_IZIN) != 'LALIN' AND KATEGORI_STATUS = 'DALAM PROSES' AND STATUS_PENCAPAIAN_SLA = 'LEWAT SLA' THEN 1 
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
WHERE 1=1
  AND {{tgl_status_terakhir}}
  AND {{perizinan}}
  AND {{kategori_status}}
  AND {{tahun}}
  AND {{bulan}}""",
        "params": {
            "tgl_status_terakhir": "Filter tanggal",
            "perizinan": "Filter jenis izin",
            "kategori_status": "Filter status",
            "tahun": "Filter tahun",
            "bulan": "Filter bulan",
        },
    },
}


def _build_queries() -> dict:
    out = {}
    for qid, meta in _QUERY_RAW.items():
        out[qid] = {"label": meta["label"], "sql": meta["sql"], "params": dict(meta["params"])}
    return out


QUERIES = _build_queries()


def get_query(query_id: str) -> dict | None:
    return QUERIES.get(query_id)


def list_queries() -> list[dict]:
    return [
        {"id": qid, "label": meta["label"], "params": list(meta["params"].keys())}
        for qid, meta in QUERIES.items()
    ]
