from datetime import datetime
from zoneinfo import ZoneInfo

from receptionist.hours import business_hours_status, is_after_hours, is_open_now


def test_open_during_business_hours(sample_config):
    # Monday 10:00 America/New_York
    now = datetime(2026, 9, 21, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, now) is True
    assert is_after_hours(sample_config, now) is False


def test_closed_before_open(sample_config):
    now = datetime(2026, 9, 21, 7, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, now) is False
    assert is_after_hours(sample_config, now) is True


def test_closed_after_close(sample_config):
    now = datetime(2026, 9, 21, 18, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, now) is False


def test_closed_on_weekend(sample_config):
    # Saturday
    now = datetime(2026, 9, 26, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, now) is False


def test_friday_shorter_hours(sample_config):
    friday_afternoon = datetime(2026, 9, 25, 16, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, friday_afternoon) is False
    friday_midday = datetime(2026, 9, 25, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    assert is_open_now(sample_config, friday_midday) is True


def test_timezone_conversion_across_zones(sample_config):
    # Business is in America/New_York. 21:00 UTC on Monday is 17:00 in New York
    # during EDT (UTC-4), i.e. right at closing, so should read as closed.
    now_utc = datetime(2026, 9, 21, 21, 0, tzinfo=ZoneInfo("UTC"))
    assert is_open_now(sample_config, now_utc) is False

    # 19:00 UTC is 15:00 New York, well within hours.
    now_utc_open = datetime(2026, 9, 21, 19, 0, tzinfo=ZoneInfo("UTC"))
    assert is_open_now(sample_config, now_utc_open) is True


def test_naive_datetime_assumed_local(sample_config):
    naive = datetime(2026, 9, 21, 10, 0)
    assert is_open_now(sample_config, naive) is True


def test_business_hours_status_shape(sample_config):
    now = datetime(2026, 9, 21, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    status = business_hours_status(sample_config, now)
    assert status["open_now"] is True
    assert "Monday" in status["today"]
    assert "Saturday: closed" in status["weekly_hours"]
    assert status["timezone"] == "America/New_York"
