from pathlib import Path

from src.meeting_agent_workflow import (
    evaluate_meeting_agent,
    run_meeting_agent_workflow,
    run_meeting_graph,
)
from src.meeting_demo import (
    _rounded_float,
    detect_quality_flags,
    transcript_reference_similarity,
)


class FloatLikeScalar:
    def __float__(self) -> float:
        return 0.987654


def _ready_gate() -> dict:
    return {
        "decision": "READY",
        "reasons": [],
        "flagged_segment_count": 0,
        "human_decision_required": True,
    }


def _hold_gate() -> dict:
    return {
        "decision": "HOLD",
        "reasons": ["STT_FALLBACK_USED"],
        "flagged_segment_count": 0,
        "human_decision_required": True,
    }


def test_stt_scalar_is_normalized_for_langgraph_checkpoint() -> None:
    value = _rounded_float(FloatLikeScalar())
    assert value == 0.9877
    assert type(value) is float


def test_no_speech_probability_uses_whisper_combined_threshold() -> None:
    assert detect_quality_flags(
        "정상 발화",
        average_log_probability=-0.4,
        no_speech_probability=0.9,
    ) == []
    assert detect_quality_flags(
        "의심 발화",
        average_log_probability=-1.2,
        no_speech_probability=0.9,
    ) == ["LOW_AVERAGE_LOG_PROBABILITY", "HIGH_NO_SPEECH_PROBABILITY"]


def test_reference_similarity_ignores_timestamp_and_speaker_label() -> None:
    expected = "[00:00] 민지: 배송 지연 문의를 확인합니다."
    actual = "[s01][00:01] 화자미상: 배송 지연 문의를 확인합니다."
    assert transcript_reference_similarity(actual, expected) == 1.0


def test_ready_stt_moves_directly_to_summary_review() -> None:
    graph_result = run_meeting_graph(
        transcript="합성 회의 전사문입니다. 배송 지연과 반품 안내를 논의했습니다.",
        segments=[{"id": "s01", "text": "합성 회의", "quality_flags": []}],
        stt_mode="local_stt",
        stt_quality_gate=_ready_gate(),
        request_id="ready-stt",
        summary_decision="approve",
    )
    assert [item["stage"] for item in graph_result["interruptions"]] == [
        "summary_review"
    ]
    assert graph_result["final_state"]["status"] == "READY_FOR_EXPORT"
    assert evaluate_meeting_agent(graph_result)["decision"] == "READY"


def test_hold_stt_requires_transcript_review_before_summary_review() -> None:
    graph_result = run_meeting_graph(
        transcript="fallback으로 불러온 합성 회의 전사문입니다. 사람이 먼저 확인합니다.",
        segments=[{"id": "s01", "text": "합성 회의", "quality_flags": []}],
        stt_mode="fixture",
        stt_quality_gate=_hold_gate(),
        request_id="hold-stt",
        transcript_decision="accept",
        summary_decision="approve",
    )
    assert [item["stage"] for item in graph_result["interruptions"]] == [
        "transcript_review",
        "summary_review",
    ]
    assert graph_result["final_state"]["transcript_review"]["decision"] == "accept"
    assert graph_result["final_state"]["status"] == "READY_FOR_EXPORT"


def test_rejected_transcript_never_reaches_summary() -> None:
    graph_result = run_meeting_graph(
        transcript="품질이 낮은 합성 전사문입니다.",
        segments=[{"id": "s01", "text": "합성 회의", "quality_flags": []}],
        stt_mode="fixture",
        stt_quality_gate=_hold_gate(),
        request_id="reject-stt",
        transcript_decision="reject",
    )
    assert [item["stage"] for item in graph_result["interruptions"]] == [
        "transcript_review"
    ]
    assert graph_result["final_state"]["status"] == "REJECTED"
    assert "provider_used" not in graph_result["final_state"]
    assert evaluate_meeting_agent(graph_result)["decision"] == "HOLD"


def test_end_to_end_local_stt_writes_all_evidence_files(tmp_path: Path) -> None:
    audio_path = tmp_path / "synthetic.wav"
    fixture_path = tmp_path / "fixture.txt"
    audio_path.write_bytes(b"synthetic-audio-placeholder")
    fixture_path.write_text("fallback fixture", encoding="utf-8")

    def fake_transcriber(*args, **kwargs):
        del args, kwargs
        text = "[00:00] 화자미상: 배송 지연과 반품 안내 범위를 논의하고 담당자와 기한을 정했습니다."
        segments = [
            {
                "id": "s01",
                "start": 0.0,
                "end": 8.0,
                "speaker": None,
                "text": "배송 지연과 반품 안내 범위를 논의하고 담당자와 기한을 정했습니다.",
                "quality_flags": [],
            }
        ]
        metadata = {
            "language": "ko",
            "language_probability": 0.99,
            "duration_seconds": 8.0,
            "duration_after_vad_seconds": 7.5,
            "model": "test-model",
        }
        return text, segments, metadata

    output_dir = tmp_path / "result"
    result = run_meeting_agent_workflow(
        audio_path=audio_path,
        transcript_fixture_path=fixture_path,
        output_dir=output_dir,
        compare_reference=False,
        transcriber=fake_transcriber,
    )
    assert result["stt"]["mode"] == "local_stt"
    assert result["stt"]["quality_gate"]["decision"] == "READY"
    assert result["evaluation"]["decision"] == "READY"
    assert result["langgraph"]["final_state"]["automatic_email"] is False
    assert (output_dir / "stt/transcript.txt").exists()
    assert (output_dir / "stt/transcript.json").exists()
    assert (output_dir / "stt/meeting_result.json").exists()
    assert (output_dir / "trace.json").exists()
    assert (output_dir / "workflow_result.json").exists()
