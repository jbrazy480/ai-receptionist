"""Structured logging helpers: phone number masking and JSONL call/event logs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("receptionist")


def mask_phone(number: Optional[str]) -> str:
    """Mask a phone number for logs, keeping enough to distinguish callers.

    '+15551234567' -> '+1555***4567'
    """
    if not number:
        return "unknown"
    digits_and_plus = number
    if len(digits_and_plus) <= 6:
        return "*" * len(digits_and_plus)
    head = digits_and_plus[:5]
    tail = digits_and_plus[-4:]
    return f"{head}***{tail}"


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one JSON record as a line, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CallLog:
    """Accumulates one call's lifecycle and tool calls, then writes one JSONL line."""

    def __init__(self, call_sid: str, from_number: Optional[str], log_path: str | Path = "data/calls.jsonl"):
        self.call_sid = call_sid
        self.from_masked = mask_phone(from_number)
        self.log_path = log_path
        self.started_at = utc_now_iso()
        self.ended_at: Optional[str] = None
        self.tool_calls: list[dict[str, Any]] = []

    def record_tool_call(self, name: str, arguments: dict[str, Any], result: dict[str, Any]) -> None:
        self.tool_calls.append(
            {
                "name": name,
                "arguments": arguments,
                "result": result,
                "at": utc_now_iso(),
            }
        )

    def end(self) -> dict[str, Any]:
        self.ended_at = utc_now_iso()
        record = {
            "call_sid": self.call_sid,
            "from_masked": self.from_masked,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "tool_calls": self.tool_calls,
        }
        append_jsonl(self.log_path, record)
        return record
