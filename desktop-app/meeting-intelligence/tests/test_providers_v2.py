from __future__ import annotations

import json

import pytest

from app.models import TranscriptSegment
from app.providers import ProviderError, fixture_summarize, openai_summarize


SEGMENTS = [
    TranscriptSegment(id="s001", start=0, end=3, speaker="김민지", text="오늘 회의 범위를 확정하겠습니다."),
    TranscriptSegment(id="s002", start=3, end=7, speaker="박준호", text="금요일까지 테스트 결과를 공유하겠습니다."),
]


def test_openai_adapter_posts_responses_schema_and_validates_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")
    expected = fixture_summarize(SEGMENTS)
    captured: dict = {}

    def fake_post(url, payload, *, headers, openai_errors, **_):
        captured.update(url=url, payload=payload, headers=headers, openai_errors=openai_errors)
        return {"output_text": json.dumps(expected.model_dump(mode="json"), ensure_ascii=False)}

    monkeypatch.setattr("app.providers._post_json", fake_post)

    record = openai_summarize(prompt="회의 전사와 근거를 구조화해 주세요.", model="gpt-5.6-luna")

    assert record.title == expected.title
    assert captured["url"].endswith("/responses")
    assert captured["payload"]["text"]["format"]["type"] == "json_schema"
    assert captured["headers"]["Authorization"] == "Bearer secret-value"
    assert captured["openai_errors"] is True


def test_openai_adapter_requires_env_key_without_accepting_request_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ProviderError) as error:
        openai_summarize(prompt="회의 전사와 근거를 구조화해 주세요.", model="gpt-5.6-luna")

    assert error.value.code == "OPENAI_API_KEY_MISSING"
