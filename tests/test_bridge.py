import base64
import json

import pytest

import receptionist.tools as tools_module
from receptionist.realtime_bridge import MediaBridge, build_session_update


class Recorder:
    """Captures async send calls for assertions."""

    def __init__(self):
        self.calls = []

    async def __call__(self, payload):
        self.calls.append(payload)


class FakeCallsResource:
    def __init__(self, recorder):
        self._recorder = recorder

    def update(self, twiml):
        self._recorder.append(twiml)


class FakeTwilioRestClient:
    def __init__(self):
        self.updates = []

    def calls(self, call_sid):
        return FakeCallsResource(self.updates)


def make_bridge(sample_config, **kwargs):
    return MediaBridge(sample_config, call_sid="CA_TEST", from_number="+15550001111", **kwargs)


def test_session_update_uses_ga_protocol(sample_config):
    event = build_session_update(sample_config, "instructions text")
    assert event["type"] == "session.update"
    session = event["session"]
    assert session["type"] == "realtime"
    assert session["model"] == "gpt-realtime"
    assert session["audio"]["input"]["format"] == {"type": "audio/pcmu"}
    assert session["audio"]["input"]["turn_detection"] == {"type": "server_vad"}
    assert session["audio"]["output"]["format"] == {"type": "audio/pcmu"}
    assert session["audio"]["output"]["voice"] == sample_config.business.voice
    tool_names = {tool["name"] for tool in session["tools"]}
    assert "transfer_call" in tool_names


