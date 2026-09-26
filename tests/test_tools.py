import json

from receptionist.tools import TOOL_DEFINITIONS, ToolExecutor


def test_tool_definitions_cover_all_tools():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert names == {
        "get_business_hours",
        "answer_faq",
        "take_message",
        "transfer_call",
        "book_appointment",
        "end_call",
    }
    for tool in TOOL_DEFINITIONS:
        assert tool["type"] == "function"
        assert "parameters" in tool


def test_get_business_hours(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.get_business_hours()
    assert "open_now" in result
    assert "weekly_hours" in result


def test_answer_faq_found(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.answer_faq("Do you accept walk-ins for a visit?")
    assert result["found"] is True
    assert "availability" in result["answer"]


def test_answer_faq_not_found_never_invents(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.answer_faq("What is the meaning of life?")
    assert result["found"] is False
    assert result["answer"] is None


def test_take_message_writes_jsonl(sample_config_with_paths):
    executor = ToolExecutor(sample_config_with_paths, call_sid="CA123", dry_run=True)
    result = executor.take_message(
        name="Jamie", callback_number="+15550001111", reason="question about pricing"
    )
    assert result["success"] is True

    lines = open(sample_config_with_paths.messages.file_path).read().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["name"] == "Jamie"
    assert record["call_sid"] == "CA123"


def test_book_appointment_without_webhook_writes_file(sample_config, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    executor = ToolExecutor(sample_config, call_sid="CA999", dry_run=True)
    result = executor.book_appointment(
        name="Jamie", phone="+15550001111", requested_time="Tuesday 2pm", service="cleaning"
    )
    assert result["success"] is True
    lines = (tmp_path / "data" / "bookings.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["service"] == "cleaning"


def test_book_appointment_with_webhook_posts(sample_config, monkeypatch):
    sample_config.booking.webhook_url = "https://example.invalid/hook"

    posted = {}

    class FakeClient:
        def post(self, url, json=None, timeout=None):
            posted["url"] = url
            posted["json"] = json

    executor = ToolExecutor(sample_config, dry_run=True, webhook_client=FakeClient())
    result = executor.book_appointment(
        name="Jamie", phone="+15550001111", requested_time="Tuesday 2pm", service="cleaning"
    )
    assert result["success"] is True
    assert posted["url"] == "https://example.invalid/hook"
    assert posted["json"]["service"] == "cleaning"


def test_transfer_call_when_open(sample_config, monkeypatch):
    import receptionist.tools as tools_module

    monkeypatch.setattr(tools_module, "is_open_now", lambda config, now=None: True)
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.transfer_call("Billing")

    assert result["success"] is True
    assert result["pending_action"]["type"] == "transfer"
    assert result["pending_action"]["phone_number"] == "+15551234567"


def test_transfer_call_after_hours_falls_back_to_message(sample_config, monkeypatch):
    import receptionist.tools as tools_module

    monkeypatch.setattr(tools_module, "is_open_now", lambda config, now=None: False)
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.transfer_call("Billing")

    assert result["success"] is False
    assert result["pending_action"] is None


def test_transfer_call_unknown_department(sample_config, monkeypatch):
    import receptionist.tools as tools_module

    monkeypatch.setattr(tools_module, "is_open_now", lambda config, now=None: True)
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.transfer_call("Nonexistent")
    assert result["success"] is False
    assert "Billing" in result["message"]


def test_end_call_sets_pending_hangup(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.end_call(reason="done")
    assert result["success"] is True
    assert result["pending_action"]["type"] == "hangup"


def test_dispatch_routes_to_correct_tool(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.dispatch("answer_faq", {"question": "Do you take insurance?"})
    assert result["found"] is True


def test_dispatch_unknown_tool(sample_config):
    executor = ToolExecutor(sample_config, dry_run=True)
    result = executor.dispatch("not_a_real_tool", {})
    assert result["success"] is False
