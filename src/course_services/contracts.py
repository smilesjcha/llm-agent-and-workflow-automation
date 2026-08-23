"""Stable service contracts shared by the Day 2-5 labs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Severity = Literal["P0", "P1", "P2", "P3"]


class ReviewFinding(BaseModel):
    """One actionable review item tied to an added line in the diff."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    severity: Severity
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=4)
    evidence: str = Field(min_length=2)
    suggestion: str = Field(min_length=2)
    confidence: float = Field(ge=0.0, le=1.0)
    rule_id: str = Field(min_length=2)


class ReviewReport(BaseModel):
    """Review result used by notebooks, the router, and GitHub dry-run code."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS", "EXPECTED_FAILURE"]
    findings: list[ReviewFinding] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)
    checks: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    automatic_publish: bool = False

    @model_validator(mode="after")
    def expected_failure_has_code(self) -> "ReviewReport":
        if self.status == "EXPECTED_FAILURE" and not self.error_code:
            raise ValueError("EXPECTED_FAILURE_REQUIRES_ERROR_CODE")
        if self.automatic_publish:
            raise ValueError("AUTOMATIC_PUBLISH_MUST_BE_FALSE")
        return self


class PullRequestTarget(BaseModel):
    """Minimal GitHub PR identity kept separate from credentials."""

    model_config = ConfigDict(extra="forbid")

    repository: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    number: int = Field(ge=1)
    head_sha: str = Field(min_length=7, max_length=64)


class ReviewCommentPlan(BaseModel):
    """A review comment payload that is safe to inspect before publication."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["DRY_RUN", "READY_FOR_APPROVAL", "PUBLISHED", "BLOCKED"]
    target: PullRequestTarget
    body: str
    idempotency_key: str
    human_approval_required: bool = True
    external_write: bool = False
    error_code: str | None = None
    remote_result: dict[str, Any] | None = None

    @model_validator(mode="after")
    def blocked_result_has_code(self) -> "ReviewCommentPlan":
        if self.status == "BLOCKED" and not self.error_code:
            raise ValueError("BLOCKED_REQUIRES_ERROR_CODE")
        if self.status != "PUBLISHED" and self.external_write:
            raise ValueError("EXTERNAL_WRITE_ONLY_AFTER_PUBLISH")
        return self
