"""Normal and boundary examples for the safe synthetic base revision."""

import pytest

from .meeting_export import prepare_minutes


def test_prepare_minutes_returns_local_draft() -> None:
    result = prepare_minutes("summarize", {"request_id": "fixture-001"})
    assert result["status"] == "DRAFT"


def test_prepare_minutes_requires_request_id() -> None:
    with pytest.raises(ValueError, match="REQUEST_ID_REQUIRED"):
        prepare_minutes("summarize", {})
