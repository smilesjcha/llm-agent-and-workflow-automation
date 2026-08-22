from pathlib import Path

from src.day1_agent import (
    SafeToolExecutor,
    build_day1_summary,
    count_action_markers,
    run_agent_once,
)
from src.meeting_demo import run_demo


ROOT = Path(__file__).resolve().parents[1]


def test_read_public_text_success() -> None:
    result = SafeToolExecutor(workspace=ROOT).execute(
        "read_public_text", {"path": "data/meeting_sample_ko.txt"}
    )
    assert result.ok is True
    assert result.data is not None
    assert "휴먼 검토" in result.data["text"]


def test_unknown_tool_is_blocked() -> None:
    result = SafeToolExecutor(workspace=ROOT).execute("delete_everything", {})
    assert result.ok is False
    assert result.error_code == "VALIDATION_ERROR"


def test_missing_argument_is_normalized() -> None:
    result = SafeToolExecutor(workspace=ROOT).execute("read_public_text", {})
    assert result.ok is False
    assert result.error_code == "VALIDATION_ERROR"


def test_extra_argument_is_blocked() -> None:
    result = SafeToolExecutor(workspace=ROOT).execute(
        "read_public_text", {"path": "data/meeting_sample_ko.txt", "mode": "write"}
    )
    assert result.ok is False
    assert result.error_code == "VALIDATION_ERROR"


def test_path_traversal_is_blocked() -> None:
    result = SafeToolExecutor(workspace=ROOT).execute(
        "read_public_text", {"path": "../../etc/passwd"}
    )
    assert result.ok is False
    assert result.error_code == "POLICY_BLOCKED"


def test_duplicate_call_uses_cache() -> None:
    executor = SafeToolExecutor(workspace=ROOT)
    first = executor.execute("read_public_text", {"path": "data/meeting_sample_ko.txt"})
    second = executor.execute("read_public_text", {"path": "data/meeting_sample_ko.txt"})
    assert first.ok is True
    assert second.cached is True


def test_action_markers_keep_evidence() -> None:
    result = count_action_markers("민지: 금요일까지 작성하겠습니다.\n준호: 동의합니다.")
    assert result["count"] == 1
    assert "금요일까지" in result["evidence"][0]


def test_agent_marks_failure_for_human_review() -> None:
    event = run_agent_once("무엇을 해야 하나요?", workspace=ROOT)
    assert event["needs_human_review"] is True


def test_summary_fixture_requires_approval() -> None:
    text = (ROOT / "data/meeting_sample_ko.txt").read_text(encoding="utf-8")
    result = build_day1_summary(text)
    assert len(result["action_items"]) == 2
    assert result["requires_human_approval"] is True


def test_meeting_demo_falls_back_and_writes_outputs(tmp_path: Path) -> None:
    result = run_demo(
        audio_path=tmp_path / "missing.wav",
        transcript_path=ROOT / "data/meeting_sample_ko.txt",
        output_dir=tmp_path / "demo-output",
    )
    assert result["mode"] == "fixture"
    assert result["policy"]["automatic_email"] is False
    assert result["policy"]["requires_human_approval"] is True
    assert (tmp_path / "demo-output/transcript.json").exists()
    assert (tmp_path / "demo-output/meeting_result.json").exists()
