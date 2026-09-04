from pathlib import Path
import json
from threading import Thread
from urllib.request import Request, urlopen

import pytest

from labs.day3.review_copilot.contracts import ReviewDraft, ReviewFinding, ReviewPolicy
from labs.day3.review_copilot.context_builder import build_context_pack
from labs.day3.review_copilot.diff_parser import parse_unified_diff
from labs.day3.review_copilot.evaluation import evaluate_case_set
from labs.day3.review_copilot.errors import stable_error_code
from labs.day3.review_copilot.exports import render_review_markdown
from labs.day3.review_copilot.github_plan import build_github_dry_run
from labs.day3.review_copilot.human_review import apply_human_review
from labs.day3.review_copilot.providers import (
    FixtureReviewProvider,
    LangChainReviewProvider,
    OllamaReviewProvider,
    UnavailableReviewProvider,
    run_provider,
)
from labs.day3.review_copilot.workflow import run_review_text_workflow, run_review_workflow
from labs.day3.review_copilot.web_app import create_server
from labs.day3.review_copilot.test_evidence import collect_focused_test_evidence
from labs.day3.review_copilot.cli import build_parser, main as cli_main
from labs.day3.review_copilot.workspace import read_workspace_text
from scripts.day3_pr_guard import validate_pr_payload


ROOT = Path(__file__).resolve().parents[1]
LAB = Path("labs/day3/review_copilot")


def passing_test_evidence() -> dict:
    return {
        "status": "PASSED",
        "error_code": None,
        "executed": True,
        "command": "python -m pytest -q tests/test_day3_review_copilot.py",
        "exit_code": 0,
        "stdout_tail": "all focused tests passed",
        "stderr_tail": "",
        "external_write": False,
    }


def test_day3_workflow_completes_eight_stages_without_external_write() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
    )

    assert result["status"] == "SUCCESS"
    assert result["completed_stage"] == 8
    assert list(result["stages"]) == [
        "01_review_contract",
        "02_parsed_diff",
        "03_context_pack",
        "04_candidate_review",
        "05_hybrid_review",
        "06_human_review",
        "07_evaluation",
        "08_release_evidence",
    ]
    draft = result["stages"]["05_hybrid_review"]
    assert {item["rule_id"] for item in draft["findings"]} == {
        "unsafe-dynamic-execution",
        "external-write-without-approval",
        "broad-exception-boundary",
    }
    assert all(item["line"] != 999 for item in draft["findings"])
    human = result["stages"]["06_human_review"]
    assert human["status"] == "REVIEW_REQUIRED"
    assert human["decision"] is None
    release = result["stages"]["08_release_evidence"]
    assert release["github_dry_run"]["error_code"] == "HUMAN_REVIEW_REQUIRED"
    assert release["github_dry_run"]["commands_executed"] == []
    assert release["decision"] == "HOLD"
    assert result["external_write"] is False
    metrics = result["stages"]["07_evaluation"]
    assert metrics["case_count"] == metrics["case_passed"] == 8
    assert metrics["f1"] == 1.0
    assert metrics["release_decision"] == "READY"


