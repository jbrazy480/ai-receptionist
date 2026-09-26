"""Deterministic, rule-based conversational brain for the offline text simulator.

This is NOT an LLM. It is a small slot-filling state machine that routes caller
text to the same ToolExecutor used by the live realtime bridge, so the offline
demo exercises real business logic (FAQ lookup, hours, messages, bookings,
transfers) without any API keys or network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from receptionist.config import BusinessConfig
from receptionist.tools import ToolExecutor

_BOOKING_SLOTS = ["name", "phone", "requested_time", "service"]
_MESSAGE_SLOTS = ["name", "callback_number", "reason"]

_SLOT_PROMPTS = {
    "name": "Can I get your name?",
    "phone": "What's a good phone number to reach you?",
    "callback_number": "What's a good callback number?",
    "reason": "What's this regarding?",
    "requested_time": "What day and time would you like?",
    "service": "What service is this for?",
    "department": "Which department would you like: {options}?",
}


@dataclass
class Brain:
    executor: ToolExecutor
    config: BusinessConfig
    done: bool = False
    _pending_intent: Optional[str] = None
    _pending_slots: list[str] = field(default_factory=list)
    _collected: dict = field(default_factory=dict)
    _awaiting_message_offer: bool = False

    def greeting(self) -> str:
        return self.config.business.greeting

    def respond(self, user_text: str) -> str:
        text = user_text.strip().lower()

        if self._pending_intent:
            return self._continue_pending(user_text)

        if self._awaiting_message_offer:
            self._awaiting_message_offer = False
            if text in {"yes", "y", "sure", "yeah", "please"}:
                return self._start_intent("take_message", _MESSAGE_SLOTS)
            return "No problem. Is there anything else I can help with?"

        if any(word in text for word in ("bye", "goodbye", "that's all", "nothing else", "no thanks")):
            result = self.executor.dispatch("end_call", {"reason": "caller finished"})
            self.done = True
            return result["message"]

        if "hour" in text or "open" in text or "closed" in text:
            result = self.executor.dispatch("get_business_hours", {})
            if result["open_now"]:
                return f"We're open right now. Today's hours: {result['today']}."
            return f"We're currently closed. Today's hours: {result['today']}."

        if "appointment" in text or "book" in text or "schedule" in text:
            return self._start_intent("book_appointment", list(_BOOKING_SLOTS))

        if "transfer" in text or self._matches_department(text):
            department = self._matches_department(text)
            if department:
                return self._dispatch_transfer(department)
            return self._start_intent("transfer_call", ["department"])

        if "message" in text or "call me back" in text or "leave a" in text:
            return self._start_intent("take_message", list(_MESSAGE_SLOTS))

        faq_result = self.executor.dispatch("answer_faq", {"question": user_text})
        if faq_result["found"]:
            return faq_result["answer"]

        self._awaiting_message_offer = True
        return "I'm not sure about that, and I don't want to guess. Would you like me to take a message?"

    def _matches_department(self, text: str) -> Optional[str]:
        for dept in self.config.departments:
            if dept.name.lower() in text:
                return dept.name
        return None

    def _start_intent(self, intent: str, slots: list[str]) -> str:
        self._pending_intent = intent
        self._pending_slots = slots
        self._collected = {}
        return self._ask_next_slot()

    def _ask_next_slot(self) -> str:
        slot = self._pending_slots[0]
        if slot == "department":
            options = ", ".join(d.name for d in self.config.departments) or "none available"
            return _SLOT_PROMPTS["department"].format(options=options)
        return _SLOT_PROMPTS[slot]

    def _continue_pending(self, user_text: str) -> str:
        slot = self._pending_slots.pop(0)
        self._collected[slot] = user_text.strip()

        if self._pending_slots:
            return self._ask_next_slot()

        intent = self._pending_intent
        self._pending_intent = None

        if intent == "transfer_call":
            return self._dispatch_transfer(self._collected["department"])

        result = self.executor.dispatch(intent, self._collected)
        return result["message"]

    def _dispatch_transfer(self, department: str) -> str:
        result = self.executor.dispatch("transfer_call", {"department": department})
        return result["message"]
