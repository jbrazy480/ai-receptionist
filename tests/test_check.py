import pytest

from receptionist import check


def _clear_live_call_env(monkeypatch):
    for var, _ in check.REQUIRED_FOR_LIVE_CALLS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("PUBLIC_HOST", raising=False)
    monkeypatch.setenv("BUSINESS_CONFIG_PATH", "business.example.yaml")


def test_missing_keys_exit_nonzero_and_report_missing(monkeypatch, capsys):
    _clear_live_call_env(monkeypatch)

    with pytest.raises(SystemExit) as exc_info:
        check.main()

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "[MISSING] OPENAI_API_KEY" in out
    assert check.GET_YOUR_KEYS_DOC in out


def test_placeholder_values_are_not_reported_as_ok(monkeypatch, capsys):
    _clear_live_call_env(monkeypatch)
    for var, placeholder in check.PLACEHOLDER_VALUES.items():
        monkeypatch.setenv(var, placeholder)

    with pytest.raises(SystemExit):
        check.main()

    out = capsys.readouterr().out
    assert "[PLACEHOLDER] OPENAI_API_KEY" in out
    assert "[PLACEHOLDER] TWILIO_ACCOUNT_SID" in out
    assert "[PLACEHOLDER] TWILIO_AUTH_TOKEN" in out
    assert "[OK] OPENAI_API_KEY" not in out


def test_real_looking_values_pass(monkeypatch, capsys):
    _clear_live_call_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-value")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACrealvalue")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "realtoken")

    check.main()

    out = capsys.readouterr().out
    assert "[OK] OPENAI_API_KEY" in out
    assert "[OK] TWILIO_ACCOUNT_SID" in out
    assert "[OK] TWILIO_AUTH_TOKEN" in out
    assert "Everything needed for live calls looks present." in out
