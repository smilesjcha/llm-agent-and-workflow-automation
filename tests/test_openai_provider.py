import json
from types import SimpleNamespace

import pytest

from src.langchain_lab import MeetingBrief, fixture_payload
from src.openai_provider import OpenAIResponsesTextClient, probe_openai


class FakeResponses:
    def __init__(self, *, parsed) -> None:
        self.parsed = parsed
        self.request: dict | None = None

    def parse(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(output_parsed=self.parsed)

    def create(self, **kwargs):
        raise AssertionError("Structured output must use responses.parse")


def test_structured_text_client_returns_meeting_brief_json() -> None:
    responses = FakeResponses(parsed=MeetingBrief.model_validate(fixture_payload()))
    client = OpenAIResponsesTextClient(
        sdk_client=SimpleNamespace(responses=responses),
        live_opt_in=True,
        response_model=MeetingBrief,
    )

    generated = client.generate("회의를 구조화하라", model="gpt-5.6-luna", timeout=30)
    payload = json.loads(generated)

    assert payload["automatic_email"] is False
    assert payload["requires_human_approval"] is True
    assert responses.request["model"] == "gpt-5.6-luna"
    assert responses.request["text_format"] is MeetingBrief
    assert responses.request["store"] is False


def test_structured_text_client_rejects_missing_parsed_output() -> None:
    responses = FakeResponses(parsed=None)
    client = OpenAIResponsesTextClient(
        sdk_client=SimpleNamespace(responses=responses),
        live_opt_in=True,
        response_model=MeetingBrief,
    )

    with pytest.raises(ValueError, match="OPENAI_STRUCTURED_OUTPUT_MISSING"):
        client.generate("회의를 구조화하라", model="gpt-5.6-luna", timeout=30)


def test_probe_separates_direct_call_from_notebook_run_all(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("RUN_OPENAI_LIVE", "0")

    status = probe_openai(load_env=False)

    assert status["direct_call_ready"] is True
    assert status["recommended_lane"] == "openai"
    assert status["run_all_lane"] == "fixture"
