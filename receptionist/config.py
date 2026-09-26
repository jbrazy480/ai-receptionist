"""Pydantic configuration models and loader for business.yaml."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
_PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")


class ConfigError(Exception):
    """Raised when business.yaml fails to load or validate."""


class DayHours(BaseModel):
    open: str = Field(..., description="Opening time, 24h HH:MM")
    close: str = Field(..., description="Closing time, 24h HH:MM")

    @field_validator("open", "close")
    @classmethod
    def _validate_time(cls, value: str) -> str:
        if not _TIME_RE.match(value):
            raise ValueError(
                f"'{value}' is not a valid 24-hour time. Use HH:MM, e.g. '09:00'."
            )
        return value


class FAQ(BaseModel):
    question: str
    answer: str


class Department(BaseModel):
    name: str
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        if not _PHONE_RE.match(value):
            raise ValueError(
                f"'{value}' is not a valid E.164 phone number, e.g. '+15551234567'."
            )
        return value


class BookingConfig(BaseModel):
    webhook_url: Optional[str] = None


class MessagesConfig(BaseModel):
    file_path: str = "data/messages.jsonl"
    webhook_url: Optional[str] = None


class BusinessInfo(BaseModel):
    name: str
    timezone: str
    greeting: str
    after_hours_message: str
    voice: str = "alloy"

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"'{value}' is not a known IANA timezone, e.g. 'America/New_York'."
            ) from exc
        return value


class BusinessConfig(BaseModel):
    business: BusinessInfo
    hours: dict[str, Optional[DayHours]]
    faqs: list[FAQ] = Field(default_factory=list)
    departments: list[Department] = Field(default_factory=list)
    booking: BookingConfig = Field(default_factory=BookingConfig)
    messages: MessagesConfig = Field(default_factory=MessagesConfig)

    @field_validator("hours")
    @classmethod
    def _validate_hours_keys(
        cls, value: dict[str, Optional[DayHours]]
    ) -> dict[str, Optional[DayHours]]:
        missing = [day for day in WEEKDAYS if day not in value]
        if missing:
            raise ValueError(
                "hours: missing entries for "
                f"{', '.join(missing)}. All seven weekdays must be listed "
                "(use 'null' for a closed day)."
            )
        unknown = [day for day in value if day not in WEEKDAYS]
        if unknown:
            raise ValueError(
                f"hours: unknown weekday name(s): {', '.join(unknown)}. "
                f"Expected one of {', '.join(WEEKDAYS)}."
            )
        return value

    def department_by_name(self, name: str) -> Optional[Department]:
        target = name.strip().lower()
        for dept in self.departments:
            if dept.name.strip().lower() == target:
                return dept
        return None


def _format_validation_error(exc: ValidationError, path: Path) -> str:
    lines = [f"Invalid configuration in {path}:"]
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"])
        lines.append(f"  - {loc}: {error['msg']}")
    return "\n".join(lines)


def load_config(path: str | Path) -> BusinessConfig:
    """Load and validate business.yaml, raising ConfigError with a clear message."""
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(
            f"Config file not found: {config_path}. "
            "Copy business.example.yaml to business.yaml and edit it."
        )

    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse {config_path} as YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping at the top level.")

    try:
        return BusinessConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(exc, config_path)) from exc