def test_unavailable_provider_reports_fixture_fallback_truthfully() -> None:
    fixture = FixtureReviewProvider({"case": []})
    result = run_provider(
        requested=UnavailableReviewProvider("openai", "OPENAI_NOT_CONFIGURED"),
        fallback=fixture,
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    assert result["status"] == "SUCCESS"
    assert result["provider_requested"] == "openai"
    assert result["provider_used"] == "fixture"
    assert result["fallback_reason"] == "OPENAI_NOT_CONFIGURED"


def test_langchain_adapter_accepts_structured_runnable_without_hard_dependency() -> None:
    class FakeRunnable:
        def invoke(self, prompt: dict) -> dict:
            assert prompt["contract"] == "ReviewFinding"
            return {"candidates": [{"rule_id": "fixture-candidate"}]}

    provider = LangChainReviewProvider(FakeRunnable(), name="langchain-fixture")

    assert provider.review({"contract": "ReviewFinding"}) == [
        {"rule_id": "fixture-candidate"}
    ]


def test_ollama_requires_explicit_opt_in_and_loopback_endpoint() -> None:
    provider = OllamaReviewProvider(live_opt_in=False)
    result = run_provider(
        requested=provider,
        fallback=FixtureReviewProvider({"case": []}),
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    assert result["provider_requested"] == "ollama"
    assert result["provider_used"] == "fixture"
    assert result["fallback_reason"] == "OLLAMA_LIVE_OPT_IN_REQUIRED"
    with pytest.raises(ValueError, match="OLLAMA_LOOPBACK_ENDPOINT_REQUIRED"):
        OllamaReviewProvider(endpoint="https://example.invalid/api/generate")


def test_live_provider_candidate_keeps_live_provenance() -> None:
    from labs.day3.review_copilot.review_engine import merge_grounded_candidates

    parsed = parse_unified_diff(
        "--- a/src/demo.py\n+++ b/src/demo.py\n@@ -0,0 +1 @@\n+value = build()"
    )
    draft = merge_grounded_candidates(
        parsed,
        {
            "status": "SUCCESS",
            "provider_requested": "ollama",
            "provider_used": "ollama",
            "fallback_reason": None,
            "candidates": [
                {
                    "path": "src/demo.py",
                    "line": 1,
                    "severity": "P2",
                    "title": "반환 계약 누락",
                    "impact": "호출자가 상태를 구분하지 못함",
                    "correction": "구조화된 결과를 반환",
                    "rule_id": "return-contract",
                }
            ],
        },
    )

    assert draft.findings[0].source == "live_llm"


def test_rejected_human_review_blocks_github_plan() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="reject",
        rationale="근거를 다시 확인해야 합니다.",
    )

    plan = result["stages"]["08_release_evidence"]["github_dry_run"]
    assert plan["status"] == "BLOCKED"
    assert plan["error_code"] == "HUMAN_REVIEW_REQUIRED"
    assert plan["commands_executed"] == []
    assert plan["external_write"] is False


def test_workspace_escape_is_structured_failure(tmp_path: Path) -> None:
    outside = tmp_path / "outside.diff"
    outside.write_text("secret", encoding="utf-8")

    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=outside,
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
    )

    assert result == {
        "status": "EXPECTED_FAILURE",
        "error_code": "WORKSPACE_PATH_BLOCKED",
        "completed_stage": 0,
        "external_write": False,
    }


