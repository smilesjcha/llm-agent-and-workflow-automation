from pathlib import Path

from src.ollama_tool_agent import probe_ollama, run_tool_agent


ROOT = Path(__file__).resolve().parents[1]


def test_fixture_planner_executes_allowed_read() -> None:
    result = run_tool_agent(
        "data/meeting_sample_ko.txt를 읽어줘",
        workspace=ROOT,
        provider="fixture",
    )
    assert result["status"] == "SUCCESS"
    assert result["provider_used"] == "fixture"
    assert result["tool_result"]["ok"] is True
    assert result["external_write"] is False


def test_model_proposal_cannot_escape_workspace() -> None:
    result = run_tool_agent(
        "../../private.txt를 읽어줘",
        workspace=ROOT,
        provider="fixture",
    )
    assert result["status"] == "BLOCKED"
    assert result["tool_result"]["error_code"] == "POLICY_BLOCKED"
    assert result["needs_human_review"] is True


def test_unavailable_ollama_falls_back_to_same_tool_contract() -> None:
    class UnavailableClient:
        def generate(self, prompt: str, *, model: str, timeout: int) -> str:
            raise ConnectionError("local server is unavailable")

    result = run_tool_agent(
        "data/meeting_sample_ko.txt를 읽어줘",
        workspace=ROOT,
        provider="ollama",
        client=UnavailableClient(),
    )
    assert result["status"] == "SUCCESS"
    assert result["provider_requested"] == "ollama"
    assert result["provider_used"] == "fixture"
    assert "ConnectionError" in result["fallback_reason"]
    assert result["needs_human_review"] is True


def test_probe_reports_missing_cli_without_raw_failure() -> None:
    result = probe_ollama(base_url="http://127.0.0.1:1", timeout=0.01)
    assert result["server_ready"] is False
    assert result["recommended_lane"] == "fixture"
    assert result["error_code"] in {"OLLAMA_NOT_INSTALLED", "OLLAMA_SERVER_UNAVAILABLE"}
