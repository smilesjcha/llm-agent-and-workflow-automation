"""Run every required Day 1 software path and save an instructor audit report.

The runner uses subprocess lists instead of a shell so commands and paths are
explicit. It never calls a paid model, sends email, or uploads meeting data.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    name: str
    command: list[str]
    status: str
    return_code: int | None
    stdout_tail: str
    stderr_tail: str
    expected_outputs: list[str]
    missing_outputs: list[str]


def _tail(value: str, *, max_chars: int = 2500) -> str:
    return value[-max_chars:]


def run_check(
    name: str,
    command: Sequence[str],
    *,
    expected_outputs: Sequence[Path] = (),
    timeout_seconds: int = 180,
) -> CheckResult:
    """Execute one check and normalize timeout or process failure."""

    rendered_outputs = [str(path.relative_to(ROOT)) for path in expected_outputs]
    try:
        completed = subprocess.run(
            list(command),
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        missing = [str(path.relative_to(ROOT)) for path in expected_outputs if not path.exists()]
        passed = completed.returncode == 0 and not missing
        return CheckResult(
            name=name,
            command=list(command),
            status="PASS" if passed else "FAIL",
            return_code=completed.returncode,
            stdout_tail=_tail(completed.stdout),
            stderr_tail=_tail(completed.stderr),
            expected_outputs=rendered_outputs,
            missing_outputs=missing,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name=name,
            command=list(command),
            status="TIMEOUT",
            return_code=None,
            stdout_tail=_tail(exc.stdout or ""),
            stderr_tail=_tail(exc.stderr or ""),
            expected_outputs=rendered_outputs,
            missing_outputs=rendered_outputs,
        )


def build_checks(output_dir: Path) -> list[tuple[str, list[str], list[Path]]]:
    python = sys.executable
    langchain_out = output_dir / "langchain_result.json"
    graph_dir = output_dir / "langgraph"
    approve_dir = output_dir / "workflow-approve"
    reject_dir = output_dir / "workflow-reject"
    return [
        (
            "tool_calling",
            [python, "-m", "src.day1_agent"],
            [],
        ),
        (
            "ollama_tool_call_fixture",
            [
                python,
                "-m",
                "src.ollama_tool_agent",
                "--provider",
                "fixture",
                "--out",
                str(output_dir / "ollama-tool-fixture.json"),
            ],
            [output_dir / "ollama-tool-fixture.json"],
        ),
        (
            "ollama_expected_fallback",
            [
                python,
                "-m",
                "src.ollama_tool_agent",
                "--provider",
                "ollama",
                "--out",
                str(output_dir / "ollama-tool-request.json"),
            ],
            [output_dir / "ollama-tool-request.json"],
        ),
        (
            "langchain_lcel_fixture",
            [
                python,
                "-m",
                "src.langchain_lab",
                "--provider",
                "fixture",
                "--out",
                str(langchain_out),
            ],
            [langchain_out],
        ),
        (
            "langgraph_interrupt_resume",
            [
                python,
                "-m",
                "src.langgraph_lab",
                "--draft",
                str(langchain_out),
                "--decision",
                "all",
                "--out",
                str(graph_dir),
            ],
            [
                graph_dir / "langgraph_approve.json",
                graph_dir / "langgraph_edit.json",
                graph_dir / "langgraph_reject.json",
            ],
        ),
        (
            "workflow_approve_ready",
            [
                python,
                "-m",
                "src.workflow_service",
                "--decision",
                "approve",
                "--out",
                str(approve_dir),
            ],
            [approve_dir / "trace.json", approve_dir / "workflow_result.json"],
        ),
        (
            "workflow_reject_hold",
            [
                python,
                "-m",
                "src.workflow_service",
                "--decision",
                "reject",
                "--out",
                str(reject_dir),
            ],
            [reject_dir / "trace.json", reject_dir / "workflow_result.json"],
        ),
        (
            "unit_tests",
            [python, "-m", "pytest", "-q"],
            [],
        ),
    ]


def verify_business_states(output_dir: Path) -> dict[str, object]:
    """Check product states that a zero exit code alone cannot prove."""

    approve = json.loads((output_dir / "workflow-approve/workflow_result.json").read_text())
    reject = json.loads((output_dir / "workflow-reject/workflow_result.json").read_text())
    checks = {
        "approve_graph_ready_for_export": approve["langgraph"]["final_state"]["status"]
        == "READY_FOR_EXPORT",
        "approve_release_gate_ready": approve["evaluation"]["decision"] == "READY",
        "reject_graph_rejected": reject["langgraph"]["final_state"]["status"] == "REJECTED",
        "reject_release_gate_hold": reject["evaluation"]["decision"] == "HOLD",
        "approve_email_blocked": approve["langgraph"]["final_state"]["automatic_email"] is False,
        "reject_email_blocked": reject["langgraph"]["final_state"]["automatic_email"] is False,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/day1-preflight"),
        help="Repository-relative directory for generated evidence.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [
        run_check(name, command, expected_outputs=outputs)
        for name, command, outputs in build_checks(output_dir)
    ]
    process_ok = all(result.status == "PASS" for result in results)
    business_states: dict[str, object]
    if process_ok:
        business_states = verify_business_states(output_dir)
    else:
        business_states = {"status": "SKIPPED", "checks": {}}

    overall = "PASS" if process_ok and business_states["status"] == "PASS" else "FAIL"
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "python": sys.executable,
        "repository": str(ROOT),
        "network_required": False,
        "paid_llm_required": False,
        "external_write": False,
        "status": overall,
        "checks": [asdict(result) for result in results],
        "business_states": business_states,
    }
    report_path = output_dir / "preflight_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": overall, "report": str(report_path)}, ensure_ascii=False))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
