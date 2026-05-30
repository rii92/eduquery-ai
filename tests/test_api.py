"""Integration test for the /webhook/whatsapp endpoint."""
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.services.bp_database_service.BPClient.execute")
def test_webhook_known_intent(mock_execute):
    mock_execute.side_effect = Exception("getaddrinfo failed")
    resp = client.post("/webhook/whatsapp", json={
        "sender": "628123456789",
        "message": "Jumlah izin yang sudah terbit"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "ERROR" in data["reply"]


def test_webhook_unknown_intent():
    resp = client.post("/webhook/whatsapp", json={
        "sender": "628123456789",
        "message": "Hapus semua siswa"
    })
    assert resp.status_code == 200
    assert isinstance(resp.json()["reply"], str)