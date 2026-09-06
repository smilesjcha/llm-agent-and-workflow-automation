import json
from pathlib import Path
import subprocess
import sys

from scripts.day3_pr_guard import (
    changed_paths_from_event,
    is_sensitive_path,
    validate_pr_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_body() -> str:
    return """## Goal

PR 검증기가 민감 파일과 누락된 실행 증거를 차단합니다.

## Scope

- Changed files: `scripts/day3_pr_guard.py`, `tests/test_day3_pr_guard.py`
- Intentionally unchanged: 실제 GitHub 게시와 자동 병합

## Safety and data

- [x] No secret, token, real customer data, or private meeting data is included.
- [x] File, tool, and external-write boundaries remain explicit.
- [x] Human approval is preserved for consequential actions.

## Test evidence

```text
python3 -m pytest -q tests/test_day3_pr_guard.py
```

- Result: `5 passed`

## Review request

- Risk to inspect: 민감 경로 오탐과 PR 본문 누락
- Expected behavior: 안전 항목과 test 결과가 있어야 PASS
- Known limitation: 파일 내용의 secret은 별도 scanner 범위

## Human merge checklist

- [ ] Diff matches the stated goal.
"""


def valid_payload() -> dict:
    return {
        "pull_request": {
            "title": "ci: add a deterministic PR contract",
            "body": valid_body(),
            "base": {"sha": "a" * 40},
            "head": {"sha": "b" * 40},
        }
    }


def test_valid_pr_contract_passes_without_external_access() -> None:
    result = validate_pr_payload(
        valid_payload(), changed_paths=["scripts/day3_pr_guard.py", ".env.sample"]
    )

    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["changed_paths"] == [".env.sample", "scripts/day3_pr_guard.py"]


def test_sensitive_file_name_is_blocked_but_sample_is_allowed() -> None:
    assert is_sensitive_path(".env.sample") is False
    assert is_sensitive_path("config/.env") is True
    assert is_sensitive_path("certs/service.pem") is True

    result = validate_pr_payload(valid_payload(), changed_paths=["config/.env"])

    assert result["status"] == "FAIL"
    assert {item["code"] for item in result["errors"]} == {
        "SENSITIVE_PATH_CHANGED"
    }


def test_missing_safety_and_test_evidence_are_structured_failures() -> None:
    payload = valid_payload()
    payload["pull_request"]["body"] = valid_body().replace("[x]", "[ ]").replace(
        "- Result: `5 passed`", "- Result:"
    )

    result = validate_pr_payload(payload, changed_paths=["src/example.py"])

    assert result["status"] == "FAIL"
    assert {item["code"] for item in result["errors"]} == {
        "PR_SAFETY_ATTESTATION_REQUIRED",
        "PR_TEST_RESULT_REQUIRED",
    }


def test_cli_returns_nonzero_for_non_pr_event(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"issue": {"number": 1}}), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/day3_pr_guard.py"),
            "--event",
            str(event_path),
            "--changed-path",
            "src/example.py",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "EVENT_NOT_PULL_REQUEST" in completed.stdout


def test_git_diff_cannot_target_repository_outside_workspace(tmp_path: Path) -> None:
    try:
        changed_paths_from_event(valid_payload(), repository=tmp_path)
    except ValueError as exc:
        assert str(exc) == "WORKSPACE_PATH_BLOCKED"
    else:
        raise AssertionError("outside repository must be blocked")


def test_optional_codex_review_uses_default_branch_prompt() -> None:
    workflow = (
        ROOT / ".github/workflows/day3-codex-review-optional.yml"
    ).read_text(encoding="utf-8")

    assert "refs/pull/${{ inputs.pr_number }}/merge" in workflow
    assert "github.ref_name == github.event.repository.default_branch" in workflow
    assert (
        'git show "refs/remotes/origin/${DEFAULT_BRANCH}:'
        '.github/codex/prompts/day3_pr_review.md"'
    ) in workflow
    assert "trusted_prompt=\"$RUNNER_TEMP/day3_pr_review.md\"" in workflow
    assert "prompt-file: ${{ steps.trusted_prompt.outputs.prompt_path }}" in workflow
    assert "prompt-file: .github/codex/prompts/day3_pr_review.md" not in workflow


def test_pr_runbook_posts_an_edited_body_copy() -> None:
    runbook = (ROOT / "materials/day3/GitHub_PR_자동화_런북.md").read_text(
        encoding="utf-8"
    )

    assert "cp .github/pull_request_template.md .git/day3-pr-body.md" in runbook
    assert "--body-file .git/day3-pr-body.md" in runbook
    assert "--body-file .github/pull_request_template.md" not in runbook
