from pathlib import Path
from types import SimpleNamespace

from src.ollama_tool_agent import probe_ollama, run_tool_agent
from src.openai_provider import OpenAIResponsesToolClient


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


def test_openai_provider_uses_same_safe_executor_contract() -> None:
    class FixtureOpenAIClient:
        def generate(self, prompt: str, *, model: str, timeout: int) -> str:
            assert "read_public_text" in prompt
            assert model == "gpt-5.6-luna"
            return '{"name":"read_public_text","arguments":{"path":"data/meeting_sample_ko.txt"}}'

    result = run_tool_agent(
        "data/meeting_sample_ko.txt를 읽어줘",
        workspace=ROOT,
        provider="openai",
        model="gpt-5.6-luna",
        client=FixtureOpenAIClient(),
    )
    assert result["status"] == "SUCCESS"
    assert result["provider_used"] == "openai"
    assert result["tool_result"]["ok"] is True
    assert result["external_write"] is False
    assert result["automatic_email"] is False


def test_openai_responses_client_normalizes_function_call() -> None:
    class FakeResponses:
        def __init__(self) -> None:
            self.request: dict | None = None

        def create(self, **kwargs):
            self.request = kwargs
            call = SimpleNamespace(
                type="function_call",
                name="read_public_text",
                arguments='{"path":"data/meeting_sample_ko.txt"}',
            )
            return SimpleNamespace(output=[call])

    responses = FakeResponses()
    sdk_client = SimpleNamespace(responses=responses)
    client = OpenAIResponsesToolClient(
        api_key="test-only",
        sdk_client=sdk_client,
        live_opt_in=True,
    )
    generated = client.generate("회의 파일을 읽어줘", model="gpt-5.6-luna", timeout=10)

    assert '"name": "read_public_text"' in generated
    assert responses.request["model"] == "gpt-5.6-luna"
    assert responses.request["tool_choice"] == "required"
    assert responses.request["store"] is False
    assert responses.request["tools"][0]["parameters"]["additionalProperties"] is False


def test_unavailable_openai_falls_back_without_losing_provider_evidence() -> None:
    class UnavailableClient:
        def generate(self, prompt: str, *, model: str, timeout: int) -> str:
            raise RuntimeError("OPENAI_API_KEY_MISSING")

    result = run_tool_agent(
        "data/meeting_sample_ko.txt를 읽어줘",
        workspace=ROOT,
        provider="openai",
        client=UnavailableClient(),
    )
    assert result["status"] == "SUCCESS"
    assert result["provider_requested"] == "openai"
    assert result["provider_used"] == "fixture"
    assert result["fallback_reason"] == "OPENAI_API_KEY_MISSING"
    assert result["needs_human_review"] is True


def test_openai_live_call_requires_explicit_opt_in() -> None:
    class MustNotCallResponses:
        def create(self, **kwargs):
            raise AssertionError("Responses API must not run without opt-in")

    client = OpenAIResponsesToolClient(
        api_key="test-only",
        sdk_client=SimpleNamespace(responses=MustNotCallResponses()),
        live_opt_in=False,
    )
    result = run_tool_agent(
        "data/meeting_sample_ko.txt를 읽어줘",
        workspace=ROOT,
        provider="openai",
        client=client,
    )
    assert result["provider_used"] == "fixture"
    assert result["fallback_reason"] == "OPENAI_LIVE_OPT_IN_REQUIRED"