@pytest.mark.parametrize(
    "diff_text,error",
    [
        ("", "EMPTY_DIFF"),
        ("+++ /tmp/secret.py\n@@ -0,0 +1 @@\n+token = 1", "DIFF_PATH_BLOCKED"),
    ],
)
def test_diff_parser_rejects_empty_or_absolute_target(diff_text: str, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        parse_unified_diff(diff_text)


def test_context_pack_excludes_sensitive_project_fields() -> None:
    parsed = parse_unified_diff(
        read_workspace_text(
            LAB / "fixtures/meeting_export_pr.diff",
            workspace_root=ROOT,
        )
    )
    context = build_context_pack(
        parsed,
        policy=ReviewPolicy(),
        project_context={
            "service_name": "demo",
            "purpose": "review",
            "private_customer_note": "must not appear",
        },
    )

    assert context["project_context"] == {
        "purpose": "review",
        "service_name": "demo",
    }
    assert context["context_bytes"] <= context["context_byte_limit"]


def test_context_budget_exceeded_is_explicit() -> None:
    parsed = parse_unified_diff(
        read_workspace_text(
            LAB / "fixtures/meeting_export_pr.diff",
            workspace_root=ROOT,
        )
    )

    with pytest.raises(ValueError, match="CONTEXT_BUDGET_EXCEEDED"):
        build_context_pack(parsed, policy=ReviewPolicy(), max_bytes=10)


def test_context_pack_reads_only_bounded_repository_snippets_and_policy() -> None:
    parsed = parse_unified_diff(
        "\n".join(
            [
                "--- a/labs/day3/review_copilot/review_engine.py",
                "+++ b/labs/day3/review_copilot/review_engine.py",
                "@@ -1,1 +1,2 @@",
                ' \"\"\"Rule baseline plus optional provider candidates, grounded to diff lines.\"\"\"',
                "+# synthetic context marker",
            ]
        )
    )
    context = build_context_pack(
        parsed,
        policy=ReviewPolicy(),
        workspace_root=ROOT,
    )

    assert context["repository_context"][0]["path"].endswith("review_engine.py")
    assert context["repository_context"][0]["line_end"] <= 6
    assert {item["path"] for item in context["applicable_policies"]} >= {
        "AGENTS.md",
        "labs/day3/review_copilot/AGENTS.md",
    }


def test_context_pack_records_sensitive_path_without_reading_it() -> None:
    parsed = parse_unified_diff(
        "--- a/.env\n+++ b/.env\n@@ -0,0 +1 @@\n+SAFE_FLAG=true"
    )
    context = build_context_pack(
        parsed,
        policy=ReviewPolicy(),
        workspace_root=ROOT,
    )

    assert context["repository_context"] == []
    assert context["excluded_paths"] == [
        {"path": ".env", "reason": "SENSITIVE_PATH_NOT_READ"}
    ]


@pytest.mark.parametrize(
    "overrides,error_code",
    [
        ({"severity": "P9"}, "FINDING_SEVERITY_INVALID"),
        ({"line": 0}, "FINDING_LINE_INVALID"),
        ({"confidence": 2}, "FINDING_CONFIDENCE_INVALID"),
        ({"automatic_publish": True}, "AUTOMATIC_PUBLISH_FORBIDDEN"),
    ],
)
def test_pydantic_contract_uses_stable_error_codes(overrides: dict, error_code: str) -> None:
    payload = {
        "path": "src/demo.py",
        "line": 1,
        "severity": "P1",
        "title": "외부 서비스 호출",
        "impact": "중복 게시 가능",
        "evidence": "requests.post(...) ",
        "correction": "승인 경계를 추가",
        "rule_id": "external-write",
    }
    payload.update(overrides)

    with pytest.raises(ValueError) as caught:
        ReviewFinding(**payload)

    assert stable_error_code(caught.value) == error_code


def test_workflow_returns_stable_contract_error_to_web_boundary() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="edit",
        edited_findings=[
            {
                "path": "labs/day3/review_copilot/fixtures/repository/meeting_export.py",
                "line": 7,
                "severity": "INVALID",
                "title": "잘못된 severity",
                "impact": "계약 위반",
                "evidence": "eval(action)",
                "correction": "severity 수정",
                "rule_id": "invalid-test",
            }
        ],
    )

    assert result["status"] == "SUCCESS"
    review = result["stages"]["06_human_review"]
    assert review["status"] == "BLOCKED"
    assert review["error_code"] == "FINDING_SEVERITY_INVALID"
    assert "validation error" not in review["error_code"].lower()
    assert result["stages"]["08_release_evidence"]["decision"] == "HOLD"


def test_focused_test_evidence_preserves_real_exit_code_contract() -> None:
    class Result:
        returncode = 0
        stdout = "17 passed"
        stderr = ""

    calls: list[list[str]] = []

    def fake_runner(command: list[str], **kwargs):
        calls.append(command)
        assert kwargs["cwd"] == ROOT.resolve()
        assert kwargs["timeout"] == 120
        return Result()

    evidence = collect_focused_test_evidence(
        workspace_root=ROOT,
        runner=fake_runner,
    )

    assert calls[0][-2:] == ["-q", "tests/test_day3_review_copilot.py"]
    assert evidence["status"] == "PASSED"
    assert evidence["exit_code"] == 0
    assert evidence["external_write"] is False


