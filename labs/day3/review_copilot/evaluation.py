"""Golden-set evaluation for eight synthetic Day 3 review cases."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .diff_parser import parse_unified_diff
from .review_engine import deterministic_review
from .workspace import read_workspace_json, read_workspace_text


FindingKey = tuple[str, int, str]


def _key(payload: dict[str, Any]) -> FindingKey:
    return (str(payload["path"]), int(payload["line"]), str(payload["rule_id"]))


def evaluate_case_set(
    *,
    workspace_root: str | Path,
    manifest_path: str | Path,
    golden_path: str | Path,
) -> dict[str, Any]:
    """Evaluate findings and expected parser failures without an LLM call."""

    manifest = read_workspace_json(manifest_path, workspace_root=workspace_root)
    golden = read_workspace_json(golden_path, workspace_root=workspace_root)
    cases = manifest.get("cases")
    expected_cases = golden.get("cases")
    if not isinstance(cases, list) or not isinstance(expected_cases, dict):
        raise ValueError("EVALUATION_FIXTURE_INVALID")

    true_positive = false_positive = false_negative = 0
    expected_failures_passed = 0
    results: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case["id"])
        expected = expected_cases.get(case_id)
        if not isinstance(expected, dict):
            raise ValueError(f"GOLDEN_CASE_MISSING:{case_id}")
        diff_text = read_workspace_text(case["diff"], workspace_root=workspace_root)
        expected_error = expected.get("error_code")
        try:
            parsed = parse_unified_diff(diff_text)
            actual_findings = [item.to_dict() for item in deterministic_review(parsed)]
            actual_error = None
        except ValueError as exc:
            actual_findings = []
            actual_error = str(exc)

        if expected_error:
            passed = actual_error == expected_error
            expected_failures_passed += int(passed)
            results.append(
                {
                    "id": case_id,
                    "status": "PASS" if passed else "FAIL",
                    "expected_error": expected_error,
                    "actual_error": actual_error,
                }
            )
            continue

        expected_keys = {_key(item) for item in expected.get("findings", [])}
        actual_keys = {_key(item) for item in actual_findings}
        tp = len(expected_keys & actual_keys)
        fp = len(actual_keys - expected_keys)
        fn = len(expected_keys - actual_keys)
        true_positive += tp
        false_positive += fp
        false_negative += fn
        results.append(
            {
                "id": case_id,
                "status": "PASS" if not fp and not fn and actual_error is None else "FAIL",
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "actual_error": actual_error,
            }
        )

    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 1.0
    recall = true_positive / recall_denominator if recall_denominator else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    error_case_count = sum(
        1 for value in expected_cases.values() if isinstance(value, dict) and value.get("error_code")
    )
    all_cases_passed = all(result["status"] == "PASS" for result in results)
    return {
        "gate_name": "rule_baseline_gate",
        "evaluation_scope": "deterministic_rule_baseline_only",
        "case_count": len(cases),
        "case_passed": sum(result["status"] == "PASS" for result in results),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "expected_failure_cases": error_case_count,
        "expected_failure_cases_passed": expected_failures_passed,
        "release_decision": "READY" if all_cases_passed and f1 >= 0.9 else "HOLD",
        "results": results,
        "external_write": False,
    }
