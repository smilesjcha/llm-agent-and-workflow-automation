"""Shared Human Review validation for synchronous and LangGraph workflows."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import HumanReview, ReviewDraft, ReviewFinding
from .errors import stable_error_code


def _blocked(
    code: str,
    *,
    requested_decision: str | None,
    reviewer: str | None,
    rationale: str | None,
) -> HumanReview:
    return HumanReview(
        status="BLOCKED",
        decision=None,
        requested_decision=requested_decision,
        reviewer=reviewer.strip() if isinstance(reviewer, str) and reviewer.strip() else None,
        rationale=rationale.strip() if isinstance(rationale, str) else "",
        findings=tuple(),
        human_reviewed=False,
        error_code=code,
    )


def pending_human_review(draft: ReviewDraft) -> HumanReview:
    """Represent a generated draft that has not received a human decision."""

    return HumanReview(
        status="REVIEW_REQUIRED",
        decision=None,
        requested_decision=None,
        reviewer=None,
        rationale="사람이 finding의 근거와 교정을 확인해야 합니다.",
        findings=draft.findings,
        human_reviewed=False,
        error_code="HUMAN_REVIEW_REQUIRED",
    )


def apply_human_review(
    draft: ReviewDraft,
    *,
    decision: str | None,
    reviewer: str | None,
    rationale: str | None,
    edited_findings: Iterable[ReviewFinding | Mapping[str, Any]] | None = None,
) -> HumanReview:
    """Validate approve/edit/reject and keep every failure structured."""

    if draft.status != "DRAFT":
        return _blocked(
            "DRAFT_NOT_REVIEWABLE",
            requested_decision=decision,
            reviewer=reviewer,
            rationale=rationale,
        )
    if decision is None:
        return pending_human_review(draft)
    if decision not in {"approve", "edit", "reject"}:
        return _blocked(
            "HUMAN_REVIEW_DECISION_INVALID",
            requested_decision=decision,
            reviewer=reviewer,
            rationale=rationale,
        )
    if not isinstance(reviewer, str) or not reviewer.strip():
        return _blocked(
            "HUMAN_REVIEWER_REQUIRED",
            requested_decision=decision,
            reviewer=reviewer,
            rationale=rationale,
        )
    if not isinstance(rationale, str) or not rationale.strip():
        return _blocked(
            "HUMAN_REVIEW_RATIONALE_REQUIRED",
            requested_decision=decision,
            reviewer=reviewer,
            rationale=rationale,
        )

    findings = draft.findings
    status = {"approve": "APPROVED", "edit": "EDITED", "reject": "REJECTED"}[decision]
    if decision == "edit":
        if edited_findings is None:
            return _blocked(
                "EDITED_FINDINGS_REQUIRED",
                requested_decision=decision,
                reviewer=reviewer,
                rationale=rationale,
            )
        try:
            findings = tuple(
                item
                if isinstance(item, ReviewFinding)
                else ReviewFinding.model_validate(dict(item))
                for item in edited_findings
            )
        except (TypeError, ValueError) as exc:
            return _blocked(
                stable_error_code(exc),
                requested_decision=decision,
                reviewer=reviewer,
                rationale=rationale,
            )
        if not findings:
            return _blocked(
                "EDITED_FINDINGS_REQUIRED",
                requested_decision=decision,
                reviewer=reviewer,
                rationale=rationale,
            )
        original_locations = {(item.path, item.line) for item in draft.findings}
        if any((item.path, item.line) not in original_locations for item in findings):
            return _blocked(
                "EDIT_FINDING_NOT_GROUNDED",
                requested_decision=decision,
                reviewer=reviewer,
                rationale=rationale,
            )
    elif decision == "reject":
        findings = tuple()

    return HumanReview(
        status=status,  # type: ignore[arg-type]
        decision=decision,  # type: ignore[arg-type]
        requested_decision=decision,
        reviewer=reviewer.strip(),
        rationale=rationale.strip(),
        findings=findings,
        human_reviewed=True,
        external_write=False,
    )