@pytest.mark.parametrize("argv", [["cases"], ["evaluate"], ["context", "--case", "external_write"]])
def test_cli_read_only_subcommands_return_json(argv: list[str], capsys) -> None:
    assert cli_main(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "SUCCESS"
    assert payload["external_write"] is False


def test_eight_case_golden_set_includes_clean_negative_and_expected_failure() -> None:
    result = evaluate_case_set(
        workspace_root=ROOT,
        manifest_path=LAB / "fixtures/cases.json",
        golden_path=LAB / "fixtures/golden_findings.json",
    )

    assert result["case_count"] == 8
    assert result["case_passed"] == 8
    assert result["false_positive"] == result["false_negative"] == 0
    assert result["expected_failure_cases_passed"] == 1
    assert result["release_decision"] == "READY"


def test_localhost_app_health_and_review_smoke() -> None:
    server = create_server(root=ROOT, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with urlopen(f"http://{host}:{port}/api/health", timeout=2) as response:
            health = json.loads(response.read())
        sample = (ROOT / LAB / "fixtures/meeting_export_pr.diff").read_text(encoding="utf-8")
        request = Request(
            f"http://{host}:{port}/api/review",
            data=json.dumps({"diff_text": sample, "decision": "approve"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            result = json.loads(response.read())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert health == {
        "status": "ok",
        "service": "day3-review-copilot",
        "provider": "fixture",
        "external_write": False,
    }
    assert result["status"] == "SUCCESS"
    assert result["stages"]["07_evaluation"]["case_passed"] == 8
    assert result["external_write"] is False


def test_langgraph_interrupt_requires_human_resume_when_installed() -> None:
    pytest.importorskip("langgraph")
    from labs.day3.review_copilot.langgraph_review import run_langgraph_human_review

    workflow = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
    )
    result = run_langgraph_human_review(
        workflow["stages"]["05_hybrid_review"],
        decision="approve",
        thread_id="test-day3-human-review",
    )

    assert result["interrupted"] is True
    assert result["status"] == "DRY_RUN_READY"
    assert result["interrupt_payload"]["options"] == ["approve", "edit", "reject"]
    assert result["external_write"] is False


def test_cli_has_no_implicit_human_decision() -> None:
    parser = build_parser()

    assert parser.parse_args(["run"]).decision is None
    assert parser.parse_args(["review"]).decision is None


def test_cli_pending_review_is_json_serializable(capsys) -> None:
    assert cli_main(["review", "--case", "external_write"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["stages"]["06_human_review"]["status"] == "REVIEW_REQUIRED"
    assert payload["stages"]["08_release_evidence"]["decision"] == "HOLD"


def test_explicit_approval_and_passed_test_evidence_prepare_only_a_dry_run() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="approve",
        reviewer="강사",
        rationale="추가 라인, 영향, 최소 교정을 확인했습니다.",
        test_evidence=passing_test_evidence(),
    )

    review = result["stages"]["06_human_review"]
    release = result["stages"]["08_release_evidence"]
    assert review["status"] == "APPROVED"
    assert review["human_reviewed"] is True
    assert release["github_dry_run"]["status"] == "DRY_RUN_READY"
    assert release["github_dry_run"]["commands_executed"] == []
    assert release["decision"] == "READY_FOR_MANUAL_GITHUB_STEP"
    assert result["external_write"] is False


def test_approval_without_executed_tests_stays_blocked() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="approve",
    )

    plan = result["stages"]["08_release_evidence"]["github_dry_run"]
    assert plan["status"] == "BLOCKED"
    assert plan["error_code"] == "FOCUSED_TEST_REQUIRED"
    assert result["stages"]["08_release_evidence"]["decision"] == "HOLD"


def _draft_for_human_review() -> ReviewDraft:
    return ReviewDraft(
        status="DRAFT",
        findings=(
            ReviewFinding(
                path="src/demo.py",
                line=3,
                severity="P1",
                title="사람 승인 없는 외부 서비스 호출",
                impact="검토되지 않은 결과가 게시될 수 있습니다.",
                evidence="client.post(payload)",
                correction="사람 승인 뒤에만 외부 서비스 호출을 허용합니다.",
                rule_id="external-write-without-approval",
            ),
        ),
    )


@pytest.mark.parametrize(
    "decision,reviewer,rationale,error_code",
    [
        ("publish", "검토자", "근거 확인", "HUMAN_REVIEW_DECISION_INVALID"),
        ("approve", "", "근거 확인", "HUMAN_REVIEWER_REQUIRED"),
        ("approve", "검토자", "", "HUMAN_REVIEW_RATIONALE_REQUIRED"),
    ],
)
def test_human_review_invalid_input_is_stably_blocked(
    decision: str,
    reviewer: str,
    rationale: str,
    error_code: str,
) -> None:
    review = apply_human_review(
        _draft_for_human_review(),
        decision=decision,
        reviewer=reviewer,
        rationale=rationale,
    )

    assert review.status == "BLOCKED"
    assert review.error_code == error_code
    assert review.human_reviewed is False
    assert review.external_write is False


@pytest.mark.parametrize(
    "edited_findings,error_code",
    [
        (None, "EDITED_FINDINGS_REQUIRED"),
        ([], "EDITED_FINDINGS_REQUIRED"),
        (
            [
                {
                    "path": "src/demo.py",
                    "line": 999,
                    "severity": "P1",
                    "title": "근거 없는 수정",
                    "impact": "원본 diff에 없는 위치입니다.",
                    "evidence": "invented",
                    "correction": "원본 finding 위치를 유지합니다.",
                    "rule_id": "external-write-without-approval",
                }
            ],
            "EDIT_FINDING_NOT_GROUNDED",
        ),
        (
            [
                {
                    "path": "src/demo.py",
                    "line": 3,
                    "severity": "P9",
                    "title": "계약 밖 심각도",
                    "impact": "정렬과 gate가 불안정해집니다.",
                    "evidence": "client.post(payload)",
                    "correction": "P0~P3 중 하나를 사용합니다.",
                    "rule_id": "external-write-without-approval",
                }
            ],
            "FINDING_SEVERITY_INVALID",
        ),
    ],
)
def test_human_edit_requires_valid_grounded_findings(
    edited_findings: list[dict] | None,
    error_code: str,
) -> None:
    review = apply_human_review(
        _draft_for_human_review(),
        decision="edit",
        reviewer="검토자",
        rationale="수정 근거를 확인했습니다.",
        edited_findings=edited_findings,
    )

    assert review.status == "BLOCKED"
    assert review.error_code == error_code
    assert review.findings == ()


def test_langgraph_edit_uses_the_same_grounding_contract_when_installed() -> None:
    pytest.importorskip("langgraph")
    from labs.day3.review_copilot.langgraph_review import run_langgraph_human_review

    result = run_langgraph_human_review(
        _draft_for_human_review().to_dict(),
        decision="edit",
        reviewer="검토자",
        rationale="수정 근거를 확인했습니다.",
        edited_findings=[
            {
                **_draft_for_human_review().findings[0].to_dict(),
                "line": 999,
            }
        ],
        thread_id="test-day3-invalid-edit",
    )

    assert result["status"] == "BLOCKED"
    assert result["final_state"]["review"]["status"] == "BLOCKED"
    assert result["final_state"]["review"]["error_code"] == "EDIT_FINDING_NOT_GROUNDED"
    assert result["external_write"] is False


def test_markdown_export_follows_the_human_reviewed_findings() -> None:
    initial = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
    )
    selected = dict(initial["stages"]["05_hybrid_review"]["findings"][0])
    selected["title"] = "사람이 다듬은 최종 제목"
    edited = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="edit",
        reviewer="검토자",
        rationale="첫 finding만 유지하고 표현을 다듬었습니다.",
        edited_findings=[selected],
    )
    rejected = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="reject",
        reviewer="검토자",
        rationale="이번 변경에서는 finding을 제외합니다.",
    )

    edited_markdown = render_review_markdown(edited)
    rejected_markdown = render_review_markdown(rejected)
    assert "사람이 다듬은 최종 제목" in edited_markdown
    assert edited_markdown.count("### ") == 1
    assert "검토할 finding이 없습니다." in rejected_markdown
    assert "입력 문자열의 코드 실행" not in rejected_markdown


def test_github_plan_body_passes_the_repository_pr_guard() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
        decision="approve",
        reviewer="검토자",
        rationale="실제 test evidence와 diff 근거를 확인했습니다.",
        test_evidence=passing_test_evidence(),
    )
    plan = result["stages"]["08_release_evidence"]["github_dry_run"]
    changed_paths = result["stages"]["02_parsed_diff"]["changed_paths"]

    guard = validate_pr_payload(
        {"pull_request": plan["pull_request"]},
        changed_paths=changed_paths,
    )
    assert plan["status"] == "DRY_RUN_READY"
    assert guard["status"] == "PASS"
    assert "실제 test evidence와 diff 근거를 확인했습니다." in plan["pull_request"]["body"]
    assert plan["external_write"] is False


