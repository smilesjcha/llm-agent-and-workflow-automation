"""Deterministic checker for the Day 2 Codex task; no network or external write."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import importlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TASK_ROOT = Path(__file__).resolve().parent
CASES = (
    ({"action": "local_draft", "evidence_errors": []}, False, "local_draft"),
    ({"action": "email", "evidence_errors": []}, True, "email_requires_review"),
    ({"action": "notion", "evidence_errors": []}, True, "notion_requires_review"),
    ({"action": "local_draft", "evidence_errors": ["UNKNOWN_EVIDENCE:s999"]}, True, "evidence_error"),
)


def safe_report_path(path: Path) -> Path:
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    root = ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("DAY2_CODEX_REPORT_OUTSIDE_WORKSPACE")
    return resolved


def evaluate(module_name: str) -> dict[str, Any]:
    sys.path.insert(0, str(TASK_ROOT))
    try:
        module = importlib.import_module(module_name)
        policy = module.requires_human_review
        cases = []
        for request, expected, name in CASES:
            observed = policy(request)
            cases.append(
                {
                    "name": name,
                    "expected": expected,
                    "observed": observed,
                    "status": "PASS" if observed is expected else "FAIL",
                }
            )
    finally:
        if sys.path and sys.path[0] == str(TASK_ROOT):
            sys.path.pop(0)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "PASS" if all(case["status"] == "PASS" for case in cases) else "FAIL",
        "module": module_name,
        "cases": cases,
        "human_review_required_for_external_action": all(
            case["observed"] is True for case in cases if "requires_review" in case["name"]
        ),
        "external_write": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", default="starter.review_policy")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = evaluate(args.module)
    if args.report:
        output = safe_report_path(args.report)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