@pytest.mark.asyncio
async def test_twilio_start_sets_stream_sid(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    openai_send = Recorder()

    start_message = json.dumps({"event": "start", "start": {"streamSid": "MZ123"}})
    await bridge.handle_twilio_message(start_message, openai_send)

    assert bridge.stream_sid == "MZ123"


@pytest.mark.asyncio
async def test_twilio_media_forwarded_to_openai(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    openai_send = Recorder()

    media_message = json.dumps(
        {"event": "media", "media": {"timestamp": "500", "payload": "abc123=="}}
    )
    await bridge.handle_twilio_message(media_message, openai_send)

    assert bridge.latest_media_timestamp == 500
    assert len(openai_send.calls) == 1
    sent = json.loads(openai_send.calls[0])
    assert sent["type"] == "input_audio_buffer.append"
    assert sent["audio"] == "abc123=="


@pytest.mark.asyncio
async def test_audio_delta_forwarded_to_twilio(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    bridge.stream_sid = "MZ123"
    openai_send = Recorder()
    twilio_send = Recorder()

    payload = base64.b64encode(b"fake-ulaw-audio").decode("utf-8")
    event = json.dumps(
        {"type": "response.output_audio.delta", "delta": payload, "item_id": "item_1"}
    )
    await bridge.handle_openai_message(event, openai_send, twilio_send)

    media_calls = [c for c in twilio_send.calls if c["event"] == "media"]
    assert len(media_calls) == 1
    assert media_calls[0]["streamSid"] == "MZ123"
    assert media_calls[0]["media"]["payload"] == payload

    mark_calls = [c for c in twilio_send.calls if c["event"] == "mark"]
    assert len(mark_calls) == 1
    assert bridge.last_assistant_item == "item_1"


@pytest.mark.asyncio
async def test_barge_in_truncates_and_clears(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    bridge.stream_sid = "MZ123"
    openai_send = Recorder()
    twilio_send = Recorder()

    # Assistant starts speaking.
    payload = base64.b64encode(b"fake-audio").decode("utf-8")
    await bridge.handle_openai_message(
        json.dumps({"type": "response.output_audio.delta", "delta": payload, "item_id": "item_1"}),
        openai_send,
        twilio_send,
    )

    # Caller starts talking 250ms later.
    bridge.latest_media_timestamp = bridge.response_start_timestamp + 250
    openai_send.calls.clear()
    twilio_send.calls.clear()

    await bridge.handle_openai_message(
        json.dumps({"type": "input_audio_buffer.speech_started"}), openai_send, twilio_send
    )

    truncate_events = [json.loads(c) for c in openai_send.calls if json.loads(c)["type"] == "conversation.item.truncate"]
    assert len(truncate_events) == 1
    assert truncate_events[0]["item_id"] == "item_1"
    assert truncate_events[0]["audio_end_ms"] == 250

    clear_events = [c for c in twilio_send.calls if c["event"] == "clear"]
    assert len(clear_events) == 1
    assert clear_events[0]["streamSid"] == "MZ123"

    assert bridge.last_assistant_item is None
    assert bridge.mark_queue == []


@pytest.mark.asyncio
async def test_function_call_round_trip(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    openai_send = Recorder()
    twilio_send = Recorder()

    event = json.dumps(
        {
            "type": "response.function_call_arguments.done",
            "call_id": "call_abc",
            "name": "get_business_hours",
            "arguments": "{}",
        }
    )
    await bridge.handle_openai_message(event, openai_send, twilio_send)

    assert len(openai_send.calls) == 2
    item_create = json.loads(openai_send.calls[0])
    assert item_create["type"] == "conversation.item.create"
    assert item_create["item"]["type"] == "function_call_output"
    assert item_create["item"]["call_id"] == "call_abc"
    output = json.loads(item_create["item"]["output"])
    assert "open_now" in output

    response_create = json.loads(openai_send.calls[1])
    assert response_create["type"] == "response.create"

    assert len(bridge.call_log.tool_calls) == 1
    assert bridge.call_log.tool_calls[0]["name"] == "get_business_hours"


@pytest.mark.asyncio
async def test_end_call_hangs_up_on_response_done_dry_run(sample_config):
    bridge = make_bridge(sample_config, dry_run=True)
    openai_send = Recorder()
    twilio_send = Recorder()

    event = json.dumps(
        {
            "type": "response.function_call_arguments.done",
            "call_id": "call_1",
            "name": "end_call",
            "arguments": "{}",
        }
    )
    await bridge.handle_openai_message(event, openai_send, twilio_send)
    assert bridge.should_close is False

    await bridge.handle_openai_message(json.dumps({"type": "response.done"}), openai_send, twilio_send)
    assert bridge.should_close is True


@pytest.mark.asyncio
async def test_transfer_call_updates_live_call_via_rest(sample_config, monkeypatch):
    monkeypatch.setattr(tools_module, "is_open_now", lambda config, now=None: True)

    fake_rest_client = FakeTwilioRestClient()
    bridge = make_bridge(sample_config, dry_run=False, twilio_rest_client=fake_rest_client)
    openai_send = Recorder()
    twilio_send = Recorder()

    call_event = json.dumps(
        {
            "type": "response.function_call_arguments.done",
            "call_id": "call_1",
            "name": "transfer_call",
            "arguments": json.dumps({"department": "Billing"}),
        }
    )
    await bridge.handle_openai_message(call_event, openai_send, twilio_send)
    await bridge.handle_openai_message(json.dumps({"type": "response.done"}), openai_send, twilio_send)

    assert len(fake_rest_client.updates) == 1
    assert "+15551234567" in fake_rest_client.updates[0]
    assert "<Dial>" in fake_rest_client.updates[0]


def test_greeting_events_make_the_receptionist_speak_first():
    """The bridge must request a response right after session.update so the caller hears a greeting."""
    from receptionist.config import load_config
    from receptionist.realtime_bridge import MediaBridge
    import pathlib

    config = load_config(pathlib.Path(__file__).resolve().parent.parent / "business.example.yaml")
    bridge = MediaBridge(config, call_sid="CA_test_greeting", dry_run=True)
    events = bridge.greeting_events()
    assert events[0]["type"] == "conversation.item.create"
    assert events[0]["item"]["content"][0]["type"] == "input_text"
    assert events[-1] == {"type": "response.create"}
