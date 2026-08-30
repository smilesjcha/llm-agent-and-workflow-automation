from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK_CHECK = ROOT / "labs/day2/codex-task/task_check.py"
SPEC = importlib.util.spec_from_file_location("day2_codex_task_check", TASK_CHECK)
assert SPEC and SPEC.loader
TASK_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TASK_MODULE)
evaluate = TASK_MODULE.evaluate
safe_report_path = TASK_MODULE.safe_report_path


def test_codex_task_starts_with_one_visible_failure_contract() -> None:
    report = evaluate("starter.review_policy")
    assert report["status"] == "FAIL"
    assert report["external_write"] is False
    assert any(case["status"] == "FAIL" for case in report["cases"])


def test_codex_task_reference_solution_passes_all_cases() -> None:
    report = evaluate("solution.review_policy")
    assert report["status"] == "PASS"
    assert report["human_review_required_for_external_action"] is True
    assert all(case["status"] == "PASS" for case in report["cases"])


def test_codex_task_report_stays_in_workspace(tmp_path: Path) -> None:
    assert safe_report_path(Path("output/course-labs/day2-v2/student-run/05_codex_run.json")).is_relative_to(ROOT)
    with pytest.raises(ValueError, match="DAY2_CODEX_REPORT_OUTSIDE_WORKSPACE"):
        safe_report_path(tmp_path / "outside.json")
