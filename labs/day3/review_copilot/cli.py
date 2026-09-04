"""CLI for inspecting, reviewing, evaluating, and running the Day 3 lab."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from .context_builder import build_context_pack
from .contracts import ReviewPolicy
from .diff_parser import parse_unified_diff
from .errors import stable_error_code
from .evaluation import evaluate_case_set
from .providers import OllamaReviewProvider, ReviewProvider
from .review_engine import deterministic_review
from .test_evidence import collect_focused_test_evidence
from .workflow import run_review_workflow
from .workspace import read_workspace_json, read_workspace_text, write_workspace_json


LAB = Path("labs/day3/review_copilot")
DEFAULT_DIFF = LAB / "fixtures/meeting_export_pr.diff"
PROJECT_CONTEXT = LAB / "fixtures/project_context.json"
PROVIDER_FIXTURE = LAB / "fixtures/provider_fixture.json"
CASE_MANIFEST = LAB / "fixtures/cases.json"
GOLDEN = LAB / "fixtures/golden_findings.json"
DEFAULT_OUTPUT = Path("output/course-labs/day3-v2/student-run")
CASE_ALIASES = {
    "unsafe_dynamic_execution": "unsafe-exec",
    "shell_injection": "shell-injection",
    "external_write": "external-write",
    "broad_exception": "broad-exception",
    "path_escape": "path-escape",
    "secret_logging": "secret-logging",
    "missing_timeout_idempotency": "timeout-idempotency",
    "clean_safe_negative": "safe-negative",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _print(payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _cases(root: Path) -> list[dict[str, str]]:
    payload = read_workspace_json(CASE_MANIFEST, workspace_root=root)
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("CASE_MANIFEST_INVALID")
    return [{"id": str(item["id"]), "diff": str(item["diff"])} for item in cases]


def _case(root: Path, requested: str) -> dict[str, str]:
    case_id = CASE_ALIASES.get(requested, requested)
    for item in _cases(root):
        if item["id"] == case_id:
            return item
    raise ValueError("CASE_NOT_FOUND")


def _provider(name: str) -> ReviewProvider | None:
    if name == "fixture":
        return None
    if name == "ollama":
        return OllamaReviewProvider(
            model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            live_opt_in=os.getenv("OLLAMA_LIVE_OPT_IN") == "1",
        )
    raise ValueError("PROVIDER_NOT_SUPPORTED")


def _run_case(
    root: Path,
    *,
    case_id: str,
    provider_name: str,
    context_max_bytes: int,
    decision: str | None,
    test_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item = _case(root, case_id)
    return run_review_workflow(
        workspace_root=root,
        diff_path=item["diff"],
        project_context_path=PROJECT_CONTEXT,
        fixture_path=PROVIDER_FIXTURE,
        provider=_provider(provider_name),
        context_max_bytes=context_max_bytes,
        decision=decision,
        test_evidence=test_evidence,
        provider_case_id=item["id"],
    )


def _inspect(root: Path, case_id: str) -> dict[str, Any]:
    try:
        item = _case(root, case_id)
        parsed = parse_unified_diff(read_workspace_text(item["diff"], workspace_root=root))
        findings = deterministic_review(parsed)
        return {
            "status": "SUCCESS",
            "case": item["id"],
            "contract": ReviewPolicy().to_dict(),
            "parsed_diff": parsed.to_dict(),
            "findings": [finding.to_dict() for finding in findings],
            "external_write": False,
        }
    except (OSError, TypeError, ValueError) as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "external_write": False,
        }


def _context(root: Path, case_id: str, max_bytes: int) -> dict[str, Any]:
    try:
        item = _case(root, case_id)
        parsed = parse_unified_diff(read_workspace_text(item["diff"], workspace_root=root))
        project = read_workspace_json(PROJECT_CONTEXT, workspace_root=root)
        context = build_context_pack(
            parsed,
            policy=ReviewPolicy(),
            project_context=project,
            max_bytes=max_bytes,
            workspace_root=root,
        )
        return {
            "status": "SUCCESS",
            "case": item["id"],
            "context": context,
            "external_write": False,
        }
    except (OSError, TypeError, ValueError) as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "external_write": False,
        }


def _evaluate(root: Path) -> dict[str, Any]:
    try:
        return {
            "status": "SUCCESS",
            **evaluate_case_set(
                workspace_root=root,
                manifest_path=CASE_MANIFEST,
                golden_path=GOLDEN,
            ),
        }
    except (OSError, TypeError, ValueError) as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "external_write": False,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 3 Review Copilot")
    commands = parser.add_subparsers(dest="command")

    run = commands.add_parser("run", help="8차시 전체 결과를 차시별 JSON으로 저장")
    run.add_argument("--diff", default=str(DEFAULT_DIFF))
    run.add_argument("--output", default=str(DEFAULT_OUTPUT))
    run.add_argument(
        "--decision",
        choices=("approve", "reject"),
        help="사람이 검토한 뒤에만 지정; 생략하면 REVIEW_REQUIRED/HOLD",
    )
    run.add_argument("--provider", choices=("fixture", "ollama"), default="fixture")
    run.add_argument("--context-max-bytes", type=int, default=20_000)
    run.add_argument(
        "--run-tests",
        action="store_true",
        help="고정된 focused pytest를 실행하고 실제 exit code를 결과에 포함",
    )

    inspect = commands.add_parser("inspect", help="한 case의 diff와 finding 확인")
    inspect.add_argument("--case", default="unsafe_dynamic_execution")

    context = commands.add_parser("context", help="최소 context pack 생성")
    context.add_argument("--case", default="external_write")
    context.add_argument("--max-bytes", type=int, default=20_000)

    review = commands.add_parser("review", help="한 case 또는 전체 case 리뷰")
    review.add_argument("--case", default="unsafe_dynamic_execution")
    review.add_argument("--provider", choices=("fixture", "ollama"), default="fixture")
    review.add_argument("--context-max-bytes", type=int, default=20_000)
    review.add_argument(
        "--decision",
        choices=("approve", "reject"),
        help="사람이 검토한 뒤에만 지정; 생략하면 REVIEW_REQUIRED/HOLD",
    )
    review.add_argument("--run-tests", action="store_true")

    commands.add_parser("evaluate", help="8개 golden case 평가")
    commands.add_parser("cases", help="사용 가능한 synthetic case 목록")
    return parser


def main(argv: list[str] | None = None) -> int:
    root = _root()
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if not raw_args:
        raw_args = ["run"]
    elif raw_args[0].startswith("-"):
        raw_args.insert(0, "run")
    args = build_parser().parse_args(raw_args)

    if args.command == "cases":
        _print({"status": "SUCCESS", "cases": _cases(root), "external_write": False})
        return 0
    if args.command == "inspect":
        result = _inspect(root, args.case)
        _print(result)
        return 0 if result["status"] == "SUCCESS" else 2
    if args.command == "context":
        result = _context(root, args.case, args.max_bytes)
        _print(result)
        return 0 if result["status"] == "SUCCESS" else 2
    if args.command == "evaluate":
        result = _evaluate(root)
        _print(result)
        return 0 if result["status"] == "SUCCESS" else 2
    if args.command == "review":
        evidence = (
            collect_focused_test_evidence(workspace_root=root) if args.run_tests else None
        )
        if args.case == "all":
            results = [
                {
                    "case": item["id"],
                    "result": _run_case(
                        root,
                        case_id=item["id"],
                        provider_name=args.provider,
                        context_max_bytes=args.context_max_bytes,
                        decision=args.decision,
                        test_evidence=evidence,
                    ),
                }
                for item in _cases(root)
            ]
            payload = {
                "status": "SUCCESS",
                "case_count": len(results),
                "results": results,
                "external_write": False,
            }
        else:
            payload = _run_case(
                root,
                case_id=args.case,
                provider_name=args.provider,
                context_max_bytes=args.context_max_bytes,
                decision=args.decision,
                test_evidence=evidence,
            )
        _print(payload)
        return 0 if payload["status"] == "SUCCESS" else 2

    evidence = collect_focused_test_evidence(workspace_root=root) if args.run_tests else None
    result = run_review_workflow(
        workspace_root=root,
        diff_path=args.diff,
        project_context_path=PROJECT_CONTEXT,
        fixture_path=PROVIDER_FIXTURE,
        provider=_provider(args.provider),
        decision=args.decision,
        context_max_bytes=args.context_max_bytes,
        test_evidence=evidence,
    )
    if result["status"] != "SUCCESS":
        _print(result)
        return 2

    output_dir = Path(args.output)
    for name, payload in result["stages"].items():
        write_workspace_json(
            output_dir / f"{name}.json",
            payload,
            workspace_root=root,
        )
    _print(
        {
            "status": result["status"],
            "completed_stage": result["completed_stage"],
            "output": str(output_dir),
            "test_evidence": evidence,
            "external_write": result["external_write"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
