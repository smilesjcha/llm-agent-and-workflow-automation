"""Runnable checkout service: reproduce, review, edit, and retest real Python."""

from __future__ import annotations

import difflib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from .codex_cli import CodexCLIReviewProvider
from .diff_parser import parse_unified_diff
from .providers import FixtureReviewProvider, ReviewProvider, run_provider
from .review_engine import merge_grounded_candidates
from .safety import redact_secret_like_text
from .workspace import read_workspace_text, resolve_workspace_path, write_workspace_json


DEFAULT_EXERCISE = "output/day3-redesign/student-service"
_TEMPLATE = "labs/day3/review_copilot/fixtures/checkout"


def _directory(workspace_root: str | Path, exercise_dir: str | Path) -> Path:
    directory = resolve_workspace_path(exercise_dir, workspace_root=workspace_root)
    marker = resolve_workspace_path(directory / ".day3-exercise", workspace_root=workspace_root)
    if not marker.is_file() or marker.read_text(encoding="utf-8") != "checkout-v1\n":
        raise ValueError("DAY3_EXERCISE_MARKER_REQUIRED")
    return directory


def prepare_exercise(
    *, workspace_root: str | Path, output_dir: str | Path = DEFAULT_EXERCISE,
) -> dict[str, Any]:
    """Copy public templates once. Re-running never overwrites student edits."""
    directory = resolve_workspace_path(output_dir, workspace_root=workspace_root, must_exist=False)
    if directory == Path(workspace_root).resolve():
        raise ValueError("DAY3_EXERCISE_SUBDIRECTORY_REQUIRED")
    marker = directory / ".day3-exercise"
    if directory.exists() and any(directory.iterdir()) and not marker.is_file():
        raise ValueError("DAY3_EXERCISE_NONEMPTY_DIRECTORY")
    if marker.exists():
        _directory(workspace_root, output_dir)
    files = {
        "starter/checkout.py": f"{_TEMPLATE}/starter/checkout.py",
        "solution/checkout.py": f"{_TEMPLATE}/solution/checkout.py",
        "starter/checkout_checks.py": f"{_TEMPLATE}/checkout_checks.py",
        "solution/checkout_checks.py": f"{_TEMPLATE}/checkout_checks.py",
        "requirements.md": f"{_TEMPLATE}/requirements.md",
    }
    # Resolve every target before creating anything, including symlink boundaries.
    targets = {
        name: resolve_workspace_path(directory / name, workspace_root=workspace_root, must_exist=False)
        for name in [*files, ".day3-exercise"]
    }
    created = []
    for name, template in files.items():
        target = targets[name]
        if not target.exists():
            content = read_workspace_text(template, workspace_root=workspace_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            created.append(name)
    if not targets[".day3-exercise"].exists():
        targets[".day3-exercise"].write_text("checkout-v1\n", encoding="utf-8")
    return {
        "status": "SUCCESS", "exercise_dir": str(directory),
        "starter_dir": str(directory / "starter"), "solution_dir": str(directory / "solution"),
        "requirements_path": str(directory / "requirements.md"), "created_files": created,
        "student_edits_preserved": True,
    }


def _version_dir(workspace_root: str | Path, exercise_dir: str | Path, version: str) -> Path:
    if version not in {"starter", "solution"}:
        raise ValueError("DAY3_EXERCISE_VERSION_INVALID")
    directory = _directory(workspace_root, exercise_dir)
    version_dir = resolve_workspace_path(directory / version, workspace_root=workspace_root)
    for name in ("checkout.py", "checkout_checks.py"):
        resolve_workspace_path(version_dir / name, workspace_root=workspace_root)
    return version_dir


def run_exercise_tests(
    *, workspace_root: str | Path, exercise_dir: str | Path = DEFAULT_EXERCISE,
    version: str = "starter",
) -> dict[str, Any]:
    """Execute the student's actual file in a fresh Python process."""
    directory = _version_dir(workspace_root, exercise_dir, version)
    command = [sys.executable, "-B", "checkout_checks.py"]
    try:
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=20, check=False)
    except subprocess.TimeoutExpired:
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_TEST_TIMEOUT", "executed": True}
    except OSError:
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_TEST_START_FAILED", "executed": False}
    stdout, _ = redact_secret_like_text(result.stdout[-20_000:])
    stderr, _ = redact_secret_like_text(result.stderr[-20_000:])
    count = re.search(r"Ran (\d+) tests?", stderr)
    cases = [
        {"name": name, "status": "PASSED" if outcome == "ok" else outcome}
        for name, outcome in re.findall(r"^(test_\w+) \(.+\) \.\.\. (ok|FAIL|ERROR)$", stderr, re.MULTILINE)
    ]
    test_count = int(count.group(1)) if count else None
    complete_evidence = test_count is not None and test_count > 0 and len(cases) == test_count
    if result.returncode == 0 and not complete_evidence:
        return {
            "status": "EXPECTED_FAILURE", "error_code": "NO_TEST_EVIDENCE",
            "exit_code": 0, "executed": True, "command": "python -B checkout_checks.py",
            "version": version, "stdout": stdout, "stderr": stderr,
            "test_count": test_count, "cases": cases, "external_write": False,
        }
    return {
        "status": "PASSED" if result.returncode == 0 else "FAILED",
        "exit_code": result.returncode, "executed": True,
        "command": "python -B checkout_checks.py", "version": version,
        "stdout": stdout, "stderr": stderr,
        "test_count": test_count, "external_write": False,
        "cases": cases,
    }


