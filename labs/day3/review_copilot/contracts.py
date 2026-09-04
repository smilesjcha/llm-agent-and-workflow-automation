"""Small Pydantic contracts kept explicit for the Day 3 service lab."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError


Severity = Literal["P0", "P1", "P2", "P3"]
Decision = Literal["approve", "edit", "reject"]


class ReviewPolicy(BaseModel):
    """Human-readable rules that define a useful review finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    focus: tuple[str, ...] = (
        "correctness",
        "security",
        "data_loss",
        "contract_break",
    )
    ignored: tuple[str, ...] = ("style_only", "unrelated_code", "invented_runtime_result")
    allowed_severities: tuple[Severity, ...] = ("P0", "P1", "P2", "P3")
    require_added_line: bool = True
    require_evidence: bool = True
    automatic_publish: Literal[False] = False

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class AddedLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    text: str

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class ParsedDiff(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    changed_paths: tuple[str, ...]
    added_lines: tuple[AddedLine, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "changed_paths": list(self.changed_paths),
            "added_lines": [line.to_dict() for line in self.added_lines],
        }


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    severity: Severity
    title: str = Field(min_length=2, max_length=120)
    impact: str = Field(min_length=2)
    evidence: str = Field(min_length=1)
    correction: str = Field(min_length=2)
    rule_id: str = Field(min_length=2)
    source: Literal["rule", "fixture_llm", "live_llm"] = "rule"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    automatic_publish: Literal[False] = False

    @field_validator("line", mode="before")
    @classmethod
    def line_must_be_positive(cls, value: object) -> object:
        if isinstance(value, bool):
            raise PydanticCustomError("FINDING_LINE_INVALID", "FINDING_LINE_INVALID")
        try:
            valid = int(value) >= 1  # type: ignore[arg-type]
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise PydanticCustomError("FINDING_LINE_INVALID", "FINDING_LINE_INVALID")
        return value

    @field_validator("severity", mode="before")
    @classmethod
    def severity_must_be_known(cls, value: object) -> object:
        if value not in {"P0", "P1", "P2", "P3"}:
            raise PydanticCustomError(
                "FINDING_SEVERITY_INVALID", "FINDING_SEVERITY_INVALID"
            )
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def confidence_must_be_bounded(cls, value: object) -> object:
        try:
            valid = not isinstance(value, bool) and 0.0 <= float(value) <= 1.0  # type: ignore[arg-type]
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise PydanticCustomError(
                "FINDING_CONFIDENCE_INVALID", "FINDING_CONFIDENCE_INVALID"
            )
        return value

    @field_validator("automatic_publish", mode="before")
    @classmethod
    def automatic_publish_must_be_false(cls, value: object) -> object:
        if value is not False:
            raise PydanticCustomError(
                "AUTOMATIC_PUBLISH_FORBIDDEN", "AUTOMATIC_PUBLISH_FORBIDDEN"
            )
        return value

    @model_validator(mode="after")
    def validate_policy_fields(self) -> "ReviewFinding":
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise PydanticCustomError("FINDING_PATH_INVALID", "FINDING_PATH_INVALID")
        return self

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class ProviderCandidate(BaseModel):
    """Provider output before grounding it to an actual added line."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    severity: Severity
    title: str = Field(min_length=2, max_length=120)
    impact: str = Field(min_length=2)
    correction: str = Field(min_length=2)
    rule_id: str = Field(min_length=2)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class ReviewDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["DRAFT", "EXPECTED_FAILURE"]
    findings: tuple[ReviewFinding, ...] = Field(default_factory=tuple)
    provider_requested: str = "fixture"
    provider_used: str = "fixture"
    fallback_reason: str | None = None
    error_code: str | None = None
    automatic_publish: bool = False

    @model_validator(mode="after")
    def expected_failure_has_code(self) -> "ReviewDraft":
        if self.status == "EXPECTED_FAILURE" and not self.error_code:
            raise ValueError("EXPECTED_FAILURE_REQUIRES_ERROR_CODE")
        if self.automatic_publish:
            raise ValueError("AUTOMATIC_PUBLISH_FORBIDDEN")
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "findings": [finding.to_dict() for finding in self.findings],
            "provider_requested": self.provider_requested,
            "provider_used": self.provider_used,
            "fallback_reason": self.fallback_reason,
            "error_code": self.error_code,
            "automatic_publish": False,
        }


class HumanReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["REVIEW_REQUIRED", "APPROVED", "EDITED", "REJECTED", "BLOCKED"]
    decision: Decision | None = None
    requested_decision: str | None = None
    reviewer: str | None = None
    rationale: str
    findings: tuple[ReviewFinding, ...]
    human_reviewed: bool = False
    external_write: Literal[False] = False
    error_code: str | None = None

    @model_validator(mode="after")
    def status_matches_review_state(self) -> "HumanReview":
        if self.status == "REVIEW_REQUIRED":
            if self.decision is not None or self.human_reviewed:
                raise ValueError("PENDING_REVIEW_STATE_INVALID")
        elif self.status in {"APPROVED", "EDITED", "REJECTED"}:
            if self.decision is None or not self.human_reviewed:
                raise ValueError("COMPLETED_REVIEW_STATE_INVALID")
            if not self.reviewer or not self.rationale:
                raise ValueError("COMPLETED_REVIEW_METADATA_REQUIRED")
        elif self.status == "BLOCKED" and not self.error_code:
            raise ValueError("BLOCKED_REVIEW_REQUIRES_ERROR_CODE")
        return self

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "decision": self.decision,
            "requested_decision": self.requested_decision,
            "reviewer": self.reviewer,
            "rationale": self.rationale,
            "findings": [finding.to_dict() for finding in self.findings],
            "human_reviewed": self.human_reviewed,
            "external_write": False,
            "error_code": self.error_code,
        }


_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")


def validate_github_target(repository: str, base: str, branch: str) -> None:
    """Reject ambiguous targets before a command or API payload is prepared."""

    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("GITHUB_REPOSITORY_INVALID")
    if not _BRANCH.fullmatch(base) or not _BRANCH.fullmatch(branch):
        raise ValueError("GITHUB_BRANCH_INVALID")
    if branch == base:
        raise ValueError("GITHUB_HEAD_EQUALS_BASE")
    if not branch.startswith("codex/"):
        raise ValueError("GITHUB_BRANCH_PREFIX_REQUIRED")
