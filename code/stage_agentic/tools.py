from __future__ import annotations


def normalize_channel(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def lookup_service_tier(service: str, context: dict) -> str:
    return context["service_tiers"][service]


def lookup_retry_multiplier(tier: str, context: dict) -> int:
    return int(context["retry_multiplier_by_tier"][tier])


def lookup_service_owner(service: str, context: dict) -> str:
    return context["service_owners"][service]


def lookup_primary_channel(service: str, context: dict) -> str:
    return context["service_primary_channels"][service]


def lookup_backup_channel(service: str, context: dict) -> str:
    return context["service_backup_channels"][service]


def is_escalation_channel(channel: str, context: dict) -> bool:
    return channel in set(context["escalation_channels"])


def multiply(a: int, b: int) -> int:
    return int(a) * int(b)
