from __future__ import annotations

import base64
import io
import wave

import pytest

from app.audio import AudioValidationError, inspect_audio
from app.models import ActionItem, EvidenceItem, MeetingBrief, TranscriptSegment
from app.pipeline import process_meeting, validate_evidence


MP3_SAMPLE = base64.b64decode(
    "SUQzBAAAAAAAIlRTU0UAAAAOAAADTGF2ZjYzLjEuMTAxAAAAAAAAAAAAAAD/4yjEABpwtnQfWAAAJTvAAf9/3/f9/4fjcbl8YjEMP4/kORiMUkbjb/v+78P2/lbuRFDMwnNsTjM4tM4U15bPzEMQ5GJZYwWD4Ph/BB13L+c6eJwQdUCZ/SCHL+7EADB/SCHTlw+CAY0/8uD4Ph8EAQDH////oQAAAKBQIRE0i5QBAyE3/1///gAAmBgiFQP/4yjEGSAhymx5nJACGCwl+/x//8xKOjAgbPUKo0OXNJ0Hq0kEFDxCAzulLAxDAI0DyQNpDZgtGC0L/8UiIKh8I5QuYVsQ0c3//xlSaIsQIxIqRUyLxe//dT9bmJdLqRskJQkDX9W5wlOnv/0Nu+xdhX//rpVqAAON3tgH/r///1///6/////3+EIAhgIgFBz/4yjEGxgopjZV3gAAAMCQFjA/CEMK0JIwtxtDFj16MkwZoxIwfjBZBaMCUAMGgGmAsAKBAAVqX+z2q/d9//9q7/pYuz6spVr///0/b5PXu///Sv9fv/sAIAFAYBUAnANAPoGAkgKYGBDAQgGADAlIGEshgIGHRjN4GibrkYGaHBFwAQGEBgGoGSBgXoCWBgH/4yjEPRtgphgBVxAASA1gFAR46QCABQnHW7dn09nffW7sV6LrOhj311o2V+WZ9dvf727fIvbkXV//9dhuqpXEnEZoDgKYDAAgAYUBcqzqVYfpGuLbBAEMFgsICxhoI5QDEZhHMeCZ7IhgYzmAxAYrVxw17GcRfbiVO/pQHyKXFjJwvgHqAHiAUYAEgYPCzgv/4yjEUi6rYmwBnJgBNJwj1skT5wqFRNA0WNAPeFKh8IvhSZFxsmSZzWjTPsmbqZnQHoXMOkdBQJMkBzSHEevqq6C33dXY6VCuTxMlgyNzQul4x1/9vd/tMS4bmxdMjIzNETZExMP//3//puapGS0GSRMVD1StAZy0NVeZn1JFHDiVOR2Z9VVOcDBVkQCixIj/4yjEGhIQubhZxhgAkUcOJU5tEp6IjwKjD3iU6InhvyzxKMPeJXCJ50lPRE8SuPYaiU6Innf//w0o8tVMQU1FNC4wVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVU="
)


def wav_bytes(*, seconds: float = 1.0, sample_rate: int = 8000) -> bytes:
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return stream.getvalue()


def test_fixture_pipeline_returns_grounded_ready_result() -> None:
    result = process_meeting(
        filename="sample.wav",
        content_type="audio/wav",
        data=wav_bytes(),
        stt_mode="fixture",
        provider="fixture",
    )

    assert result.status == "READY"
    assert result.stt_mode_used == "fixture"
    assert result.provider_used == "fixture"
    assert result.evidence_errors == []
    assert result.brief is not None
    assert len(result.brief.action_items) >= 1
    assert "FIXTURE_TRANSCRIPT_UPLOAD_NOT_TRANSCRIBED" in result.warnings
    assert result.human_review_required is True
    assert result.external_write is False


def test_invalid_wav_is_a_stable_hold_instead_of_traceback() -> None:
    result = process_meeting(
        filename="broken.wav",
        content_type="audio/wav",
        data=b"not-a-wave-file",
        stt_mode="fixture",
        provider="fixture",
    )

    assert result.status == "HOLD"
    assert result.stage == "audio_validation"
    assert result.error_codes == ["INVALID_WAV"]
    assert result.brief is None


def test_unknown_evidence_is_blocked() -> None:
    segments = [
        TranscriptSegment(id="s001", start=0, end=1, speaker="진행자", text="실행 범위를 확정합니다."),
    ]
    brief = MeetingBrief(
        title="회의 결과",
        summary="실행 범위와 담당 업무를 논의하고 다음 검토 일정을 확인했습니다.",
        decisions=[EvidenceItem(text="범위 확정", evidence_ids=["s001"])],
        action_items=[
            ActionItem(text="테스트 작성", assignee="개발자", evidence_ids=["s999"]),
        ],
    )

    assert validate_evidence(brief, segments) == ["ACTION_1_UNKNOWN_EVIDENCE:s999"]


def test_mp3_metadata_is_populated_by_pyav() -> None:
    metadata = inspect_audio(filename="public-meeting.mp3", content_type="audio/mpeg", data=MP3_SAMPLE)

    assert metadata.duration_seconds is not None and metadata.duration_seconds > 0
    assert metadata.sample_rate == 8000
    assert metadata.channels == 1


def test_invalid_mp3_has_stable_audio_error() -> None:
    with pytest.raises(AudioValidationError) as error:
        inspect_audio(filename="broken.mp3", content_type="audio/mpeg", data=b"ID3broken")

    assert error.value.code == "INVALID_AUDIO"
