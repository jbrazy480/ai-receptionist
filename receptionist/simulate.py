"""Offline text simulator: the 60-second, zero-keys demo.

Run with:
    python -m receptionist.simulate            # scripted demo
    python -m receptionist.simulate --interactive

No network access and no API keys are used. The conversation is driven by a
small rule-based Brain (receptionist.brain) that calls the exact same
ToolExecutor used by the live Twilio/OpenAI bridge.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from receptionist.brain import Brain
from receptionist.config import ConfigError, load_config
from receptionist.tools import ToolExecutor

DEFAULT_CONFIG_PATH = "business.yaml"
EXAMPLE_CONFIG_PATH = "business.example.yaml"

SCRIPT = [
    "What are your hours?",
    "Do you accept walk-ins?",
    "I'd like to book an appointment",
    "Jamie Rivera",
    "555-010-2020",
    "next Tuesday at 2pm",
    "teeth cleaning",
    "That's all, goodbye",
]


def resolve_config_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    if Path(DEFAULT_CONFIG_PATH).exists():
        return DEFAULT_CONFIG_PATH
    if Path(EXAMPLE_CONFIG_PATH).exists():
        print(
            f"(no {DEFAULT_CONFIG_PATH} found, using {EXAMPLE_CONFIG_PATH} for this demo)\n"
        )
        return EXAMPLE_CONFIG_PATH
    return DEFAULT_CONFIG_PATH


def run(config_path: str, interactive: bool, lines: list[str] | None = None) -> None:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(f"Configuration error:\n{exc}", file=sys.stderr)
        sys.exit(1)

    executor = ToolExecutor(config, call_sid="simulator", dry_run=True)
    brain = Brain(executor=executor, config=config)

    print(f"AI Receptionist for {config.business.name} (offline simulator, no API keys used)")
    print("-" * 60)
    print(f"Receptionist: {brain.greeting()}")

    if interactive:
        while not brain.done:
            try:
                caller_text = input("You: ")
            except EOFError:
                break
            if not caller_text.strip():
                continue
            reply = brain.respond(caller_text)
            print(f"Receptionist: {reply}")
        return

    script = lines if lines is not None else SCRIPT
    for caller_text in script:
        print(f"You: {caller_text}")
        reply = brain.respond(caller_text)
        print(f"Receptionist: {reply}")
        if brain.done:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline AI receptionist text simulator")
    parser.add_argument("--config", default=None, help="Path to business.yaml")
    parser.add_argument(
        "--interactive", action="store_true", help="Type your own messages instead of the demo script"
    )
    args = parser.parse_args()

    config_path = resolve_config_path(args.config)
    run(config_path, interactive=args.interactive)


if __name__ == "__main__":
    main()
