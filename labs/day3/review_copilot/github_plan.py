"""GitHub Draft PR planning; this module never executes a command."""

from __future__ import annotations

import hashlib
import shlex
from typing import Any

from .contracts import HumanReview, validate_github_target
from .safety import is_sensitive_path


def _blocked(code: str) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "error_code": code,
        "human_approval_required": True,
        "external_write": False,
        "commands_executed": [],
    }


def _render_pr_body(
    *,
    review: HumanReview,
    changed_paths: list[str],
    test_evidence: dict[str, Any],
) -> str:
    findings = list(review.findings)
    risk = findings[0].title if findings else "조치 가능한 finding이 없는 변경의 회귀 위험"
    finding_summary = (
        "; ".join(
            f"{item.severity} {item.path}:{item.line} {item.title}" for item in findings
        )
        or "조치 가능한 finding 없음"
    )
    command = str(test_evidence.get("command", "focused test command unavailable"))
    result = f"{test_evidence['status']} · exit_code={test_evidence['exit_code']}"
    return "\n".join(
        [
            "## Goal",
            "",
            "Review Copilot 검토 결과와 회귀 테스트 증거를 Draft PR로 전달합니다.",
            "",
            "## Scope",
            "",
            f"- Changed files: {', '.join(changed_paths)}",
            "- Intentionally unchanged: 자동 게시, 자동 comment, 자동 merge, 실제 고객 데이터",
            "",
            "## Safety and data",
            "",
            "- [x] No secret, token, real customer data, or private meeting data is included.",
            "- [x] File, tool, and external-write boundaries remain explicit.",
            "- [x] Human approval is preserved for consequential actions.",
            "",
            "## Test evidence",
            "",
            "~~~text",
            command,
            "~~~",
            f"- Result: {result}",
            "- Added/updated normal test: golden safe-negative와 허용 workflow",
            "- Added/updated failure or boundary test: path escape와 Human Review 차단",
            "",
            "## Review request",
            "",
            f"- Risk to inspect: {risk}",
            f"- Expected behavior: {finding_summary}",
            f"- Human review: {review.status} · {review.reviewer} · {review.rationale}",
            "- Known limitation: AI review는 merge 승인이 아니며 실제 대상은 사람이 재확인",
            "",
            "## Human merge checklist",
            "",
            "- [ ] Diff matches the stated goal.",
            "- [ ] CI is green.",
            "- [ ] Review findings were fixed or answered with a reason.",
            "- [ ] AI review output was treated as advice, not approval.",
            "- [ ] A human checked the final diff and merge target.",
        ]
    )


def build_github_dry_run(
    *,
    repository: str,
    base: str,
    branch: str,
    title: str,
    review: HumanReview,
    changed_paths: list[str],
    test_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Build a day3-pr-guard-compatible Draft PR only after review and tests."""

    try:
        validate_github_target(repository, base, branch)
    except ValueError as exc:
        return _blocked(str(exc))
    if review.status not in {"APPROVED", "EDITED"}:
        return _blocked("HUMAN_REVIEW_REQUIRED")
    if not changed_paths:
        return _blocked("CHANGED_PATHS_REQUIRED")
    if any(is_sensitive_path(path) for path in changed_paths):
        return _blocked("SENSITIVE_PATH_CHANGED")
    if not test_evidence.get("executed"):
        return _blocked("FOCUSED_TEST_REQUIRED")
    if (
        test_evidence.get("status") != "PASSED"
        or test_evidence.get("exit_code") != 0
        or not str(test_evidence.get("command", "")).strip()
    ):
        return _blocked("FOCUSED_TEST_FAILED")

    body = _render_pr_body(
        review=review,
        changed_paths=changed_paths,
        test_evidence=test_evidence,
    )
    digest = hashlib.sha256(
        f"{repository}:{base}:{branch}:{title}:{body}".encode("utf-8")
    ).hexdigest()[:24]
    stage_paths = " ".join(shlex.quote(path) for path in changed_paths)
    return {
        "status": "DRY_RUN_READY",
        "target": {"repository": repository, "base": base, "branch": branch},
        "pull_request": {"title": title, "body": body, "draft": True},
        "test_evidence": {
            "status": test_evidence["status"],
            "command": test_evidence["command"],
            "exit_code": test_evidence["exit_code"],
        },
        "suggested_commands": [
            f"git switch -c {branch}",
            f"git add -- {stage_paths}",
            "git diff --cached",
            'git commit -m "feat(day3): add reviewed change"',
            f"git push -u origin {branch}",
            f"gh pr create --draft --repo {repository} --base {base} --head {branch}",
        ],
        "idempotency_key": digest,
        "human_approval_required": True,
        "external_write": False,
        "commands_executed": [],
        "next_step": "사람이 diff·test·target을 다시 확인한 뒤 명령을 한 줄씩 실행",
    }
