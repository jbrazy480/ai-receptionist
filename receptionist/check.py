"""Doctor / smoke command: validates config and env vars for live calls.

Run with: python -m receptionist.check
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from receptionist.config import ConfigError, load_config

DEFAULT_CONFIG_PATH = "business.yaml"

REQUIRED_FOR_LIVE_CALLS = [
    ("OPENAI_API_KEY", "OpenAI Realtime API key"),
    ("TWILIO_ACCOUNT_SID", "Twilio account SID"),
    ("TWILIO_AUTH_TOKEN", "Twilio auth token, also used for webhook signature validation"),
]

# Exact placeholder values shipped in .env.example. A user who runs
# `cp .env.example .env` without editing it should not see [OK].
PLACEHOLDER_VALUES = {
    "OPENAI_API_KEY": "sk-placeholder",
    "TWILIO_ACCOUNT_SID": "ACplaceholder",
    "TWILIO_AUTH_TOKEN": "placeholder",
}

RECOMMENDED = [
    ("PUBLIC_HOST", "Public hostname (ngrok/cloudflared) Twilio streams audio to"),
]

GET_YOUR_KEYS_DOC = "docs/GET_YOUR_KEYS.md"


def main() -> None:
    load_dotenv()
    config_path = os.getenv("BUSINESS_CONFIG_PATH", DEFAULT_CONFIG_PATH)

    print("AI Receptionist doctor check")
    print("-" * 60)

    ok = True

    print(f"Config file: {config_path}")
    try:
        config = load_config(config_path)
        print(f"  OK: business.yaml loaded for '{config.business.name}'")
        print(f"  Departments configured: {len(config.departments)}")
        print(f"  FAQs configured: {len(config.faqs)}")
    except ConfigError as exc:
        ok = False
        print(f"  FAIL: {exc}")

    print()
    print("Environment variables required for live phone calls:")
    for var, description in REQUIRED_FOR_LIVE_CALLS:
        value = os.getenv(var)
        if not value:
            status = "MISSING"
            ok = False
        elif value == PLACEHOLDER_VALUES.get(var):
            status = "PLACEHOLDER"
            ok = False
        else:
            status = "OK"
        print(f"  [{status}] {var}: {description}")

    print()
    print("Recommended:")
    for var, description in RECOMMENDED:
        value = os.getenv(var)
        status = "set" if value else "not set"
        print(f"  [{status}] {var}: {description}")

    validate_sig = os.getenv("VALIDATE_TWILIO_SIGNATURE", "true").lower() != "false"
    print()
    print(f"Twilio signature validation: {'enabled' if validate_sig else 'disabled (dev mode)'}")

    print()
    if ok:
        print("Everything needed for live calls looks present.")
    else:
        print("Some items are missing or still set to placeholder values above.")
        print(f"See {GET_YOUR_KEYS_DOC} for step by step help getting real values.")
        print("The offline simulator will still work without them:")
        print("  python -m receptionist.simulate")
        sys.exit(1)


if __name__ == "__main__":
    main()
