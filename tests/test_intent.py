"""Unit test untuk ekstraksi intent BP Batam."""

from app.ai.keyword_classifier import classify_by_keyword


def test_bp_total_masuk():
    result = classify_by_keyword("Total masuk izin BP Batam")
    assert result["intent"] == "bp_total_masuk"


def test_bp_izin_terbit():
    result = classify_by_keyword("Jumlah izin yang sudah terbit")
    assert result["intent"] == "bp_izin_terbit_per_bulan"


def test_bp_backlog():
    result = classify_by_keyword("Berapa backlog perizinan?")
    assert result["intent"] == "bp_total_backlog_per_bulan"


def test_bp_dalam_proses():
    result = classify_by_keyword("Izin dalam proses BP Batam")
    assert result["intent"] == "bp_dalam_proses"


def test_bp_komposisi():
    result = classify_by_keyword("Komposisi status perizinan BP Batam")
    assert result["intent"] == "bp_komposisi_status"


def test_bp_sebaran():
    result = classify_by_keyword("Sebaran izin BP Batam")
    assert result["intent"] == "bp_sebaran_jenis_izin"


def test_greeting():
    result = classify_by_keyword("Halo")
    assert result["intent"] == "_greeting"


def test_unknown():
    result = classify_by_keyword("Apa kabar cuaca hari ini?")
    assert result is None