def test_github_plan_blocks_sensitive_changed_path() -> None:
    review = apply_human_review(
        _draft_for_human_review(),
        decision="approve",
        reviewer="검토자",
        rationale="근거를 확인했습니다.",
    )
    plan = build_github_dry_run(
        repository="owner/repository",
        base="main",
        branch="codex/day3-safe-review",
        title="Day 3",
        review=review,
        changed_paths=["config/credentials.json"],
        test_evidence=passing_test_evidence(),
    )

    assert plan["status"] == "BLOCKED"
    assert plan["error_code"] == "SENSITIVE_PATH_CHANGED"
    assert plan["commands_executed"] == []


@pytest.mark.parametrize(
    "path",
    [
        "credentials.json",
        "config/secrets.json",
        ".env.production",
        "certificates/service.key",
        "certificates/service.pem",
        "certificates/service.p12",
        "certificates/service.pfx",
    ],
)
def test_context_pack_never_reads_sensitive_path_variants(path: str) -> None:
    parsed = parse_unified_diff(
        f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n+SAFE_LABEL=classroom"
    )
    context = build_context_pack(
        parsed,
        policy=ReviewPolicy(),
        workspace_root=ROOT,
    )

    assert context["repository_context"] == []
    assert {item["path"] for item in context["excluded_paths"]} == {path}
    assert context["excluded_paths"][0]["reason"] == "SENSITIVE_PATH_NOT_READ"


