import json
from pathlib import Path

import pytest

from src.course_services.codex_harness import CodexTaskSpec, assess_codex_run, render_codex_task
from src.course_services.course_demo import build_course_demo
from src.course_services.eval_service import evaluate_review_findings, release_gate
from src.course_services.github_service import (
    InMemoryIdempotencyStore,
    classify_github_response,
    load_pr_fixture,
    prepare_review_comment,
    publish_review_comment,
)
from src.course_services.meeting_service import (
    chunk_transcript_segments,
    validate_action_evidence,
)
from src.course_services.review_service import parse_unified_diff, run_review_service
from src.course_services.service_router import route_service_request
from src.observability_lab import redact_observability_text


ROOT = Path(__file__).resolve().parents[1]
DIFF_PATH = ROOT / "data/day3_review_cases/unsafe_pr.diff"


def test_unified_diff_maps_findings_to_added_lines() -> None:
    diff_text = DIFF_PATH.read_text(encoding="utf-8")
    parsed = parse_unified_diff(diff_text)
    result = run_review_service(diff_text)

    assert parsed.changed_paths == ("src/payment_job.py",)
    assert [item["line"] for item in result["findings"]] == [9, 11, 12]
    assert {item["rule_id"] for item in result["findings"]} == {
        "unsafe-dynamic-execution",
        "external-write-without-approval",
        "broad-exception-boundary",
    }
    assert result["automatic_publish"] is False


def test_meeting_chunks_keep_segment_evidence_and_validate_unknown_ids() -> None:
    segments = [
        {"id": "s01", "text": "배송 지연 원인을 주문과 물류 단계별로 확인합니다."},
        {"id": "s02", "text": "고객 안내 문구를 채널과 상황별로 수정합니다."},
        {"id": "s03", "text": "담당자는 민지입니다."},
    ]
    chunks = chunk_transcript_segments(segments, max_chars=40, overlap_segments=1)
    errors = validate_action_evidence(
        [{"task": "문구 수정", "evidence_ids": ["s02", "s99"]}],
        known_segment_ids={"s01", "s02", "s03"},
    )
    assert chunks[0]["segment_ids"] == ["s01"]
    assert chunks[1]["segment_ids"][0] == "s01"
    assert errors == ["ACTION_1_UNKNOWN_EVIDENCE:s99"]


@pytest.mark.parametrize("diff_text", ["", "+++ /tmp/secret.py\n@@ -0,0 +1 @@\n+token = 1"])
def test_invalid_or_absolute_diff_is_structured_failure(diff_text: str) -> None:
    result = run_review_service(diff_text)
    assert result["status"] == "EXPECTED_FAILURE"
    assert result["error_code"]
    assert result["automatic_publish"] is False


def test_github_comment_requires_approval_and_is_idempotent() -> None:
    fixture = load_pr_fixture(ROOT / "data/day4_github/pr_fixture.json", workspace_root=ROOT)
    report = run_review_service(DIFF_PATH.read_text(encoding="utf-8"))
    target = {key: fixture[key] for key in ("repository", "number", "head_sha")}
    approval_plan = prepare_review_comment(report=report, target=target, dry_run=False)
    store = InMemoryIdempotencyStore()
    calls: list[str] = []

    blocked = publish_review_comment(
        plan=approval_plan,
        human_approved=False,
        publisher=lambda _target, body: {"id": 1, "body": body},
        store=store,
    )
    assert blocked["status"] == "BLOCKED"
    assert blocked["error_code"] == "HUMAN_APPROVAL_REQUIRED"

    def fake_publisher(_target, body: str) -> dict:
        calls.append(body)
        return {"id": 101, "url": "https://example.invalid/review/101"}

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
    assert first["status"] == second["status"] == "PUBLISHED"
    assert first["remote_result"]["reused"] is False
    assert second["remote_result"]["reused"] is True
    assert len(calls) == 1


