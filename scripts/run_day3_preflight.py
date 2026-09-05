"""Verify Day 3 offline labs and separately report local Codex CLI readiness."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "output/day3-preflight/preflight_report.json"

REQUIRED_CODE_FILES = (
    ".gitignore", "requirements-day1.txt", "requirements-day3.txt",
    "scripts/build_day3_notebook.py", "scripts/build_day3_student_bundle.py",
    "scripts/run_day3_preflight.py", "scripts/day3_pr_guard.py",
    "materials/day3/day3_review_intelligence_lab.ipynb",
    "materials/day3/day3_global_references.json", "materials/day3/글로벌_사례_해설.md",
    "labs/day3/__init__.py",
    "labs/day3/review_copilot/cli.py", "labs/day3/review_copilot/codex_cli.py",
    "labs/day3/review_copilot/exercise.py", "labs/day3/review_copilot/day3.env.example",
    "labs/day3/review_copilot/deep_dive.py",
    "labs/day3/review_copilot/web_app.py",
    "labs/day3/review_copilot/fixtures/cases.json",
    "labs/day3/review_copilot/fixtures/golden_findings.json",
    "labs/day3/review_copilot/fixtures/checkout/requirements.md",
    "labs/day3/review_copilot/fixtures/checkout/checkout_checks.py",
    "labs/day3/review_copilot/fixtures/checkout/starter/checkout.py",
    "labs/day3/review_copilot/fixtures/checkout/solution/checkout.py",
    "tests/test_day3_review_copilot.py", "tests/test_day3_notebook.py",
    "tests/test_day3_deep_dive.py",
    "tests/test_day3_pr_guard.py", "tests/test_day3_curriculum.py",
    "tests/test_day3_preflight.py", "tests/test_day3_student_bundle.py",
)
REQUIRED_CLASSROOM_FILES = (
    "slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx",
    "output/pdf/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pdf",
    "scripts/slides/build_day3_codex_cli.mjs", "scripts/slides/day3_codex_content.mjs",
    "scripts/slides/day3_ai_enrichment.mjs",
    "materials/day3/심화_4개차시_강사운영안.md",
    "materials/day3/day3_review_intelligence_lab.executed.ipynb",
    "materials/day3/2026_Day3_수강생_실습가이드.md",
    "materials/day3/2026_Day3_강사용_상세교안.md",
    "materials/day3/day3_redesign_curriculum.json",
    "materials/day3/코드리뷰_Agent_아키텍처.md",
    "assets/components/day3/master-code-review-agent.mmd",
)
REQUIRED_FILES = REQUIRED_CODE_FILES + REQUIRED_CLASSROOM_FILES
REQUIRED_MODULES = (
    "pytest", "pydantic", "langchain_core", "langgraph", "dotenv", "jupyter", "ipykernel",
)
OFFLINE_TESTS = (
    "tests/test_day3_review_copilot.py", "tests/test_day3_pr_guard.py",
    "tests/test_day3_deep_dive.py",
    "tests/test_day3_preflight.py", "tests/test_day3_student_bundle.py",
)
CLASSROOM_TESTS = ("tests/test_day3_notebook.py", "tests/test_day3_curriculum.py")
DAY1_TESTS = (
    "tests/test_day1_agent.py", "tests/test_langchain_langgraph_lab.py",
    "tests/test_meeting_agent_workflow.py", "tests/test_openai_provider.py",
    "tests/test_ollama_tool_agent.py",
)


def _command(*args: str, root: Path = ROOT, timeout: int = 180) -> dict[str, Any]:
    display = list(args)
    if display and display[0] == sys.executable:
        display[0] = "python"
    try:
        completed = subprocess.run(
            args, cwd=root, text=True, capture_output=True, check=False, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": " ".join(display), "return_code": None, "status": "FAIL",
            "error_code": "COMMAND_TIMEOUT" if isinstance(exc, subprocess.TimeoutExpired) else "COMMAND_START_FAILED",
            "stdout_tail": [], "stderr_tail": [],
        }
    return {
        "command": " ".join(display), "return_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
    }


def codex_readiness() -> dict[str, Any]:
    """Ask the CLI for status only; discard its text and never open auth files."""
    executable = shutil.which("codex")
    result: dict[str, Any] = {
        "installed": executable is not None, "login_ready": False,
        "status": "NOT_INSTALLED", "inference_location": "cloud",
        "required_for_offline_checks": False, "model_request_sent": False,
        "credential_values_recorded": False,
    }
    if executable is None:
        return result
    # Only normal login environment values are passed; API key values are excluded.
    allowed = (
        "PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT",
        "WINDIR", "TMP", "TEMP", "TMPDIR", "LANG", "LC_ALL", "CODEX_HOME",
    )
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    try:
        completed = subprocess.run(
            [executable, "login", "status"], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=10, check=False, env=environment,
        )
    except subprocess.TimeoutExpired:
        result["status"] = "STATUS_TIMEOUT"
    except OSError:
        result["status"] = "STATUS_UNAVAILABLE"
    else:
        result["login_ready"] = completed.returncode == 0
        result["status"] = "READY" if completed.returncode == 0 else "LOGIN_REQUIRED"
    return result


def _env_ignore_check(root: Path) -> dict[str, Any]:
    """An extracted ZIP has no Git metadata, so inspect its public ignore rule."""
    ignore_path = root / ".gitignore"
    inside = ignore_path.resolve().is_relative_to(root.resolve())
    rules = ignore_path.read_text(encoding="utf-8").splitlines() if inside and ignore_path.is_file() else []
    normalized = [line.strip() for line in rules if line.strip() and not line.lstrip().startswith("#")]
    protected = False
    for rule in normalized:
        negated = rule.startswith("!")
        pattern = rule[1:] if negated else rule
        pattern = pattern.lstrip("/")
        while pattern.startswith("**/"):
            pattern = pattern[3:]
        # Only the root .env file is in scope, so directory rules cannot match it.
        if "/" not in pattern and fnmatch.fnmatchcase(".env", pattern):
            protected = not negated
    return {
        "env_file_ignored": protected, "verification": "public_gitignore_rule",
        "git_metadata_required": False, "env_values_read": False, "env_values_printed": False,
    }


def build_report(*, full_suite: bool = False, code_only: bool = False, root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    required_paths = REQUIRED_CODE_FILES if code_only else REQUIRED_FILES
    files = {path: (root / path).is_file() for path in required_paths}
    modules = {name: importlib.util.find_spec(name) is not None for name in REQUIRED_MODULES}
    commands = {name: bool(shutil.which(name)) for name in ("git", "gh", "codex", "code")}
    tests = OFFLINE_TESTS if code_only else OFFLINE_TESTS + CLASSROOM_TESTS
    checks: dict[str, Any] = {
        "day3_focused": _command(sys.executable, "-m", "pytest", "-q", *tests, root=root),
        "localhost_smoke": _command(
            sys.executable, "-m", "labs.day3.review_copilot.web_app",
            "--smoke-and-exit", "--port", "0", root=root,
        ),
    }
    if full_suite:
        checks["day1_regression"] = _command(sys.executable, "-m", "pytest", "-q", *DAY1_TESTS, root=root)
    boundary = _env_ignore_check(root)
    ready = (
        all(files.values()) and all(modules.values()) and sys.version_info >= (3, 10)
        and (code_only or commands["git"])
        and all(item["status"] == "PASS" for item in checks.values())
        and boundary["env_file_ignored"]
    )
    return {
        "status": "PASS" if ready else "FAIL", "mode": "code-only" if code_only else "classroom",
        "python": {"version": sys.version.split()[0], "recommended": "3.12", "supported": sys.version_info >= (3, 10)},
        "required_files": files, "required_modules": modules,
        "commands": {
            "required": {} if code_only else {"git": commands["git"]},
            "optional": {key: commands[key] for key in ("gh", "codex", "code")},
        },
        "codex_cli": codex_readiness(), "checks": checks, "secret_boundary": boundary,
        "safety": {"network_call": False, "external_write": False, "automatic_push": False, "automatic_merge": False},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Day 3 classroom preflight")
    parser.add_argument("--full-suite", action="store_true", help="전체 저장소에서 Day 1 회귀 테스트도 실행")
    parser.add_argument("--code-only", action="store_true", help="학생용 ZIP의 코드·테스트·Localhost 검증, PPT/PDF는 제외")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args(argv)
    if args.code_only and args.full_suite:
        parser.error("--code-only cannot include the full repository Day 1 suite")
    target = (args.report if args.report.is_absolute() else ROOT / args.report).resolve()
    if not target.is_relative_to(ROOT.resolve()):
        parser.error("report must remain inside the workspace")
    report = build_report(full_suite=args.full_suite, code_only=args.code_only)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "mode": report["mode"],
        "report": str(target.relative_to(ROOT)), "codex_cli": report["codex_cli"]["status"],
        "external_write": False,
    }, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