def test_secret_like_values_are_redacted_before_provider_prompt() -> None:
    class CapturingProvider:
        name = "capturing-live"
        model = "synthetic-model"

        def __init__(self) -> None:
            self.prompt: dict | None = None

        def review(self, prompt: dict) -> list[dict]:
            self.prompt = prompt
            return []

    provider = CapturingProvider()
    secret = "sk-" + "proj-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ12345"
    result = run_review_text_workflow(
        workspace_root=ROOT,
        diff_text=(
            "--- a/src/normal.py\n"
            "+++ b/src/normal.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+message = 'normal-marker'\n"
            f"+api_key = '{secret}'"
        ),
        project_context={
            "service_name": "demo",
            "purpose": f"token={secret}",
        },
        fixture_payload={"case_id": "case", "responses": {"case": []}},
        provider=provider,
    )

    serialized_prompt = json.dumps(provider.prompt, ensure_ascii=False)
    assert result["status"] == "SUCCESS"
    assert secret not in serialized_prompt
    assert "[REDACTED" in serialized_prompt
    assert "normal-marker" in serialized_prompt
    assert provider.prompt is not None and provider.prompt["redaction_count"] >= 2


def test_context_bytes_matches_the_final_serialized_payload() -> None:
    parsed = parse_unified_diff(
        read_workspace_text(
            LAB / "fixtures/meeting_export_pr.diff",
            workspace_root=ROOT,
        )
    )
    context = build_context_pack(
        parsed,
        policy=ReviewPolicy(),
        project_context={"service_name": "한국어 Review Copilot"},
        workspace_root=ROOT,
    )

    serialized_bytes = len(
        json.dumps(context, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    assert context["context_bytes"] == serialized_bytes
    assert serialized_bytes <= context["context_byte_limit"]


def test_representative_diff_uses_real_synthetic_code_test_and_policy_context() -> None:
    result = run_review_workflow(
        workspace_root=ROOT,
        diff_path=LAB / "fixtures/meeting_export_pr.diff",
        project_context_path=LAB / "fixtures/project_context.json",
        fixture_path=LAB / "fixtures/provider_fixture.json",
    )
    context = result["stages"]["03_context_pack"]

    assert [item["path"] for item in context["repository_context"]] == [
        "labs/day3/review_copilot/fixtures/repository/meeting_export.py"
    ]
    assert [item["path"] for item in context["existing_tests"]] == [
        "labs/day3/review_copilot/fixtures/repository/test_meeting_export.py"
    ]
    assert {item["path"] for item in context["applicable_policies"]} >= {
        "AGENTS.md",
        "labs/day3/review_copilot/AGENTS.md",
        "labs/day3/review_copilot/fixtures/repository/AGENTS.md",
    }


def _provider_candidate() -> dict:
    return {
        "path": "src/demo.py",
        "line": 1,
        "severity": "P2",
        "title": "반환 계약 누락",
        "impact": "호출자가 결과 상태를 구분하지 못합니다.",
        "correction": "명시적인 status와 error_code를 반환합니다.",
        "rule_id": "return-contract",
        "confidence": 0.8,
    }


def test_provider_fixture_and_live_contracts_include_model_and_schema_status() -> None:
    fixture = FixtureReviewProvider({"case": [_provider_candidate()]})
    fixture_result = run_provider(
        requested=fixture,
        fallback=fixture,
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    class LiveProvider:
        name = "live-test"
        model = "live-model-v1"

        def review(self, prompt: dict) -> list[dict]:
            assert prompt["case_id"] == "case"
            return [_provider_candidate()]

    live_result = run_provider(
        requested=LiveProvider(),
        fallback=fixture,
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    assert fixture_result["model"] == "deterministic-review-fixture-v1"
    assert fixture_result["schema_valid"] is True
    assert live_result["provider_used"] == "live-test"
    assert live_result["requested_model"] == live_result["model"] == "live-model-v1"
    assert live_result["schema_valid"] is True


def test_provider_schema_failure_falls_back_with_truthful_provenance() -> None:
    class InvalidLiveProvider:
        name = "live-test"
        model = "live-model-v1"

        def review(self, prompt: dict) -> list[dict]:
            del prompt
            return [{"rule_id": "missing-required-fields"}]

    result = run_provider(
        requested=InvalidLiveProvider(),
        fallback=FixtureReviewProvider({"case": []}),
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    assert result["provider_requested"] == "live-test"
    assert result["provider_used"] == "fixture"
    assert result["requested_model"] == "live-model-v1"
    assert result["model"] == "deterministic-review-fixture-v1"
    assert result["schema_valid"] is True
    assert result["fallback_reason"] == "PROVIDER_SCHEMA_INVALID"


def test_langchain_sdk_exception_becomes_stable_provider_failure_and_fallback() -> None:
    class VendorSpecificSDKError(Exception):
        pass

    class BrokenRunnable:
        model_name = "sdk-model"

        def invoke(self, prompt: dict) -> dict:
            del prompt
            raise VendorSpecificSDKError("vendor-specific private message")

    result = run_provider(
        requested=LangChainReviewProvider(BrokenRunnable()),
        fallback=FixtureReviewProvider({"case": []}),
        prompt={"case_id": "case"},
        allow_fallback=True,
    )

    assert result["status"] == "SUCCESS"
    assert result["provider_used"] == "fixture"
    assert result["fallback_reason"] == "PROVIDER_CALL_FAILED"
    assert "vendor-specific" not in json.dumps(result)


@pytest.mark.parametrize("interrupt_type", [KeyboardInterrupt, SystemExit])
def test_langchain_does_not_swallow_process_interrupts(interrupt_type: type[BaseException]) -> None:
    class InterruptedRunnable:
        def invoke(self, prompt: dict) -> dict:
            del prompt
            raise interrupt_type()

    provider = LangChainReviewProvider(InterruptedRunnable())
    with pytest.raises(interrupt_type):
        provider.review({"case_id": "case"})


def test_live_provider_requires_separate_candidate_evaluation_for_release() -> None:
    class LiveProvider:
        name = "live-test"
        model = "live-model-v1"

        def review(self, prompt: dict) -> list[dict]:
            del prompt
            return []

    common = {
        "workspace_root": ROOT,
        "diff_path": LAB / "fixtures/meeting_export_pr.diff",
        "project_context_path": LAB / "fixtures/project_context.json",
        "fixture_path": LAB / "fixtures/provider_fixture.json",
        "provider": LiveProvider(),
        "decision": "approve",
        "reviewer": "검토자",
        "rationale": "모델 후보와 rule baseline을 분리해 확인했습니다.",
        "test_evidence": passing_test_evidence(),
    }
    without_candidate_eval = run_review_workflow(**common)
    with_candidate_eval = run_review_workflow(
        **common,
        candidate_evaluation={
            "release_decision": "READY",
            "dataset": "synthetic-held-out-v1",
            "case_count": 8,
        },
    )

    blocked_release = without_candidate_eval["stages"]["08_release_evidence"]
    ready_release = with_candidate_eval["stages"]["08_release_evidence"]
    assert blocked_release["rule_baseline_gate"]["evaluation_scope"] == (
        "deterministic_rule_baseline_only"
    )
    assert blocked_release["provider_candidate_gate"] == {
        "status": "HOLD",
        "error_code": "LIVE_PROVIDER_CANDIDATE_EVALUATION_REQUIRED",
    }
    assert blocked_release["decision"] == "HOLD"
    assert ready_release["provider_candidate_gate"]["status"] == "PASSED"
    assert ready_release["decision"] == "READY_FOR_MANUAL_GITHUB_STEP"
