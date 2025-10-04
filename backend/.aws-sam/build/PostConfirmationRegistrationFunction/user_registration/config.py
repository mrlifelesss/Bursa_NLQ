from __future__ import annotations

import os
from dataclasses import dataclass


class MissingConfiguration(RuntimeError):
    """Raised when the Lambda configuration is incomplete."""


@dataclass(frozen=True)
class RegistrationSettings:
    users_table: str
    organizations_table: str
    free_group_name: str
    default_language: str
    tier1_limit: int
    tier2_limit: int
    welcome_period_days: int


def _require(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise MissingConfiguration(f"Environment variable '{name}' must be defined")
    return value


def _optional_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise MissingConfiguration(f"Environment variable '{name}' must be an integer") from exc


def load_settings() -> RegistrationSettings:
    """Read configuration from environment variables."""
    return RegistrationSettings(
        users_table=_require("USERS_TABLE_NAME"),
        organizations_table=_require("ORGS_TABLE_NAME"),
        free_group_name=os.getenv("FREE_TIER_GROUP_NAME", "Free-Tier"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
        tier1_limit=_optional_int("FREE_TIER_TIER1_LIMIT", 5),
        tier2_limit=_optional_int("FREE_TIER_TIER2_LIMIT", 3),
        welcome_period_days=_optional_int("FREE_TIER_WELCOME_DAYS", 30),
    )