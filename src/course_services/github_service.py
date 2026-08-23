"""GitHub review-comment planning with an explicit human approval boundary."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from typing import Any

from src.course_services.contracts import PullRequestTarget, ReviewCommentPlan, ReviewReport
from src.meeting_demo import ensure_workspace_path


class InMemoryIdempotencyStore:
    """Classroom store that makes duplicate publication observable."""

    def __init__(self) -> None:
        self._results: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._results.get(key)

    def put(self, key: str, result: dict[str, Any]) -> None:
        self._results[key] = dict(result)


def load_pr_fixture(path: Path, *, workspace_root: Path) -> dict[str, Any]:
    """Read a synthetic PR fixture only after enforcing the workspace boundary."""

    resolved = ensure_workspace_path(path, workspace_root)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    required = {"repository", "number", "head_sha", "title", "diff"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"PR_FIXTURE_FIELDS_REQUIRED: {','.join(missing)}")
    PullRequestTarget(
        repository=payload["repository"],
        number=payload["number"],
        head_sha=payload["head_sha"],
    )
    return payload


def _render_comment_body(report: ReviewReport) -> str:
    if not report.findings:
        return "검토 결과: 현재 diff에서 게시할 만한 고위험 finding을 찾지 못했습니다."
    rows = ["## 교육용 코드 리뷰 초안", ""]
    for finding in report.findings:
        rows.extend(
            [
                f"- **{finding.severity} · {finding.title}**",
                f"  - 위치: `{finding.path}:{finding.line}`",
                f"  - 근거: `{finding.evidence}`",
                f"  - 제안: {finding.suggestion}",
            ]
        )
    rows.extend(["", "자동 게시하지 않았습니다. 대상과 내용을 사람이 확인해야 합니다."])
    return "\n".join(rows)


def prepare_review_comment(
    *,
    report: dict[str, Any],
    target: dict[str, Any],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Create a deterministic payload without contacting GitHub."""

    parsed_report = ReviewReport.model_validate(report)
    parsed_target = PullRequestTarget.model_validate(target)
    body = _render_comment_body(parsed_report)
    digest_source = (
        f"{parsed_target.repository}:{parsed_target.number}:"
        f"{parsed_target.head_sha}:{body}"
    )
    key = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:24]
    plan = ReviewCommentPlan(
        status="DRY_RUN" if dry_run else "READY_FOR_APPROVAL",
        target=parsed_target,
        body=body,
        idempotency_key=key,
        human_approval_required=True,
        external_write=False,
    )
    return plan.model_dump(mode="json")


def publish_review_comment(
    *,
    plan: dict[str, Any],
    human_approved: bool,
    publisher: Callable[[PullRequestTarget, str], dict[str, Any]] | None,
    store: InMemoryIdempotencyStore,
) -> dict[str, Any]:
    """Publish at most once after approval; no live network client is bundled."""

    parsed = ReviewCommentPlan.model_validate(plan)
    if parsed.status == "DRY_RUN":
        return parsed.model_copy(
            update={"status": "BLOCKED", "error_code": "DRY_RUN_CANNOT_PUBLISH"}
        ).model_dump(mode="json")
    if not human_approved:
        return parsed.model_copy(
            update={"status": "BLOCKED", "error_code": "HUMAN_APPROVAL_REQUIRED"}
        ).model_dump(mode="json")
    if publisher is None:
        return parsed.model_copy(
            update={"status": "BLOCKED", "error_code": "PUBLISHER_NOT_CONFIGURED"}
        ).model_dump(mode="json")

    previous = store.get(parsed.idempotency_key)
    if previous is not None:
        return parsed.model_copy(
            update={
                "status": "PUBLISHED",
                "external_write": True,
                "remote_result": {**previous, "reused": True},
            }
        ).model_dump(mode="json")

    remote_result = publisher(parsed.target, parsed.body)
    store.put(parsed.idempotency_key, remote_result)
    return parsed.model_copy(
        update={
            "status": "PUBLISHED",
            "external_write": True,
            "remote_result": {**remote_result, "reused": False},
        }
    ).model_dump(mode="json")
