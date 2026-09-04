"""Normalize library exceptions into stable classroom error codes."""

from __future__ import annotations

from pydantic import ValidationError


_FIELD_CODES = {
    "path": "FINDING_PATH_INVALID",
    "line": "FINDING_LINE_INVALID",
    "severity": "FINDING_SEVERITY_INVALID",
    "title": "FINDING_TITLE_INVALID",
    "impact": "FINDING_IMPACT_INVALID",
    "evidence": "FINDING_EVIDENCE_INVALID",
    "correction": "FINDING_CORRECTION_INVALID",
    "rule_id": "FINDING_RULE_ID_INVALID",
    "confidence": "FINDING_CONFIDENCE_INVALID",
    "automatic_publish": "AUTOMATIC_PUBLISH_FORBIDDEN",
}


def stable_error_code(exc: BaseException) -> str:
    """Return one named code instead of a version-specific traceback message."""

    if isinstance(exc, ValidationError):
        errors = exc.errors()
        if not errors:
            return "VALIDATION_ERROR"
        first = errors[0]
        error_type = str(first.get("type", ""))
        if error_type.isupper():
            return error_type
        location = first.get("loc", ())
        field = str(location[-1]) if location else ""
        return _FIELD_CODES.get(field, "CONTRACT_VALIDATION_FAILED")
    text = str(exc).splitlines()[0].strip()
    if text and " " not in text and len(text) <= 120:
        return text
    return "UNEXPECTED_INPUT_ERROR"
