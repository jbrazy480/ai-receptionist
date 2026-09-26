import shutil

import pytest
from fastapi.testclient import TestClient

from receptionist import twilio_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    shutil.copy("business.example.yaml", tmp_path / "business.yaml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VALIDATE_TWILIO_SIGNATURE", "false")
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    return TestClient(twilio_app.app)


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["business"] == "Sunrise Dental"


def test_health_config_error(client, tmp_path):
    (tmp_path / "business.yaml").unlink()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "config_error"


def test_voice_returns_connect_stream_twiml(client):
    response = client.post("/voice", data={"CallSid": "CA123", "From": "+15550001111"})
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    body = response.text
    assert "<Connect>" in body
    assert "<Stream" in body
    assert "wss://" in body
    assert "/media-stream" in body


def test_voice_with_missing_config_says_error_and_hangs_up(client, tmp_path):
    (tmp_path / "business.yaml").unlink()
    response = client.post("/voice", data={"CallSid": "CA123"})
    assert response.status_code == 200
    assert "<Hangup" in response.text
