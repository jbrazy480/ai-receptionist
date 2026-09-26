"""Bridge between a Twilio Media Stream WebSocket and the OpenAI Realtime GA API.

Protocol notes (see REFERENCE_twilio_openai_realtime_GA_main.py, not vendored here):
- Connect to wss://api.openai.com/v1/realtime?model=gpt-realtime
- session.update uses session.type "realtime", audio input/output format
  {"type": "audio/pcmu"}, and server_vad turn detection.
- Assistant audio arrives as response.output_audio.delta events (GA name, not
  the retired response.audio.delta).
- Barge-in: on input_audio_buffer.speech_started, send conversation.item.truncate
  for the in-flight assistant item and clear Twilio's playback buffer.
- Function calls arrive via response.function_call_arguments.done and are
  answered with conversation.item.create (type function_call_output) followed
  by response.create.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Optional, Protocol

from receptionist.config import BusinessConfig
from receptionist.hours import is_after_hours
from receptionist.logging_utils import CallLog
from receptionist.prompt import build_system_prompt
from receptionist.tools import TOOL_DEFINITIONS, ToolExecutor

logger = logging.getLogger("receptionist.bridge")

REALTIME_MODEL = "gpt-realtime"


class TwilioRestClient(Protocol):
    """Minimal shape of the twilio.rest.Client interface the bridge needs."""

    def calls(self, call_sid: str): ...  # pragma: no cover - protocol


def build_session_update(config: BusinessConfig, instructions: str) -> dict[str, Any]:
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"},
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": config.business.voice,
                },
            },
            "instructions": instructions,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
        },
    }


class MediaBridge:
    """Owns per-call state and event handling for one Twilio <-> OpenAI session."""

    def __init__(
        self,
        config: BusinessConfig,
        call_sid: str,
        from_number: Optional[str] = None,
        dry_run: bool = False,
        twilio_rest_client: Optional[TwilioRestClient] = None,
    ):
        self.config = config
        self.call_sid = call_sid
        self.dry_run = dry_run
        self.twilio_rest_client = twilio_rest_client
        self.tools = ToolExecutor(config, call_sid=call_sid, dry_run=dry_run)
        self.call_log = CallLog(call_sid, from_number)

        self.stream_sid: Optional[str] = None
        self.latest_media_timestamp = 0
        self.last_assistant_item: Optional[str] = None
        self.mark_queue: list[str] = []
        self.response_start_timestamp: Optional[int] = None
        self._pending_action: Optional[dict[str, Any]] = None
        self.should_close = False

        # Accumulate function_call arguments by call_id, since arguments may
        # arrive as deltas before the .done event carries the final string.
        self._pending_call_names: dict[str, str] = {}

    def instructions(self) -> str:
        return build_system_prompt(self.config)

    def session_update_event(self) -> dict[str, Any]:
        return build_session_update(self.config, self.instructions())

    def greeting_events(self) -> list[dict[str, Any]]:
        """Events that make the receptionist speak first when the call connects.

        With server_vad the model otherwise waits for the caller to talk, so we
        add a short instruction item and request a response right after the
        session.update.
        """
        return [
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "The caller just connected. Greet them now using the opening "
                                "greeting from your instructions (use the after-hours version "
                                "if the business is closed), then ask how you can help."
                            ),
                        }
                    ],
                },
            },
            {"type": "response.create"},
        ]

    # -- Twilio -> bridge -------------------------------------------------

    async def handle_twilio_message(self, raw_message: str, openai_send) -> None:
        data = json.loads(raw_message)
        event = data.get("event")
        if event == "media":
            self.latest_media_timestamp = int(data["media"]["timestamp"])
            await openai_send(
                json.dumps(
                    {
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    }
                )
            )
        elif event == "start":
            self.stream_sid = data["start"]["streamSid"]
            self.response_start_timestamp = None
            self.latest_media_timestamp = 0
            self.last_assistant_item = None
        elif event == "mark":
            if self.mark_queue:
                self.mark_queue.pop(0)

    # -- OpenAI -> bridge ---------------------------------------------------

    async def handle_openai_message(self, raw_message: str, openai_send, twilio_send) -> None:
        event = json.loads(raw_message)
        event_type = event.get("type")

        if event_type == "response.output_audio.delta" and "delta" in event:
            await self._forward_audio_delta(event, twilio_send)
        elif event_type == "input_audio_buffer.speech_started":
            await self._handle_speech_started(openai_send, twilio_send)
        elif event_type == "response.function_call_arguments.done":
            await self._handle_function_call_done(event, openai_send)
        elif event_type == "response.done":
            await self._handle_response_done(twilio_send)
        elif event_type == "error":
            logger.error("OpenAI realtime error: %s", event)

    async def _forward_audio_delta(self, event: dict[str, Any], twilio_send) -> None:
        audio_payload = event["delta"]
        await twilio_send(
            {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": audio_payload},
            }
        )

        item_id = event.get("item_id")
        if item_id and item_id != self.last_assistant_item:
            self.response_start_timestamp = self.latest_media_timestamp
            self.last_assistant_item = item_id

        await self._send_mark(twilio_send)

    async def _send_mark(self, twilio_send) -> None:
        if not self.stream_sid:
            return
        await twilio_send(
            {
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {"name": "responsePart"},
            }
        )
        self.mark_queue.append("responsePart")

    async def _handle_speech_started(self, openai_send, twilio_send) -> None:
        if self.mark_queue and self.response_start_timestamp is not None and self.last_assistant_item:
            elapsed_ms = self.latest_media_timestamp - self.response_start_timestamp
            await openai_send(
                json.dumps(
                    {
                        "type": "conversation.item.truncate",
                        "item_id": self.last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": max(elapsed_ms, 0),
                    }
                )
            )

        if self.stream_sid:
            await twilio_send({"event": "clear", "streamSid": self.stream_sid})

        self.mark_queue.clear()
        self.last_assistant_item = None
        self.response_start_timestamp = None

    async def _handle_function_call_done(self, event: dict[str, Any], openai_send) -> None:
        call_id = event["call_id"]
        name = event["name"]
        try:
            arguments = json.loads(event.get("arguments") or "{}")
        except json.JSONDecodeError:
            arguments = {}

        result = self.tools.dispatch(name, arguments)
        self.call_log.record_tool_call(name, arguments, result)

        pending_action = result.pop("pending_action", None) if isinstance(result, dict) else None
        if pending_action:
            self._pending_action = pending_action

        await openai_send(
            json.dumps(
                {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result),
                    },
                }
            )
        )
        await openai_send(json.dumps({"type": "response.create"}))

    async def _handle_response_done(self, twilio_send) -> None:
        if not self._pending_action:
            return
        action = self._pending_action
        self._pending_action = None

        if action["type"] == "hangup":
            await self._perform_hangup()
        elif action["type"] == "transfer":
            await self._perform_transfer(action)

    async def _perform_hangup(self) -> None:
        if self.dry_run or self.twilio_rest_client is None:
            self.should_close = True
            return
        from twilio.twiml.voice_response import VoiceResponse

        twiml = VoiceResponse()
        twiml.hangup()
        self.twilio_rest_client.calls(self.call_sid).update(twiml=str(twiml))
        self.should_close = True

    async def _perform_transfer(self, action: dict[str, Any]) -> None:
        if self.dry_run or self.twilio_rest_client is None:
            return
        from twilio.twiml.voice_response import Dial, VoiceResponse

        twiml = VoiceResponse()
        dial = Dial()
        dial.number(action["phone_number"])
        twiml.append(dial)
        self.twilio_rest_client.calls(self.call_sid).update(twiml=str(twiml))

    def is_after_hours(self) -> bool:
        return is_after_hours(self.config)

    def finish(self) -> dict[str, Any]:
        return self.call_log.end()
