"""Human review policy starter used by the Day 2 Codex lab."""

from __future__ import annotations

from typing import Any


EXTERNAL_ACTIONS = frozenset({"email", "notion", "confluence", "slack"})


def requires_human_review(request: dict[str, Any]) -> bool:
    """Return whether the proposed meeting-record action needs human review."""

    # TODO(day2 learner): implement the policy described in TASK.md.
    return False