def test_dry_run_can_never_publish() -> None:
    fixture = json.loads((ROOT / "data/day4_github/pr_fixture.json").read_text(encoding="utf-8"))
    report = run_review_service(DIFF_PATH.read_text(encoding="utf-8"))
    plan = prepare_review_comment(
        report=report,
        target={key: fixture[key] for key in ("repository", "number", "head_sha")},
        dry_run=True,
    )
    result = publish_review_comment(
        plan=plan,
        human_approved=True,
        publisher=lambda _target, _body: {"id": 1},
        store=InMemoryIdempotencyStore(),
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "DRY_RUN_CANNOT_PUBLISH"


def test_codex_harness_holds_unreviewed_or_out_of_scope_changes() -> None:
    spec = CodexTaskSpec(
        objective="diff reviewer에 정상·실패 test를 추가한다.",
        allowed_paths=("src/course_services", "tests"),
        acceptance_tests=("python -m pytest -q tests/test_course_services.py",),
    )
    prompt = render_codex_task(spec)
    assert "변경 허용 범위" in prompt
    result = assess_codex_run(
        spec,
        changed_paths=["src/course_services/review_service.py", ".env"],
        executed_tests={"python -m pytest -q tests/test_course_services.py": True},
        diff_reviewed=False,
        secrets_detected=True,
    )
    assert result["decision"] == "HOLD"
    assert set(result["reasons"]) == {
        "UNEXPECTED_CHANGED_PATH",
        "DIFF_REVIEW_REQUIRED",
        "SECRET_DETECTED",
    }


def test_router_runs_both_services_and_blocks_workspace_escape(tmp_path: Path) -> None:
    meeting = route_service_request(
        input_kind="meeting_transcript",
        source_path=ROOT / "data/meeting_sample_ko.txt",
        workspace_root=ROOT,
    )
    review = route_service_request(
        input_kind="code_diff",
        source_path=DIFF_PATH,
        workspace_root=ROOT,
    )
    escaped = route_service_request(
        input_kind="code_diff",
        source_path=tmp_path / "outside.diff",
        workspace_root=ROOT,
    )
    assert meeting["service"] == "meeting"
    assert review["service"] == "code_review"
    assert escaped["status"] == "EXPECTED_FAILURE"
    assert "WORKSPACE_PATH_BLOCKED" in escaped["error_code"]


def test_offline_eval_drives_release_gate() -> None:
    expected = json.loads(
        (ROOT / "data/day5_eval/golden_review_findings.json").read_text(encoding="utf-8")
    )
    report = run_review_service(DIFF_PATH.read_text(encoding="utf-8"))
    metrics = evaluate_review_findings(report["findings"], expected)
    decision = release_gate(
        review_metrics=metrics,
        safety_passed=True,
        latency_seconds=0.2,
    )
    assert metrics == {
        "true_positive": 3,
        "false_positive": 0,
        "false_negative": 0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }
    assert decision["decision"] == "READY"


@pytest.mark.parametrize("day", [2, 3, 4, 5])
def test_course_demo_has_success_boundary_and_no_real_external_write(day: int) -> None:
    result = build_course_demo(day, workspace_root=ROOT)

    assert result["status"] == "SUCCESS"
    assert result["stages"]
    assert result["boundary_case"]
    assert result["external_write"] is False


def test_course_demo_rejects_unknown_day() -> None:
    result = build_course_demo(1, workspace_root=ROOT)

    assert result == {
        "status": "EXPECTED_FAILURE",
        "error_code": "UNSUPPORTED_COURSE_DAY",
        "supported_days": [2, 3, 4, 5],
        "external_write": False,
    }


def test_github_status_contract_retries_only_rate_limit() -> None:
    rate_limited = classify_github_response(429, retry_after_seconds=3)
    unauthorized = classify_github_response(401, retry_after_seconds=3)

    assert rate_limited["retryable"] is True
    assert rate_limited["retry_after_seconds"] == 3
    assert unauthorized["retryable"] is False
    assert unauthorized["retry_after_seconds"] is None
    assert unauthorized["error_code"] == "GITHUB_AUTH_REQUIRED"


def test_observability_redaction_removes_pii_and_token_shapes() -> None:
    result = redact_observability_text(
        "담당자 test@example.com 010-1234-5678 sk-exampletoken123456789"
    )

    assert result["redacted"] is True
    assert "test@example.com" not in result["text"]
    assert "010-1234-5678" not in result["text"]
    assert "sk-exampletoken123456789" not in result["text"]
