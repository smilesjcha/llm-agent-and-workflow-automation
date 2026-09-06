"""Run one fixed, bounded focused test and preserve its real exit code."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import subprocess
import sys
from typing import Any


Runner = Callable[..., subprocess.CompletedProcess[str]]


def collect_focused_test_evidence(
    *,
    workspace_root: str | Path,
    runner: Runner = subprocess.run,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Run only the hard-coded Day 3 test; user text can never become a command."""

    root = Path(workspace_root).resolve()
    test_path = root / "tests/test_day3_review_copilot.py"
    if not test_path.is_file():
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "FOCUSED_TEST_FILE_NOT_FOUND",
            "executed": False,
            "exit_code": None,
            "external_write": False,
        }
    command = [sys.executable, "-m", "pytest", "-q", "tests/test_day3_review_copilot.py"]
    try:
        completed = runner(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "FOCUSED_TEST_TIMEOUT",
            "executed": True,
            "command": "python -m pytest -q tests/test_day3_review_copilot.py",
            "exit_code": None,
            "external_write": False,
        }
    return {
        "status": "PASSED" if completed.returncode == 0 else "FAILED",
        "error_code": None if completed.returncode == 0 else "FOCUSED_TEST_FAILED",
        "executed": True,
        "command": "python -m pytest -q tests/test_day3_review_copilot.py",
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-1000:],
        "external_write": False,
    }


def not_run_evidence() -> dict[str, Any]:
    return {
        "status": "NOT_RUN",
        "error_code": "FOCUSED_TEST_REQUIRED",
        "executed": False,
        "exit_code": None,
        "external_write": False,
    }
