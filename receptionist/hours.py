"""Business hours and after-hours detection, timezone aware."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from zoneinfo import ZoneInfo

from receptionist.config import WEEKDAYS, BusinessConfig, DayHours


def _now_local(config: BusinessConfig, now: Optional[datetime] = None) -> datetime:
    tz = ZoneInfo(config.business.timezone)
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def today_hours(config: BusinessConfig, now: Optional[datetime] = None) -> Optional[DayHours]:
    local = _now_local(config, now)
    weekday_name = WEEKDAYS[local.weekday()]
    return config.hours.get(weekday_name)


def is_open_now(config: BusinessConfig, now: Optional[datetime] = None) -> bool:
    local = _now_local(config, now)
    day_hours = today_hours(config, now)
    if day_hours is None:
        return False
    open_h, open_m = (int(part) for part in day_hours.open.split(":"))
    close_h, close_m = (int(part) for part in day_hours.close.split(":"))
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m
    now_minutes = local.hour * 60 + local.minute
    return open_minutes <= now_minutes < close_minutes


def is_after_hours(config: BusinessConfig, now: Optional[datetime] = None) -> bool:
    return not is_open_now(config, now)


def hours_summary(config: BusinessConfig) -> str:
    """Human-readable weekly hours, in weekday order, for the system prompt and tool replies."""
    lines = []
    for day in WEEKDAYS:
        day_hours = config.hours.get(day)
        label = day.capitalize()
        if day_hours is None:
            lines.append(f"{label}: closed")
        else:
            lines.append(f"{label}: {day_hours.open} to {day_hours.close}")
    return "\n".join(lines)


def business_hours_status(config: BusinessConfig, now: Optional[datetime] = None) -> dict:
    """Structured status used by the get_business_hours tool."""
    local = _now_local(config, now)
    day_hours = today_hours(config, now)
    open_now = is_open_now(config, now)
    if day_hours is None:
        today_text = f"{WEEKDAYS[local.weekday()].capitalize()}: closed"
    else:
        today_text = (
            f"{WEEKDAYS[local.weekday()].capitalize()}: {day_hours.open} to {day_hours.close}"
        )
    return {
        "open_now": open_now,
        "today": today_text,
        "weekly_hours": hours_summary(config),
        "timezone": config.business.timezone,
    }
