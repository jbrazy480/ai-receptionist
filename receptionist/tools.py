"""Realtime function tool implementations.

These are pure Python functions on top of the business config, JSONL storage,
and an optional webhook. They are used by both the live Twilio/OpenAI bridge
and the offline text simulator, so the same logic is exercised either way.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from receptionist.config import BusinessConfig
from receptionist.hours import business_hours_status, is_open_now
from receptionist.logging_utils import append_jsonl, utc_now_iso

# Tool definitions in OpenAI Realtime GA function-calling format
# (session.tools -> {"type": "function", "name", "description", "parameters"}).
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_business_hours",
        "description": "Look up whether the business is open now and its weekly hours.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "answer_faq",
        "description": "Look up an answer to a caller's question in the business FAQ list.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The caller's question."}
            },
            "required": ["question"],
        },
    },
    {
        "type": "function",
        "name": "take_message",
        "description": "Record a message from the caller for the business to follow up on.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "callback_number": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["name", "callback_number", "reason"],
        },
    },
    {
        "type": "function",
        "name": "transfer_call",
        "description": "Transfer the caller to a department. Only works while the business is open.",
        "parameters": {
            "type": "object",
            "properties": {"department": {"type": "string"}},
            "required": ["department"],
        },
    },
    {
        "type": "function",
        "name": "book_appointment",
        "description": "Book an appointment request for the caller.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "requested_time": {"type": "string"},
                "service": {"type": "string"},
            },
            "required": ["name", "phone", "requested_time", "service"],
        },
    },
    {
        "type": "function",
        "name": "end_call",
        "description": "End the call after saying goodbye.",
        "parameters": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": [],
        },
    },
]


def _word_set(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


class ToolExecutor:
    """Dispatches realtime function tool calls to concrete business logic.

    ``dry_run`` controls whether transfer_call/end_call perform any real Twilio
    REST action. In dry_run mode (used by the simulator and tests) they only
    report what they would do, via the ``pending_action`` field, which the
    live bridge acts on after the spoken handoff finishes.
    """

    def __init__(
        self,
        config: BusinessConfig,
        call_sid: str = "sim",
        dry_run: bool = True,
        webhook_client: Optional[httpx.Client] = None,
    ):
        self.config = config
        self.call_sid = call_sid
        self.dry_run = dry_run
        self._webhook_client = webhook_client

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = {
            "get_business_hours": self.get_business_hours,
            "answer_faq": self.answer_faq,
            "take_message": self.take_message,
            "transfer_call": self.transfer_call,
            "book_appointment": self.book_appointment,
            "end_call": self.end_call,
        }.get(name)
        if handler is None:
            return {"success": False, "message": f"Unknown tool: {name}"}
        return handler(**arguments)

    def get_business_hours(self) -> dict[str, Any]:
        return business_hours_status(self.config)

    def answer_faq(self, question: str) -> dict[str, Any]:
        question_words = _word_set(question)
        best_faq = None
        best_score = 0
        for faq in self.config.faqs:
            score = len(question_words & _word_set(faq.question))
            if score > best_score:
                best_score = score
                best_faq = faq
        if best_faq is not None and best_score > 0:
            return {"found": True, "question": best_faq.question, "answer": best_faq.answer}
        return {
            "found": False,
            "answer": None,
            "message": (
                "No matching FAQ found. Do not invent an answer; offer to take a "
                "message instead."
            ),
        }

    def take_message(self, name: str, callback_number: str, reason: str) -> dict[str, Any]:
        record = {
            "call_sid": self.call_sid,
            "name": name,
            "callback_number": callback_number,
            "reason": reason,
            "at": utc_now_iso(),
        }
        append_jsonl(self.config.messages.file_path, record)
        if self.config.messages.webhook_url:
            self._post_webhook(self.config.messages.webhook_url, record)
        return {
            "success": True,
            "message": f"Thanks {name}, we saved your message and will call you back.",
            "pending_action": None,
        }

    def book_appointment(
        self, name: str, phone: str, requested_time: str, service: str
    ) -> dict[str, Any]:
        record = {
            "call_sid": self.call_sid,
            "name": name,
            "phone": phone,
            "requested_time": requested_time,
            "service": service,
            "at": utc_now_iso(),
        }
        if self.config.booking.webhook_url:
            self._post_webhook(self.config.booking.webhook_url, record)
        else:
            append_jsonl("data/bookings.jsonl", record)
        return {
            "success": True,
            "message": (
                f"Thanks {name}, we have requested {service} at {requested_time}. "
                "We will confirm shortly."
            ),
            "pending_action": None,
        }

    def transfer_call(self, department: str) -> dict[str, Any]:
        if not is_open_now(self.config):
            return {
                "success": False,
                "message": (
                    "We're closed right now, so I can't transfer you. "
                    "I can take a message instead."
                ),
                "pending_action": None,
            }
        dept = self.config.department_by_name(department)
        if dept is None:
            names = ", ".join(d.name for d in self.config.departments) or "none configured"
            return {
                "success": False,
                "message": f"I don't have a department called '{department}'. Options: {names}.",
                "pending_action": None,
            }
        return {
            "success": True,
            "message": f"Transferring you to {dept.name} now.",
            "pending_action": {
                "type": "transfer",
                "department": dept.name,
                "phone_number": dept.phone_number,
                "dry_run": self.dry_run,
            },
        }

    def end_call(self, reason: str = "") -> dict[str, Any]:
        return {
            "success": True,
            "message": "Thanks for calling. Goodbye!",
            "pending_action": {"type": "hangup", "reason": reason, "dry_run": self.dry_run},
        }

    def _post_webhook(self, url: str, payload: dict[str, Any]) -> None:
        try:
            client = self._webhook_client or httpx
            client.post(url, json=payload, timeout=5.0)
        except httpx.HTTPError:
            pass
