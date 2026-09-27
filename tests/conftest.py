import copy

import dotenv
import pytest

from receptionist import check
from receptionist.config import BusinessConfig


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    """Keep developer credentials and local .env files out of every test."""
    def skip_dotenv(*args, **kwargs):
        return False

    monkeypatch.setattr(dotenv, "load_dotenv", skip_dotenv)
    # Patch each application's imported binding, not just the dotenv source.
    monkeypatch.setattr(check, "load_dotenv", skip_dotenv)
    for name in (
        "OPENAI_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "PUBLIC_HOST",
        "PUBLIC_BASE_URL",
        "PUBLIC_URL",
        "VALIDATE_TWILIO_SIGNATURE",
        "BUSINESS_CONFIG_PATH",
        "PORT",
        "LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)


RAW_CONFIG = {
    "business": {
        "name": "Sunrise Dental",
        "timezone": "America/New_York",
        "greeting": "Thanks for calling Sunrise Dental!",
        "after_hours_message": "We're closed. Leave a message.",
        "voice": "alloy",
    },
    "hours": {
        "monday": {"open": "09:00", "close": "17:00"},
        "tuesday": {"open": "09:00", "close": "17:00"},
        "wednesday": {"open": "09:00", "close": "17:00"},
        "thursday": {"open": "09:00", "close": "17:00"},
        "friday": {"open": "09:00", "close": "15:00"},
        "saturday": None,
        "sunday": None,
    },
    "faqs": [
        {"question": "Do you accept walk-ins?", "answer": "Yes, when we have availability."},
        {"question": "Do you take insurance?", "answer": "We accept most PPO plans."},
    ],
    "departments": [
        {"name": "Billing", "phone_number": "+15551234567"},
        {"name": "Scheduling", "phone_number": "+15551234568"},
    ],
    "booking": {"webhook_url": None},
    "messages": {"file_path": "data/messages.jsonl", "webhook_url": None},
}


@pytest.fixture
def raw_config() -> dict:
    return copy.deepcopy(RAW_CONFIG)


@pytest.fixture
def sample_config(raw_config) -> BusinessConfig:
    return BusinessConfig.model_validate(raw_config)


@pytest.fixture
def sample_config_with_paths(raw_config, tmp_path) -> BusinessConfig:
    raw_config["messages"]["file_path"] = str(tmp_path / "messages.jsonl")
    return BusinessConfig.model_validate(raw_config)
