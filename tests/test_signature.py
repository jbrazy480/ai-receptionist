import shutil

import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from receptionist import twilio_app

AUTH_TOKEN = "test_auth_token_1234567890"


@pytest.fixture
def client(tmp_path, monkeypatch):
    shutil.copy("business.example.yaml", tmp_path / "business.yaml")
    monkeypatch.chdir(tmp_path)
    return TestClient(twilio_app.app)


def test_signature_required_when_enabled_and_token_set(client, monkeypatch):
    monkeypatch.setenv("VALIDATE_TWILIO_SIGNATURE", "true")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)

    response = client.post("/voice", data={"CallSid": "CA123"})
    assert response.status_code == 403


def test_signature_accepted_when_valid(client, monkeypatch):
    monkeypatch.setenv("VALIDATE_TWILIO_SIGNATURE", "true")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)

    url = "http://testserver/voice"
    params = {"CallSid": "CA123"}
    validator = RequestValidator(AUTH_TOKEN)
    signature = validator.compute_signature(url, params)

    response = client.post("/voice", data=params, headers={"X-Twilio-Signature": signature})
    assert response.status_code == 200
    assert "<Connect>" in response.text


def test_signature_skipped_when_disabled(client, monkeypatch):
    monkeypatch.setenv("VALIDATE_TWILIO_SIGNATURE", "false")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)

    response = client.post("/voice", data={"CallSid": "CA123"})
    assert response.status_code == 200


def test_signature_skipped_when_no_token_configured(client, monkeypatch):
    monkeypatch.setenv("VALIDATE_TWILIO_SIGNATURE", "true")
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)

    response = client.post("/voice", data={"CallSid": "CA123"})
    assert response.status_code == 200
