"""Day 2 transcript chunking and evidence validation service."""

from __future__ import annotations

from typing import Any

from src.meeting_demo import parse_transcript


def chunk_transcript_segments(
    segments: list[dict[str, Any]], *, max_chars: int = 1200, overlap_segments: int = 1
) -> list[dict[str, Any]]:
    """Chunk on segment boundaries so evidence IDs and timestamps survive."""

    if max_chars < 40:
        raise ValueError("MAX_CHARS_TOO_SMALL")
    if overlap_segments < 0:
        raise ValueError("OVERLAP_MUST_BE_NON_NEGATIVE")
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def size(items: list[dict[str, Any]]) -> int:
        return sum(len(str(item.get("text", ""))) for item in items)

    for segment in segments:
        if current and size([*current, segment]) > max_chars:
            chunks.append(
                {
                    "id": f"c{len(chunks) + 1:02d}",
                    "segment_ids": [item["id"] for item in current],
                    "text": "\n".join(str(item.get("text", "")) for item in current),
                }
            )
            current = current[-overlap_segments:] if overlap_segments else []
        current.append(segment)
    if current:
        chunks.append(
            {
                "id": f"c{len(chunks) + 1:02d}",
                "segment_ids": [item["id"] for item in current],
                "text": "\n".join(str(item.get("text", "")) for item in current),
            }
        )
    return chunks


def validate_action_evidence(
    action_items: list[dict[str, Any]], *, known_segment_ids: set[str]
) -> list[str]:
    """Return stable errors instead of inventing evidence for an action item."""

    errors: list[str] = []
    for index, item in enumerate(action_items, start=1):
        evidence_ids = item.get("evidence_ids", [])
        if not evidence_ids:
            errors.append(f"ACTION_{index}_EVIDENCE_REQUIRED")
            continue
        unknown = sorted(set(evidence_ids) - known_segment_ids)
        if unknown:
            errors.append(f"ACTION_{index}_UNKNOWN_EVIDENCE:{','.join(unknown)}")
    return errors


def prepare_transcript_for_summary(
    transcript: str, *, max_chars: int = 1200
) -> dict[str, Any]:
    segments = parse_transcript(transcript)
    return {
        "status": "SUCCESS" if segments else "EXPECTED_FAILURE",
        "error_code": None if segments else "EMPTY_TRANSCRIPT",
        "segments": segments,
        "chunks": chunk_transcript_segments(segments, max_chars=max_chars) if segments else [],
        "human_spot_check_required": True,
    }
