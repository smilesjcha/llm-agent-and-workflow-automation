#!/usr/bin/env python3
"""Validate a pull request contract without network access or repository writes.

The GitHub Actions workflow passes ``GITHUB_EVENT_PATH`` to this script.  The
same validator can be exercised locally with a saved, synthetic event fixture
and explicit changed paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Iterable


REQUIRED_SECTIONS = (
    "Goal",
    "Scope",
    "Safety and data",
    "Test evidence",
    "Review request",
    "Human merge checklist",
)
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
HEADING_PATTERN = re.compile(r"(?m)^##\s+(.+?)\s*$")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
CHECKED_BOX_PATTERN = re.compile(r"(?im)^\s*-\s*\[[xX]\]\s+.+$")
SENSITIVE_BASENAMES = {
    ".env",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
SAFE_ENV_EXAMPLES = {".env.example", ".env.sample"}
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def _strip_comments(value: str) -> str:
    return HTML_COMMENT_PATTERN.sub("", value).strip()


def _split_sections(body: str) -> dict[str, str]:
    matches = list(HEADING_PATTERN.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def _field_value(section: str, label: str) -> str:
    match = re.search(
        rf"(?im)^\s*-\s*{re.escape(label)}:\s*(.*?)\s*$",
        section,
    )
    return _strip_comments(match.group(1)) if match else ""


def is_sensitive_path(raw_path: str) -> bool:
    """Return True for secret-bearing file names, never by reading file data."""

    normalized = raw_path.replace("\\", "/").strip("/")
    name = PurePosixPath(normalized).name.lower()
    if name in SAFE_ENV_EXAMPLES:
        return False
    if name in SENSITIVE_BASENAMES or name.startswith(".env."):
        return True
    return PurePosixPath(name).suffix.lower() in SENSITIVE_SUFFIXES


def validate_pr_payload(
    payload: dict[str, Any], *, changed_paths: Iterable[str]
) -> dict[str, Any]:
    """Validate the review evidence required before a human merge decision."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        return {
            "status": "FAIL",
            "errors": [
                {
                    "code": "EVENT_NOT_PULL_REQUEST",
                    "message": "pull_request event payload가 필요합니다.",
                }
            ],
            "warnings": [],
            "changed_paths": [],
        }

    title = str(pull_request.get("title") or "").strip()
    body = str(pull_request.get("body") or "")
    sections = _split_sections(body)
    paths = sorted({str(path).strip() for path in changed_paths if str(path).strip()})

    if not title:
        errors.append({"code": "PR_TITLE_REQUIRED", "message": "PR 제목이 비어 있습니다."})
    elif re.match(r"(?i)^(wip|draft)\b", title):
        warnings.append(
            {
                "code": "DRAFT_TITLE",
                "message": "검토 요청 전 제목의 WIP/Draft 표시를 제거하세요.",
            }
        )

    for heading in REQUIRED_SECTIONS:
        if heading not in sections:
            errors.append(
                {
                    "code": "PR_SECTION_REQUIRED",
                    "message": f"PR 본문에 '## {heading}' 섹션이 필요합니다.",
                }
            )

    if not _strip_comments(sections.get("Goal", "")):
        errors.append(
            {
                "code": "PR_GOAL_REQUIRED",
                "message": "Goal에 변경할 동작을 한 문장으로 적으세요.",
            }
        )

    scope = sections.get("Scope", "")
    if not _field_value(scope, "Changed files"):
        errors.append(
            {
                "code": "PR_CHANGED_FILES_REQUIRED",
                "message": "Scope의 Changed files를 채우세요.",
            }
        )
    if not _field_value(scope, "Intentionally unchanged"):
        errors.append(
            {
                "code": "PR_UNCHANGED_SCOPE_REQUIRED",
                "message": "Scope의 Intentionally unchanged를 채우세요.",
            }
        )

    safety = sections.get("Safety and data", "")
    if len(CHECKED_BOX_PATTERN.findall(safety)) < 3:
        errors.append(
            {
                "code": "PR_SAFETY_ATTESTATION_REQUIRED",
                "message": "Safety and data의 세 항목을 확인한 뒤 체크하세요.",
            }
        )

    test_evidence = sections.get("Test evidence", "")
    if not _field_value(test_evidence, "Result"):
        errors.append(
            {
                "code": "PR_TEST_RESULT_REQUIRED",
                "message": "실행한 명령의 실제 Result를 적으세요.",
            }
        )

    review_request = sections.get("Review request", "")
    if not _field_value(review_request, "Risk to inspect"):
        errors.append(
            {
                "code": "PR_REVIEW_FOCUS_REQUIRED",
                "message": "리뷰어가 우선 확인할 Risk to inspect를 적으세요.",
            }
        )

    sensitive = [path for path in paths if is_sensitive_path(path)]
    if sensitive:
        errors.append(
            {
                "code": "SENSITIVE_PATH_CHANGED",
                "message": "secret 가능성이 있는 경로를 PR에서 제거하세요: "
                + ", ".join(sensitive),
            }
        )

    if not paths:
        warnings.append(
            {
                "code": "NO_CHANGED_PATHS",
                "message": "변경 파일을 확인하지 못했습니다. base/head SHA를 점검하세요.",
            }
        )

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "changed_paths": paths,
    }


def changed_paths_from_event(payload: dict[str, Any], *, repository: Path) -> list[str]:
    """Read changed path names from the local Git checkout; no file content is read."""

    resolved_repository = repository.resolve()
    try:
        resolved_repository.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("WORKSPACE_PATH_BLOCKED") from exc

    pull_request = payload.get("pull_request") or {}
    base_sha = str((pull_request.get("base") or {}).get("sha") or "")
    head_sha = str((pull_request.get("head") or {}).get("sha") or "")
    if not SHA_PATTERN.fullmatch(base_sha) or not SHA_PATTERN.fullmatch(head_sha):
        raise ValueError("PR_BASE_HEAD_SHA_REQUIRED")

    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base_sha,
            head_sha,
            "--",
        ],
        cwd=resolved_repository,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        raise RuntimeError("GIT_DIFF_FAILED")
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _load_event(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("PR_EVENT_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise ValueError("PR_EVENT_OBJECT_REQUIRED")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True, type=Path)
    parser.add_argument("--repository", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Local rehearsal path. Repeat to avoid deriving paths from Git SHAs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_event(args.event)
        changed_paths = args.changed_path or changed_paths_from_event(
            payload, repository=args.repository.resolve()
        )
        result = validate_pr_payload(payload, changed_paths=changed_paths)
    except (ValueError, RuntimeError) as exc:
        result = {
            "status": "FAIL",
            "errors": [{"code": str(exc), "message": "PR 검증 입력을 확인하세요."}],
            "warnings": [],
            "changed_paths": [],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
