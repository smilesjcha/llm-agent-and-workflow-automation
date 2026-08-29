"""Focused normal and boundary tests for the Day 2 multi-source workflow."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.course_services.day2_meeting_workflow import (
    DEFAULT_OPENAI_MODEL,
    DomainContext,
    MCPRetrievalPolicy,
    MeetingRecord,
    SourceInput,
    TranscriptEnvelope,
    adapt_audio_stt,
    adapt_clovanote,
    adapt_google_meet,
    compare_execution_strategies,
    render_email_draft,
    route_execution_strategy,
    run_meeting_workflow,
    run_optional_cli_prompt,
    run_optional_openai_record,
    run_optional_openai_prompt,
    source_mixing_error_example,
)


DOMAIN = DomainContext(
    industry="이커머스 고객경험",
    organization_context="배송 지연 문의가 증가해 상담 부담과 고객 불편이 함께 커진 상태",
    meeting_objective="배송 지연 회의 기록 자동화 범위 확정",
    glossary={"WISMO": "배송 위치 문의", "SLA": "약속한 응답 시간"},
    prior_decisions=["외부 발송은 사람 승인 뒤에만 진행"],
    desired_outcomes=["근거가 있는 담당자별 To Do 초안"],
)

MEET_TEXT = """\
[00:00] 민지: 오늘은 배송 지연 회의 기록 자동화 범위를 확정하겠습니다.
[00:15] 준호: WISMO 문의를 우선 처리하고 환불 자동화는 보류하는 것이 좋겠습니다.
[00:30] 서연: 제가 9월 2일까지 고객 안내 문구를 정리해 공유하겠습니다.
[00:45] 민지: 최근 야근 부담이 있으니 범위를 더 늘리지 않겠습니다.
"""

CLOVA_TEXT = """\
화자 1 00:00
배송 지연 원인 분류를 1차 범위로 확정합니다.
화자 2 00:20
제가 9월 3일까지 분류 기준을 작성하겠습니다.
"""


def test_three_source_adapters_produce_one_common_envelope(tmp_path: Path) -> None:
    meet = adapt_google_meet(
        SourceInput(
            source_mode="google_meet_text",
            source_ref="meet://fixture/001",
            meet_transcript=MEET_TEXT,
            speaker_metadata={"민지": {"display_name": "민지", "role": "PM"}},
            history_metadata={"prior_decisions": ["자동 발송 금지"]},
        )
    )
    clova = adapt_clovanote(
        SourceInput(
            source_mode="clovanote_txt",
            source_ref="clovanote-export.txt",
            clovanote_text=CLOVA_TEXT,
        )
    )
    audio_path = tmp_path / "meeting.wav"
    audio_path.write_bytes(b"not-decoded-by-injected-fixture")

    def fake_stt(_path: Path):
        return (
            "",
            [{"text": "제가 9월 4일까지 STT 결과를 검토하겠습니다.", "speaker": "민지"}],
            {"provider": "fixture_local_stt", "language": "ko"},
        )

    audio = adapt_audio_stt(
        SourceInput(
            source_mode="audio_stt",
            source_ref="local-audio-fixture",
            audio_path=str(audio_path),
        ),
        transcriber=fake_stt,
    )

    assert all(isinstance(item, TranscriptEnvelope) for item in (meet, clova, audio))
    assert [item.source_mode for item in (meet, clova, audio)] == [
        "google_meet_text",
        "clovanote_txt",
        "audio_stt",
    ]
    assert all(item.source_count == 1 for item in (meet, clova, audio))
    assert audio.stt_metadata["fallback_transcript_substituted"] is False


def test_source_mode_mixing_and_silent_stt_fallback_are_blocked(tmp_path: Path) -> None:
    assert source_mixing_error_example()["error_code"] == "SOURCE_MODE_MIXING_FORBIDDEN"
    with pytest.raises(ValidationError, match="SOURCE_MODE_MIXING_FORBIDDEN"):
        SourceInput(
            source_mode="google_meet_text",
            source_ref="mixed",
            meet_transcript=MEET_TEXT,
            clovanote_text=CLOVA_TEXT,
        )

    audio_path = tmp_path / "meeting.wav"
    audio_path.write_bytes(b"fixture")
    with pytest.raises(RuntimeError, match="^STT_ADAPTER_REQUIRED$"):
        adapt_audio_stt(
            SourceInput(
                source_mode="audio_stt",
                source_ref="audio-only",
                audio_path=str(audio_path),
            ),
            transcriber=None,
        )


@pytest.mark.parametrize(
    ("decision", "expected_status", "draft_ready"),
    [
        ("approve", "DRAFT_READY", True),
        ("edit", "DRAFT_READY", True),
        ("reject", "REJECTED", False),
    ],
)
def test_langgraph_workflow_preserves_evidence_and_human_review(
    decision: str, expected_status: str, draft_ready: bool
) -> None:
    source = SourceInput(
        source_mode="google_meet_text",
        source_ref="meet://fixture/001",
        meet_transcript=MEET_TEXT,
    )
    edits = (
        {
            "meeting_summary": "사람이 근거를 확인한 뒤 배송 지연 기록 범위를 확정했습니다.",
            "todo_updates": {"0": {"owner": "민지", "due_date": "2026-09-05"}},
        }
        if decision == "edit"
        else None
    )
    result = run_meeting_workflow(
        source,
        DOMAIN,
        review_decision=decision,
        review_edits=edits,
        retrieval_policy=MCPRetrievalPolicy(
            allowed_connectors=["notion", "slack"],
            explicit_user_authorization=True,
            allowed_scopes={"notion": ["CX 프로젝트"], "slack": ["#delivery-poc"]},
        ),
    )

    assert result["framework"] == "LangGraph"
    assert [event["node"] for event in result["trace"]] == result["graph_nodes"]
    assert result["status"] == expected_status
    assert result["exports"]["status"] == (
        "DRAFT_READY" if draft_ready else "SKIPPED_NOT_APPROVED"
    )
    assert result["external_write"] is False
    assert result["retrieval_plan"]["executed"] is False
    assert result["retrieval_plan"]["external_write"] is False
    assert result["retrieval_plan"]["status"] == "SIMULATED_POLICY_PLAN"
    known_ids = {item["id"] for item in result["envelope"]["segments"]}
    assert set(result["record"]["summary_evidence_ids"]) <= known_ids
    todo_evidence = {
        evidence
        for item in result["record"]["todos"]
        for evidence in item["evidence_ids"]
    }
    assert todo_evidence <= known_ids
    assert any(item["owner"] is not None for item in result["record"]["todos"])
    assert any(item["due_date"] is not None for item in result["record"]["todos"])
    assert result["record"]["wellbeing_risks"]


def test_rule_router_distinguishes_fixed_workflow_agent_and_one_off_llm() -> None:
    fixed = route_execution_strategy(
        requested_actions=["normalize", "summarize", "todos", "draft"]
    )
    agent = route_execution_strategy(
        requested_actions=["summarize"], external_context_sources=["notion", "slack"]
    )
    one_off = route_execution_strategy(requested_actions=["write_poem"])

    assert fixed["strategy"] == "deterministic_workflow"
    assert agent["strategy"] == "agent_router"
    assert one_off["strategy"] == "single_llm"
    assert all(result["llm_router_call"] is False for result in (fixed, agent, one_off))
    assert {item["strategy"] for item in compare_execution_strategies()} == {
        "single_llm",
        "deterministic_workflow",
        "agent_router",
    }


def test_openai_adapter_defaults_off_and_model_unavailable_is_stable() -> None:
    default = run_optional_openai_prompt("회의를 구조화해 주세요.", env={})
    assert default == {
        "status": "FALLBACK",
        "provider_requested": "openai",
        "provider_used": "fixture",
        "model": DEFAULT_OPENAI_MODEL,
        "model_available": None,
        "live_attempted": False,
        "output_text": "로컬 fixture: API를 호출하지 않은 구조 검증 결과",
        "fallback_reason": "OPENAI_LIVE_OPT_IN_REQUIRED",
        "api_key_value_exposed": False,
        "external_write": False,
    }

    class ModelNotFound(Exception):
        status_code = 404

    class FakeResponses:
        @staticmethod
        def create(**_kwargs):
            raise ModelNotFound("requested model does not exist")

    fake_client = SimpleNamespace(responses=FakeResponses())
    unavailable = run_optional_openai_prompt(
        "회의를 구조화해 주세요.",
        env={"OPENAI_LIVE_OPT_IN": "1"},
        client=fake_client,
    )
    assert unavailable["status"] == "FALLBACK"
    assert unavailable["fallback_reason"] == "MODEL_NOT_AVAILABLE"
    assert unavailable["model_available"] is False
    assert unavailable["provider_used"] == "fixture"
    assert unavailable["api_key_value_exposed"] is False

    envelope = adapt_google_meet(
        SourceInput(
            source_mode="google_meet_text",
            source_ref="meet://fixture/record",
            meet_transcript=MEET_TEXT,
        )
    )
    structured = run_optional_openai_record(envelope, DOMAIN, env={})
    assert structured["status"] == "FALLBACK"
    assert structured["provider_used"] == "fixture"
    assert structured["schema_valid"] is True
    assert structured["record"]["external_write"] is False


def test_email_output_is_draft_without_recipient_or_send() -> None:
    result = run_meeting_workflow(
        SourceInput(
            source_mode="clovanote_txt",
            source_ref="clova.txt",
            clovanote_text=CLOVA_TEXT,
        ),
        DOMAIN,
        review_decision="approve",
    )
    record = result["record"]
    draft = render_email_draft(MeetingRecord.model_validate(record))
    assert draft["to"] == []
    assert draft["send"] is False
    assert draft["external_write"] is False


def test_missing_owner_and_due_remain_null_instead_of_being_invented() -> None:
    result = run_meeting_workflow(
        SourceInput(
            source_mode="google_meet_text",
            source_ref="meet://ambiguous/001",
            meet_transcript="민지: 다음 회의에서 후속 조치를 논의해 봅시다.",
        ),
        DOMAIN,
        review_decision="approve",
    )
    todo = result["record"]["todos"][0]
    assert todo["task"] == "후속 조치의 담당자와 기한 확정"
    assert todo["owner"] is None
    assert todo["due_date"] is None
    assert todo["evidence_ids"] == ["s01"]


def test_cli_providers_are_opt_in_and_use_constrained_argument_lists() -> None:
    for provider in ("ollama", "codex", "claude_code"):
        result = run_optional_cli_prompt(provider, "회의 기록을 검토해 주세요.")
        assert result["status"] == "EXPECTED_SKIP"
        assert result["error_code"] == "CLI_LIVE_OPT_IN_REQUIRED"
        assert result["command_executed"] is False
        assert result["command"][-1] == "<PROMPT>"
        assert result["shell"] is False
        assert result["external_write"] is False

    assert "read-only" in run_optional_cli_prompt("codex", "x")["command"]
    assert "--no-session-persistence" in run_optional_cli_prompt("claude_code", "x")[
        "command"
    ]
