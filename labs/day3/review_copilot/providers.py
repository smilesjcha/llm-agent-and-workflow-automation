"""Injectable LLM provider boundary with deterministic fixture fallback."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any, Protocol
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import ValidationError

from .contracts import ProviderCandidate


class ReviewProvider(Protocol):
    name: str
    model: str

    def review(self, prompt: dict[str, Any]) -> list[dict[str, Any]]: ...


class ProviderUnavailable(RuntimeError):
    """Expected provider failure that may safely use the fixture fallback."""


class FixtureReviewProvider:
    """A stable classroom provider; it performs no network call."""

    name = "fixture"
    model = "deterministic-review-fixture-v1"

    def __init__(self, responses: Mapping[str, list[dict[str, Any]]]) -> None:
        self._responses = responses

    def review(self, prompt: dict[str, Any]) -> list[dict[str, Any]]:
        case_id = str(prompt.get("case_id", "default"))
        return [dict(item) for item in self._responses.get(case_id, [])]


class UnavailableReviewProvider:
    """Useful in class to demonstrate an unavailable live model."""

    def __init__(
        self,
        name: str,
        reason: str = "PROVIDER_NOT_CONFIGURED",
        *,
        model: str = "unconfigured",
    ) -> None:
        self.name = name
        self.reason = reason
        self.model = model

    def review(self, prompt: dict[str, Any]) -> list[dict[str, Any]]:
        del prompt
        raise ProviderUnavailable(self.reason)


class LangChainReviewProvider:
    """Adapter for an injected LangChain Runnable; LangChain is not a hard dependency.

    A notebook may pass any object exposing ``invoke(prompt)``.  The adapter
    accepts a list, ``{"candidates": [...]}``, or an AIMessage-like object whose
    ``content`` is JSON.  Credentials remain inside the model configuration and
    are never part of the prompt or result.
    """

    def __init__(
        self,
        runnable: Any,
        *,
        name: str = "langchain",
        model: str | None = None,
    ) -> None:
        self.name = name
        self.model = model or str(getattr(runnable, "model_name", "injected-runnable"))
        self._runnable = runnable

    def review(self, prompt: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            output = self._runnable.invoke(prompt)
        except Exception as exc:
            raise ProviderUnavailable("PROVIDER_CALL_FAILED") from exc
        if hasattr(output, "content"):
            output = output.content
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError as exc:
                raise ProviderUnavailable("LANGCHAIN_OUTPUT_NOT_JSON") from exc
        if isinstance(output, dict):
            output = output.get("candidates")
        if not isinstance(output, list) or not all(isinstance(item, dict) for item in output):
            raise ProviderUnavailable("LANGCHAIN_OUTPUT_CONTRACT_INVALID")
        return [dict(item) for item in output]


class OllamaReviewProvider:
    """Explicit localhost-only Ollama adapter for the optional qwen3:4b lab."""

    name = "ollama"

    def __init__(
        self,
        *,
        model: str = "qwen3:4b",
        endpoint: str = "http://127.0.0.1:11434/api/generate",
        timeout_seconds: float = 60.0,
        live_opt_in: bool = False,
    ) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("OLLAMA_LOOPBACK_ENDPOINT_REQUIRED")
        if not model.strip():
            raise ValueError("OLLAMA_MODEL_REQUIRED")
        if timeout_seconds <= 0 or timeout_seconds > 180:
            raise ValueError("OLLAMA_TIMEOUT_INVALID")
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.live_opt_in = live_opt_in

    def review(self, prompt: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.live_opt_in:
            raise ProviderUnavailable("OLLAMA_LIVE_OPT_IN_REQUIRED")
        instruction = {
            "task": "추가된 코드 줄에서만 ReviewFinding 후보를 JSON으로 작성",
            "output": {"candidates": "list[ReviewFinding]"},
            "rules": [
                "존재하지 않는 path와 line을 만들지 않음",
                "style-only finding 제외",
                "실행하지 않은 test 결과를 근거로 사용하지 않음",
            ],
            "input": prompt,
        }
        request = Request(
            self.endpoint,
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": json.dumps(instruction, ensure_ascii=False),
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0},
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(1_000_001)
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailable(f"OLLAMA_UNAVAILABLE:{type(exc).__name__}") from exc
        if len(raw) > 1_000_000:
            raise ProviderUnavailable("OLLAMA_RESPONSE_TOO_LARGE")
        try:
            envelope = json.loads(raw.decode("utf-8"))
            output = json.loads(str(envelope["response"]))
            candidates = output["candidates"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ProviderUnavailable("OLLAMA_OUTPUT_CONTRACT_INVALID") from exc
        if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):
            raise ProviderUnavailable("OLLAMA_OUTPUT_CONTRACT_INVALID")
        return [dict(item) for item in candidates]


def run_provider(
    *,
    requested: ReviewProvider,
    fallback: FixtureReviewProvider,
    prompt: dict[str, Any],
    allow_fallback: bool,
) -> dict[str, Any]:
    """Return provider provenance so a fixture result is never labelled live."""

    def validate_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            return [
                ProviderCandidate.model_validate(item).model_dump(mode="json")
                for item in candidates
            ]
        except (TypeError, ValidationError) as exc:
            raise ProviderUnavailable("PROVIDER_SCHEMA_INVALID") from exc

    try:
        candidates = validate_candidates(requested.review(prompt))
        return {
            "status": "SUCCESS",
            "provider_requested": requested.name,
            "provider_used": requested.name,
            "requested_model": requested.model,
            "model": requested.model,
            "schema_valid": True,
            "fallback_reason": None,
            "candidates": candidates,
        }
    except ProviderUnavailable as exc:
        if not allow_fallback:
            return {
                "status": "EXPECTED_FAILURE",
                "provider_requested": requested.name,
                "provider_used": None,
                "requested_model": requested.model,
                "model": None,
                "schema_valid": False,
                "fallback_reason": None,
                "error_code": str(exc),
                "candidates": [],
            }
        try:
            fallback_candidates = validate_candidates(fallback.review(prompt))
        except ProviderUnavailable:
            return {
                "status": "EXPECTED_FAILURE",
                "provider_requested": requested.name,
                "provider_used": None,
                "requested_model": requested.model,
                "model": None,
                "schema_valid": False,
                "fallback_reason": str(exc),
                "error_code": "FIXTURE_SCHEMA_INVALID",
                "candidates": [],
            }
        return {
            "status": "SUCCESS",
            "provider_requested": requested.name,
            "provider_used": fallback.name,
            "requested_model": requested.model,
            "model": fallback.model,
            "schema_valid": True,
            "fallback_reason": str(exc),
            "candidates": fallback_candidates,
        }
