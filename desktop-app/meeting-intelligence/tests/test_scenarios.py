from __future__ import annotations

from pathlib import Path

import pytest

from app.models import TranscriptSegment
from app.pipeline import process_request, route_execution
from tests.test_pipeline import wav_bytes


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GOOGLE_MEET = (FIXTURES / "google_meet_sample_ko.txt").read_bytes()
CLOVA_NOTE = (FIXTURES / "clova_note_sample_ko.txt").read_bytes()
PARTICIPANTS = (FIXTURES / "participants_sample.json").read_text(encoding="utf-8")


def run_text(source_mode: str, data: bytes, **kwargs):
    return process_request(
        source_mode=source_mode,
        source_filename="meeting.txt",
        content_type="text/plain",
        source_data=data,
        participants_raw=kwargs.pop("participants_raw", PARTICIPANTS),
        provider=kwargs.pop("provider", "fixture"),
        **kwargs,
    )


def test_google_meet_text_and_participant_metadata_normal_path() -> None:
    result = run_text(
        "google_meet",
        GOOGLE_MEET,
        domain_context="B2B 고객 상담 SaaS의 제품·보안 검토 회의",
        prior_context="지난 회의에서 자동 발송은 위험하다는 의견이 있었습니다.",
        requested_outputs=["summary", "participant_perspectives", "todos", "insights"],
        execution_mode="auto",
    )

    assert result.status == "READY"
    assert result.source_mode == "google_meet"
    assert result.stt_mode_requested == "not_required"
    assert result.execution_mode_used == "workflow"
    assert len(result.participants) == 3
    assert result.meeting_record is not None
    assert result.meeting_record.participant_perspectives
    assert result.evidence
    assert result.markdown_preview and "근거:" in result.markdown_preview
    assert result.email_draft and result.email_draft.send_status == "DRAFT_ONLY"
    assert result.external_write is False
    assert all(item.approval_required and item.status == "PLAN_ONLY" for item in result.integration_plan)


def test_clova_note_numbered_speakers_are_mapped_to_participants() -> None:
    result = run_text(
        "clova_note",
        CLOVA_NOTE,
        requested_outputs=["summary", "participant_perspectives", "todos"],
        execution_mode="workflow",
    )

    assert result.status == "READY"
    assert result.source_mode == "clova_note"
    assert [segment.speaker for segment in result.segments[:3]] == ["김민지", "박준호", "이서연"]
    assert result.meeting_record is not None
    assert result.meeting_record.action_items
    assert result.meeting_record.short_term_insights == []


def test_audio_normal_path_uses_real_live_adapter_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    segments = [
        TranscriptSegment(id="s001", start=0, end=4, speaker="화자 미상", text="오늘은 시범 서비스 범위를 결정하겠습니다."),
        TranscriptSegment(id="s002", start=4, end=9, speaker="화자 미상", text="금요일까지 정상 흐름과 실패 흐름을 준비하겠습니다."),
        TranscriptSegment(id="s003", start=9, end=14, speaker="화자 미상", text="자동 발송 없이 사람이 검토하는 방식으로 확정합니다."),
    ]
    monkeypatch.setattr("app.pipeline.live_transcribe", lambda **_: segments)

    result = process_request(
        source_mode="audio",
        source_filename="meeting.wav",
        content_type="audio/wav",
        source_data=wav_bytes(seconds=1),
        provider="fixture",
        requested_outputs=["summary", "todos"],
        execution_mode="auto",
    )

    assert result.status == "READY"
    assert result.stt_mode_requested == "live"
    assert result.stt_mode_used == "live:faster-whisper"
    assert result.audio is not None
    assert "SPEAKER_LABELS_REQUIRE_REVIEW" in result.warnings


@pytest.mark.parametrize(
    ("source_mode", "data", "expected"),
    [
        ("google_meet", b"x", "TRANSCRIPT_PARSE_FAILED"),
        ("clova_note", b"\xff\xfe\x00\x00", "TRANSCRIPT_ENCODING_UNSUPPORTED"),
        ("audio", b"not-a-wave", "INVALID_WAV"),
    ],
)
def test_three_source_boundaries_return_stable_hold(source_mode: str, data: bytes, expected: str) -> None:
    result = process_request(
        source_mode=source_mode,
        source_filename="meeting.wav" if source_mode == "audio" else "meeting.txt",
        content_type="audio/wav" if source_mode == "audio" else "text/plain",
        source_data=data,
        provider="fixture",
    )

    assert result.status == "HOLD"
    assert expected in result.error_codes
    assert result.external_write is False
    assert result.integration_plan == []


def test_auto_router_uses_agent_only_for_adaptive_external_request() -> None:
    used, reason, steps = route_execution(
        "auto",
        source_mode="google_meet",
        requested_outputs=["summary", "todos"],
        domain_context="",
        prior_context="",
        adaptive_request="기존 Notion 기록도 찾아서 이메일 초안 계획을 만들어 주세요.",
    )

    assert used == "agent"
    assert "계획" in reason
    assert "외부 작업 계획 분리" in steps


def test_invalid_openai_model_has_stable_fixture_fallback_without_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "this-value-must-never-appear")
    result = run_text(
        "google_meet",
        GOOGLE_MEET,
        provider="openai",
        model="invalid model with spaces",
        allow_fixture_fallback=True,
    )

    payload = result.model_dump(mode="json")
    assert result.status == "READY"
    assert result.provider_used == "fixture"
    assert result.fallback_reason == "OPENAI_MODEL_INVALID"
    assert "this-value-must-never-appear" not in str(payload)


def test_invalid_openai_model_without_fallback_is_hold() -> None:
    result = run_text(
        "google_meet",
        GOOGLE_MEET,
        provider="openai",
        model="invalid model with spaces",
        allow_fixture_fallback=False,
    )

    assert result.status == "HOLD"
    assert result.error_codes == ["OPENAI_MODEL_INVALID"]
    assert result.meeting_record is None
