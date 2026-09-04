"""Verify the Day 3 classroom environment without using network credentials."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "output/day3-preflight/preflight_report.json"

REQUIRED_FILES = (
    "requirements-day3.txt",
    "slides/IPA_LLM_Agent_업무자동화_Day3_2026_STUDENT_READY_176p.pptx",
    "output/pdf/IPA_LLM_Agent_업무자동화_Day3_2026_STUDENT_READY_176p.pdf",
    "scripts/slides/build_day3_student_ready.mjs",
    "scripts/slides/day3_student_content.mjs",
    "scripts/build_day3_student_bundle.py",
    "materials/day3/day3_review_intelligence_lab.ipynb",
    "materials/day3/day3_review_intelligence_lab.executed.ipynb",
    "materials/day3/2026_Day3_수강생_실습가이드.md",
    "materials/day3/2026_Day3_강사용_상세교안.md",
    "labs/day3/__init__.py",
    "labs/day3/review_copilot/cli.py",
    "labs/day3/review_copilot/day3.env.example",
    "labs/day3/review_copilot/web_app.py",
    "labs/day3/review_copilot/fixtures/cases.json",
    "labs/day3/review_copilot/fixtures/golden_findings.json",
    "tests/test_day3_review_copilot.py",
    "tests/test_day3_notebook.py",
    "tests/test_day3_pr_guard.py",
    "tests/test_day3_curriculum.py",
    "tests/test_day3_student_bundle.py",
    "design-system/ppt/cha-sungjae-lecture/content-harness/DAY3_MESSAGE_MAP.json",
)

REQUIRED_MODULES = (
    "pytest",
    "pydantic",
    "langchain_core",
    "langgraph",
    "dotenv",
    "jupyter",
    "ipykernel",
)


def _command(*args: str, timeout: int = 180) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    display = list(args)
    if display and display[0] == sys.executable:
        display[0] = "python"
    return {
        "command": " ".join(display),
        "return_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_tail": completed.stdout.strip().splitlines()[-8:],
        "stderr_tail": completed.stderr.strip().splitlines()[-8:],
    }


def build_report(*, full_suite: bool = False) -> dict[str, Any]:
    files = {
        path: (ROOT / path).is_file()
        for path in REQUIRED_FILES
    }
    modules = {
        name: importlib.util.find_spec(name) is not None
        for name in REQUIRED_MODULES
    }
    commands = {
        name: bool(shutil.which(name))
        for name in ("git", "gh", "ollama", "code")
    }
    focused = _command(
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_day3_review_copilot.py",
        "tests/test_day3_notebook.py",
        "tests/test_day3_pr_guard.py",
        "tests/test_day3_curriculum.py",
        "tests/test_day3_student_bundle.py",
    )
    smoke = _command(
        sys.executable,
        "-m",
        "labs.day3.review_copilot.web_app",
        "--smoke-and-exit",
        "--port",
        "0",
    )
    checks: dict[str, Any] = {
        "day3_focused": focused,
        "localhost_smoke": smoke,
    }
    if full_suite:
        checks["day1_regression"] = _command(
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_day1_agent.py",
            "tests/test_langchain_langgraph_lab.py",
            "tests/test_meeting_agent_workflow.py",
            "tests/test_openai_provider.py",
            "tests/test_ollama_tool_agent.py",
        )

    env_ignored = _command("git", "check-ignore", ".env")
    required_ready = (
        all(files.values())
        and all(modules.values())
        and commands["git"]
        and all(item["status"] == "PASS" for item in checks.values())
        and env_ignored["return_code"] == 0
    )
    return {
        "status": "PASS" if required_ready else "FAIL",
        "python": {
            "version": sys.version.split()[0],
            "recommended": "3.12",
            "supported": sys.version_info >= (3, 10),
        },
        "required_files": files,
        "required_modules": modules,
        "commands": {
            "required": {"git": commands["git"]},
            "optional": {key: commands[key] for key in ("gh", "ollama", "code")},
        },
        "checks": checks,
        "secret_boundary": {
            "env_file_ignored": env_ignored["return_code"] == 0,
            "env_values_read": False,
            "env_values_printed": False,
        },
        "safety": {
            "network_call": False,
            "external_write": False,
            "automatic_push": False,
            "automatic_merge": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 3 classroom preflight")
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Day 3 focused checks와 AGENTS.md에서 요구한 Day 1 회귀 suite를 함께 실행",
    )
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    report = build_report(full_suite=args.full_suite)
    target = args.report if args.report.is_absolute() else ROOT / args.report
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "report": str(target.relative_to(ROOT)),
        "external_write": False,
    }, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
