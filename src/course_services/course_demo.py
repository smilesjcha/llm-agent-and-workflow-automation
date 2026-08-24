"""Deterministic Day 2-5 demo bundles for class openings and notebooks.

The bundles are generated from the same fixtures and service functions used in
the labs. They never contact an external service and never perform a real
GitHub write.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.course_services.eval_service import evaluate_review_findings, release_gate
from src.course_services.github_service import (
    InMemoryIdempotencyStore,
    load_pr_fixture,
    prepare_review_comment,
    publish_review_comment,
)
from src.course_services.meeting_service import (
    prepare_transcript_for_summary,
    validate_action_evidence,
)
from src.course_services.review_service import run_review_service
from src.course_services.service_router import route_service_request
from src.meeting_demo import ensure_workspace_path


SUPPORTED_DAYS = frozenset({2, 3, 4, 5})


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _day2(root: Path) -> dict[str, Any]:
    transcript_path = root / "data/meeting_sample_ko_12min.txt"
    expected_path = root / "data/meeting_sample_ko_12min_expected.json"
    transcript = transcript_path.read_text(encoding="utf-8")
    prepared = prepare_transcript_for_summary(transcript, max_chars=900)
    expected = _read_json(expected_path)
    known_ids = {segment["id"] for segment in prepared["segments"]}
    evidence_errors = validate_action_evidence(
        expected["action_items"], known_segment_ids=known_ids
    )
    boundary_errors = validate_action_evidence(
        [{"task": "근거가 없는 자동 발행", "evidence_ids": ["s999"]}],
        known_segment_ids=known_ids,
    )
    policy = expected["policy"]
    ready = (
        prepared["status"] == "SUCCESS"
        and not evidence_errors
        and policy["automatic_publish"] is False
        and policy["requires_human_approval"] is True
    )
    return {
        "day": 2,
        "service": "Meeting Intelligence Service",
        "status": "SUCCESS",
        "decision": "READY" if ready else "HOLD",
        "input": {
            "audio": "data/meeting_sample_ko_12min.wav",
            "transcript": str(transcript_path.relative_to(root)),
            "synthetic": True,
        },
        "stages": [
            {"name": "audio_contract", "status": "READY", "artifact": "audio_metadata.json"},
            {"name": "transcript_segments", "status": prepared["status"], "artifact": "transcript.json"},
            {"name": "evidence_chunks", "status": "SUCCESS", "artifact": "meeting_chunks.json"},
            {"name": "meeting_brief", "status": "VALIDATED", "artifact": "meeting_brief.json"},
        ],
        "metrics": {
            "segment_count": len(prepared["segments"]),
            "chunk_count": len(prepared["chunks"]),
            "action_item_count": len(expected["action_items"]),
            "evidence_error_count": len(evidence_errors),
        },
        "result": {
            "title": expected["title"],
            "summary": expected["summary"],
            "action_items": expected["action_items"],
            "policy": policy,
        },
        "boundary_case": {
            "status": "HOLD",
            "errors": boundary_errors,
            "external_write": False,
        },
        "external_write": False,
        "human_approval_required": True,
    }


def _day3(root: Path) -> dict[str, Any]:
    diff_path = root / "data/day3_review_cases/unsafe_pr.diff"
    expected_path = root / "data/day5_eval/golden_review_findings.json"
    report = run_review_service(diff_path.read_text(encoding="utf-8"))
    metrics = evaluate_review_findings(report["findings"], _read_json(expected_path))
    gate = release_gate(
        review_metrics=metrics,
        safety_passed=report["automatic_publish"] is False,
        latency_seconds=0.2,
    )
    empty_diff = run_review_service("")
    return {
        "day": 3,
        "service": "Review Intelligence Service",
        "status": "SUCCESS",
        "decision": "READY_FOR_HUMAN_REVIEW" if gate["decision"] == "READY" else "HOLD",
        "input": {"diff": str(diff_path.relative_to(root)), "synthetic": True},
        "stages": [
            {"name": "unified_diff", "status": "PARSED", "artifact": "parsed_hunks.json"},
            {"name": "deterministic_review", "status": report["status"], "artifact": "review_report.json"},
            {"name": "offline_evaluation", "status": gate["decision"], "artifact": "review_eval.json"},
        ],
        "metrics": {**metrics, "finding_count": len(report["findings"])},
        "result": report,
        "boundary_case": {
            "status": empty_diff["status"],
            "error_code": empty_diff["error_code"],
            "automatic_publish": empty_diff["automatic_publish"],
        },
        "external_write": False,
        "human_merge_required": True,
    }


def _day4(root: Path) -> dict[str, Any]:
    fixture = load_pr_fixture(root / "data/day4_github/pr_fixture.json", workspace_root=root)
    diff_text = (root / fixture["diff"]).read_text(encoding="utf-8")
    report = run_review_service(diff_text)
    target = {key: fixture[key] for key in ("repository", "number", "head_sha")}
    dry_run = prepare_review_comment(report=report, target=target, dry_run=True)
    approval_plan = prepare_review_comment(report=report, target=target, dry_run=False)
    store = InMemoryIdempotencyStore()
    calls: list[dict[str, Any]] = []

    def fake_publisher(_target: Any, body: str) -> dict[str, Any]:
        calls.append({"body_length": len(body)})
        return {"id": 101, "url": "https://example.invalid/reviews/101"}

    rejected = publish_review_comment(
        plan=approval_plan,
        human_approved=False,
        publisher=fake_publisher,
        store=store,
    )
    first = publish_review_comment(
        plan=approval_plan,
        human_approved=True,
        publisher=fake_publisher,
        store=store,
    )
    second = publish_review_comment(
        plan=approval_plan,
        human_approved=True,
        publisher=fake_publisher,
        store=store,
    )
    return {
        "day": 4,
        "service": "PR Review Automation",
        "status": "SUCCESS",
        "decision": "READY_FOR_SANDBOX_REVIEW",
        "input": {"fixture": "data/day4_github/pr_fixture.json", "synthetic": True},
        "stages": [
            {"name": "target_validation", "status": "SUCCESS", "artifact": "pr_target.json"},
            {"name": "review_dry_run", "status": dry_run["status"], "artifact": "review_comment_plan.json"},
            {"name": "human_approval", "status": "RECORDED", "artifact": "review_decision.json"},
            {"name": "idempotency", "status": "SUCCESS", "artifact": "day4_audit_record.json"},
        ],
        "metrics": {
            "finding_count": len(report["findings"]),
            "fake_publisher_call_count": len(calls),
            "duplicate_reused": second["remote_result"]["reused"],
        },
        "result": {
            "target": target,
            "dry_run": dry_run,
            "rejected": rejected,
            "approved_once": first,
            "duplicate_request": second,
            "publisher_mode": "fake",
        },
        "boundary_case": {
            "status": rejected["status"],
            "error_code": rejected["error_code"],
            "real_external_write": False,
        },
        "external_write": False,
        "human_approval_required": True,
    }


def _day5(root: Path) -> dict[str, Any]:
    meeting_path = root / "data/meeting_sample_ko.txt"
    diff_path = root / "data/day3_review_cases/unsafe_pr.diff"
    meeting = route_service_request(
        input_kind="meeting_transcript", source_path=meeting_path, workspace_root=root
    )
    review = route_service_request(
        input_kind="code_diff", source_path=diff_path, workspace_root=root
    )
    expected = _read_json(root / "data/day5_eval/golden_review_findings.json")
    metrics = evaluate_review_findings(review["result"]["findings"], expected)
    gate = release_gate(review_metrics=metrics, safety_passed=True, latency_seconds=0.2)
    hold = release_gate(
        review_metrics={"precision": 0.7, "recall": 0.6},
        safety_passed=False,
        latency_seconds=42.0,
    )
    trace = {
        "run_name": "agent-operations-console",
        "data_classification": "synthetic",
        "spans": [
            {"name": "route_meeting", "status": meeting["status"], "latency_ms": 12.1},
            {"name": "route_code_review", "status": review["status"], "latency_ms": 18.4},
            {"name": "offline_evaluation", "status": gate["decision"], "latency_ms": 2.8},
        ],
        "raw_content_uploaded": False,
    }
    return {
        "day": 5,
        "service": "Agent Operations Console",
        "status": "SUCCESS",
        "decision": gate["decision"],
        "input": {"kinds": ["meeting_transcript", "code_diff"], "synthetic": True},
        "stages": [
            {"name": "explicit_router", "status": "SUCCESS", "artifact": "unified_service_result.json"},
            {"name": "local_trace", "status": "SUCCESS", "artifact": "trace.json"},
            {"name": "dataset_experiment", "status": gate["decision"], "artifact": "experiment_result.json"},
            {"name": "release_candidate", "status": gate["decision"], "artifact": "release_scorecard.json"},
        ],
        "metrics": {**metrics, "service_count": 2, "trace_span_count": len(trace["spans"])},
        "result": {
            "services": {"meeting": meeting["status"], "code_review": review["status"]},
            "trace": trace,
            "release_gate": gate,
        },
        "boundary_case": {"status": hold["decision"], "reasons": hold["reasons"]},
        "external_write": False,
        "human_release_required": True,
    }


def build_course_demo(day: int, *, workspace_root: Path) -> dict[str, Any]:
    """Build one in-memory demo with stable success and boundary evidence."""

    if day not in SUPPORTED_DAYS:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "UNSUPPORTED_COURSE_DAY",
            "supported_days": sorted(SUPPORTED_DAYS),
            "external_write": False,
        }
    root = workspace_root.resolve()
    builders = {2: _day2, 3: _day3, 4: _day4, 5: _day5}
    return builders[day](root)


def write_course_demo(
    day: int, *, workspace_root: Path, output_dir: Path
) -> dict[str, Any]:
    """Write the demo only inside the configured workspace."""

    root = workspace_root.resolve()
    safe_output = ensure_workspace_path(output_dir, root)
    result = build_course_demo(day, workspace_root=root)
    if result["status"] == "EXPECTED_FAILURE":
        return result
    safe_output.mkdir(parents=True, exist_ok=True)
    result_path = safe_output / "demo_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {**result, "output": str(result_path.relative_to(root))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, choices=sorted(SUPPORTED_DAYS), required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output_dir = args.out or root / f"output/course-demos/day{args.day}"
    result = write_course_demo(
        args.day, workspace_root=root, output_dir=output_dir
    )
    print(
        json.dumps(
            {
                "day": result.get("day"),
                "status": result["status"],
                "decision": result.get("decision"),
                "output": result.get("output"),
                "external_write": result["external_write"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
