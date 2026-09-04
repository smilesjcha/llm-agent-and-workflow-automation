"""Sensitive path and secret-like text guards for provider context."""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Any


_SENSITIVE_BASENAMES = {
    ".env",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}
_SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
_TOKEN_SHAPE = re.compile(r"\b(?:sk-(?:proj-)?|gh[pousr]_|lsv2_)[A-Za-z0-9_-]{10,}")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|token|password|secret)\b\s*[:=]\s*)"
    r"([\"']?)([^\s,;\"']{6,})(?:\2)"
)


def is_sensitive_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/").strip("/")
    parts = PurePosixPath(normalized).parts
    name = PurePosixPath(normalized).name.lower()
    if any(part in {".git", "node_modules", "__pycache__", ".venv", "dist"} for part in parts):
        return True
    if name in _SENSITIVE_BASENAMES or name.startswith(".env."):
        return True
    return PurePosixPath(name).suffix.lower() in _SENSITIVE_SUFFIXES


def redact_secret_like_text(value: str) -> tuple[str, int]:
    count = 0

    def redact_assignment(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}[REDACTED]"

    value = _SECRET_ASSIGNMENT.sub(redact_assignment, value)
    value, token_count = _TOKEN_SHAPE.subn("[REDACTED_TOKEN]", value)
    return value, count + token_count


def contains_secret_like_text(value: str) -> bool:
    _, count = redact_secret_like_text(value)
    return count > 0


def redact_payload(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return redact_secret_like_text(value)
    if isinstance(value, list):
        items = []
        total = 0
        for item in value:
            redacted, count = redact_payload(item)
            items.append(redacted)
            total += count
        return items, total
    if isinstance(value, tuple):
        redacted, count = redact_payload(list(value))
        return redacted, count
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        total = 0
        for key, item in value.items():
            redacted, count = redact_payload(item)
            payload[str(key)] = redacted
            total += count
        return payload, total
    return value, 0