def run_exercise_demo(
    *, workspace_root: str | Path, exercise_dir: str | Path = DEFAULT_EXERCISE,
    version: str = "starter", total_won: int = 10_000, coupon_won: int = 15_000,
) -> dict[str, Any]:
    """Run checkout.py and return a receipt, without making a payment."""
    directory = _version_dir(workspace_root, exercise_dir, version)
    code = (
        "import json,sys; from checkout import calculate_checkout; "
        "values=json.loads(sys.argv[1]); "
        "print(json.dumps(calculate_checkout(**values),ensure_ascii=False))"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-c", code, json.dumps({"total_won": total_won, "coupon_won": coupon_won})],
            cwd=directory, capture_output=True, text=True, timeout=10, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_DEMO_TIMEOUT"}
    except OSError:
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_DEMO_START_FAILED"}
    if result.returncode:
        error_code = "EXERCISE_DEMO_FAILED"
        for known in ("MONEY_NON_NEGATIVE_REQUIRED", "MONEY_INTEGER_REQUIRED"):
            if known in result.stderr:
                error_code = known
        return {"status": "EXPECTED_FAILURE", "error_code": error_code, "version": version}
    try:
        receipt = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_RECEIPT_INVALID"}
    fields = {"total_won", "coupon_applied_won", "shipping_won", "payable_won"}
    if not isinstance(receipt, dict) or set(receipt) != fields or any(type(value) is not int for value in receipt.values()):
        return {"status": "EXPECTED_FAILURE", "error_code": "EXERCISE_RECEIPT_INVALID"}
    return {"status": "SUCCESS", "version": version, "result": receipt, "actual_payment": False}


def exercise_diff(
    *, workspace_root: str | Path, exercise_dir: str | Path = DEFAULT_EXERCISE,
    version: str = "starter",
) -> str:
    """Starter is a proposed new file; solution shows the repair against starter."""
    directory = _version_dir(workspace_root, exercise_dir, version)
    current = read_workspace_text(directory / "checkout.py", workspace_root=workspace_root)
    before = "" if version == "starter" else read_workspace_text(
        directory.parent / "starter/checkout.py", workspace_root=workspace_root,
    )
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), current.splitlines(keepends=True),
        fromfile="a/checkout.py", tofile="b/checkout.py",
    ))


def _fixture_candidates(parsed: Any) -> list[dict[str, Any]]:
    examples = {
        "return total_won - coupon_won": (
            "coupon-cap", "쿠폰이 상품 금액을 초과할 때 음수 결제액", "10,000원 상품에 15,000원 쿠폰을 적용하면 상품 금액이 -5,000원이 됩니다.",
            "0 이상 원 단위 정수를 검사한 뒤 할인액을 상품 금액 이하로 제한합니다.",
        ),
        "shipping = 0 if total_won >= 50_000 else 3_000": (
            "shipping-after-discount", "할인 전 금액에 적용한 무료 배송", "50,000원 상품에 10,000원 쿠폰을 적용해도 배송비가 면제됩니다. 정책상 3,000원이 필요합니다.",
            "무료 배송 기준을 total_won 대신 할인 후 payment로 계산합니다.",
        ),
    }
    result = []
    for line in parsed.added_lines:
        if line.text.strip() not in examples:
            continue
        rule_id, title, impact, correction = examples[line.text.strip()]
        result.append({
            "path": line.path, "line": line.line, "severity": "P1", "title": title,
            "impact": impact, "correction": correction, "rule_id": rule_id, "confidence": 1.0,
        })
    return result


