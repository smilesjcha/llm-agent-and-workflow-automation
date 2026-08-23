"""Small harness for turning a Codex request into reviewable evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CodexTaskSpec:
    objective: str
    allowed_paths: tuple[str, ...]
    acceptance_tests: tuple[str, ...]
    forbidden_actions: tuple[str, ...] = (
        "secret 출력 또는 commit",
        "workspace 밖 파일 변경",
        "사람 승인 없는 외부 쓰기",
        "통과를 위한 기존 test 약화",
    )
    rollback_point: str = "작업 전 commit"
    context_files: tuple[str, ...] = ("AGENTS.md", "README.md")


def render_codex_task(spec: CodexTaskSpec) -> str:
    """Render a concise task request that Codex can execute and humans can audit."""

    allowed = "\n".join(f"- {item}" for item in spec.allowed_paths)
    tests = "\n".join(f"- {item}" for item in spec.acceptance_tests)
    forbidden = "\n".join(f"- {item}" for item in spec.forbidden_actions)
    context = "\n".join(f"- {item}" for item in spec.context_files)
    return (
        f"목표\n{spec.objective}\n\n"
        f"먼저 읽을 파일\n{context}\n\n"
        f"변경 허용 범위\n{allowed}\n\n"
        f"완료 조건\n{tests}\n\n"
        f"금지 행동\n{forbidden}\n\n"
        f"복구 지점\n- {spec.rollback_point}\n\n"
        "마지막에 변경 파일, 핵심 diff, 실행한 test 명령과 결과를 보고하세요."
    )


def _path_is_allowed(path: str, allowed: Iterable[str]) -> bool:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    for prefix in allowed:
        normalized = prefix.rstrip("/")
        if path == normalized or path.startswith(f"{normalized}/"):
            return True
    return False


def assess_codex_run(
    spec: CodexTaskSpec,
    *,
    changed_paths: list[str],
    executed_tests: dict[str, bool],
    diff_reviewed: bool,
    secrets_detected: bool,
) -> dict[str, object]:
    """Gate a generated patch on scope, tests, review, and secret handling."""

    unexpected_paths = sorted(
        path for path in changed_paths if not _path_is_allowed(path, spec.allowed_paths)
    )
    missing_tests = sorted(
        command for command in spec.acceptance_tests if not executed_tests.get(command, False)
    )
    reasons: list[str] = []
    if unexpected_paths:
        reasons.append("UNEXPECTED_CHANGED_PATH")
    if missing_tests:
        reasons.append("ACCEPTANCE_TEST_NOT_PASSED")
    if not diff_reviewed:
        reasons.append("DIFF_REVIEW_REQUIRED")
    if secrets_detected:
        reasons.append("SECRET_DETECTED")
    return {
        "decision": "READY_FOR_HUMAN_MERGE" if not reasons else "HOLD",
        "reasons": reasons,
        "unexpected_paths": unexpected_paths,
        "missing_tests": missing_tests,
        "human_merge_required": True,
    }
