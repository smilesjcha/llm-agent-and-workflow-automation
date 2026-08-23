"""Day 5 router that joins meeting and code-review services safely."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from src.course_services.review_service import run_review_service
from src.day1_agent import build_day1_summary
from src.meeting_demo import ensure_workspace_path, parse_transcript


InputKind = Literal["meeting_transcript", "code_diff"]


def route_service_request(
    *,
    input_kind: str,
    source_path: Path,
    workspace_root: Path,
) -> dict[str, object]:
    """Route explicit input types; never infer an external side effect."""

    try:
        resolved = ensure_workspace_path(source_path, workspace_root)
    except ValueError as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": str(exc),
            "external_write": False,
        }
    if not resolved.exists():
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "SOURCE_FILE_NOT_FOUND",
            "external_write": False,
        }
    text = resolved.read_text(encoding="utf-8")
    if input_kind == "meeting_transcript":
        segments = parse_transcript(text)
        return {
            "status": "SUCCESS",
            "service": "meeting",
            "result": build_day1_summary(text),
            "evidence_segment_count": len(segments),
            "external_write": False,
            "human_approval_required": True,
        }
    if input_kind == "code_diff":
        return {
            "status": "SUCCESS",
            "service": "code_review",
            "result": run_review_service(text),
            "external_write": False,
            "human_approval_required": True,
        }
    return {
        "status": "EXPECTED_FAILURE",
        "error_code": "UNSUPPORTED_INPUT_KIND",
        "external_write": False,
    }