def checkout_fixture_provider(
    *, workspace_root: str | Path, exercise_dir: str | Path = DEFAULT_EXERCISE,
) -> FixtureReviewProvider:
    """Explicitly selected classroom replay; never presented as a Codex run."""
    parsed = parse_unified_diff(exercise_diff(workspace_root=workspace_root, exercise_dir=exercise_dir))
    return FixtureReviewProvider({"checkout": _fixture_candidates(parsed)})


def review_exercise(
    *, workspace_root: str | Path, exercise_dir: str | Path = DEFAULT_EXERCISE,
    provider: ReviewProvider | None = None, allow_fallback: bool = False,
    review_instructions: str | None = None,
) -> dict[str, Any]:
    """Review the working starter and save human-readable, line-grounded feedback."""
    directory = _directory(workspace_root, exercise_dir)
    diff_text = exercise_diff(workspace_root=workspace_root, exercise_dir=exercise_dir)
    parsed = parse_unified_diff(diff_text)
    evidence = run_exercise_tests(workspace_root=workspace_root, exercise_dir=exercise_dir)
    prompt = {
        "case_id": "checkout", "contract": "ReviewFinding",
        "requirements": read_workspace_text(directory / "requirements.md", workspace_root=workspace_root),
        "added_lines": [line.to_dict() for line in parsed.added_lines],
        "test_evidence": evidence,
    }
    if review_instructions is not None:
        if not isinstance(review_instructions, str) or not review_instructions.strip() or len(review_instructions) > 30_000:
            raise ValueError("REVIEW_INSTRUCTIONS_INVALID")
        prompt["review_instructions"] = review_instructions
    fixture = FixtureReviewProvider({"checkout": _fixture_candidates(parsed)})
    requested = provider or CodexCLIReviewProvider()
    provider_result = run_provider(requested=requested, fallback=fixture, prompt=prompt, allow_fallback=allow_fallback)
    draft = merge_grounded_candidates(parsed, provider_result)
    lines = [
        "# 쿠폰 결제 서비스 코드 리뷰", "",
        f"- 실제 사용 Provider: {provider_result.get('provider_used') or '실행 실패'}",
        f"- 모델 선택: {provider_result.get('model')}",
        f"- 테스트: {evidence['status']} · exit code {evidence.get('exit_code')}",
        f"- 대체 실행 사유: {provider_result.get('fallback_reason') or '없음'}", "",
    ]
    if provider_result["status"] != "SUCCESS":
        lines += [f"실행 오류: {provider_result.get('error_code')}", ""]
    for finding in draft.findings:
        lines += [
            f"## [{finding.severity}] {finding.title}", "",
            f"`{finding.path}:{finding.line}` · `{finding.rule_id}`", "",
            f"- 재현 조건과 영향: {finding.impact}", f"- 코드 근거: `{finding.evidence}`",
            f"- 수정 제안: {finding.correction}", "",
        ]
    lines += ["## 다음 작업", "", "리뷰 중 수정할 항목을 선택하고 starter/checkout.py를 수정한 뒤 같은 테스트를 다시 실행합니다.", ""]
    markdown = "\n".join(lines)
    report_path = resolve_workspace_path(directory / "review.md", workspace_root=workspace_root, must_exist=False)
    report_path.write_text(markdown, encoding="utf-8")
    diff_path = resolve_workspace_path(directory / "changed.diff", workspace_root=workspace_root, must_exist=False)
    diff_path.write_text(diff_text, encoding="utf-8")
    result = {
        "status": provider_result["status"], "provider": provider_result, "review": draft.to_dict(),
        "markdown": markdown, "review_path": str(report_path), "diff_text": diff_text,
        "test_evidence": evidence, "execution": getattr(requested, "last_run", {}),
        "external_write": False,
    }
    write_workspace_json(directory / "review.json", result, workspace_root=workspace_root)
    return result
