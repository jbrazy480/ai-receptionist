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

RECOMMENDED = [
    ("PUBLIC_HOST", "Public hostname (ngrok/cloudflared) Twilio streams audio to"),
]


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
        status = "OK" if value else "MISSING"
        if not value:
            ok = False
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
        print("Some items are missing above. The offline simulator will still work without them:")
        print("  python -m receptionist.simulate")
        sys.exit(1)


if __name__ == "__main__":
    main()
