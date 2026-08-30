"""Reference implementation for the Day 2 human review policy."""

from __future__ import annotations

from typing import Any


EXTERNAL_ACTIONS = frozenset({"email", "notion", "confluence", "slack"})


def requires_human_review(request: dict[str, Any]) -> bool:
    action = str(request.get("action", "")).strip().lower()
    evidence_errors = request.get("evidence_errors") or []
    return action in EXTERNAL_ACTIONS or bool(evidence_errors)
