"""Fixture, Ollama, and OpenAI Tool Calling lab used from Day 1 period 4.

The model only proposes a tool call. ``SafeToolExecutor`` remains the only
execution boundary, so a local model can never widen file or write access.
When an optional provider is unavailable or returns unusable output, the same
lesson continues with a deterministic fixture planner and records why.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Literal, Protocol
from urllib import error, request

from src.day1_agent import SafeToolExecutor, TOOL_SCHEMAS
from src.openai_provider import DEFAULT_OPENAI_MODEL, OpenAIResponsesToolClient


ProviderName = Literal["fixture", "ollama", "openai"]


class GenerateClient(Protocol):
    def generate(self, prompt: str, *, model: str, timeout: int) -> str: ...


class OllamaGenerateClient:
    """Call Ollama's local generate endpoint without a cloud API or SDK."""

    def __init__(self, *, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")

    def generate(self, prompt: str, *, model: str, timeout: int) -> str:
        payload = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "think": False,
                "options": {"temperature": 0, "num_predict": 512},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        generated = body.get("response")
        if not isinstance(generated, str) or not generated.strip():
            raise ValueError("OLLAMA_EMPTY_RESPONSE")
        return generated


def probe_ollama(*, base_url: str | None = None, timeout: float = 2.0) -> dict[str, Any]:
    """Return CLI, server, and local model readiness without raising."""

    endpoint = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
    cli_path = shutil.which("ollama")
    version: str | None = None
    models: list[str] = []
    error_code: str | None = None
    try:
        with request.urlopen(f"{endpoint}/api/version", timeout=timeout) as response:
            version = json.loads(response.read().decode("utf-8")).get("version")
        with request.urlopen(f"{endpoint}/api/tags", timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        models = [item.get("name", "") for item in body.get("models", []) if item.get("name")]
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        error_code = "OLLAMA_NOT_INSTALLED" if cli_path is None else "OLLAMA_SERVER_UNAVAILABLE"
        detail = f"{type(exc).__name__}: {exc}"
    else:
        detail = None
        if not models:
            error_code = "OLLAMA_MODEL_MISSING"

    return {
        "cli_installed": cli_path is not None,
        "cli_path": cli_path,
        "server_ready": version is not None,
        "version": version,
        "models": models,
        "model_ready": bool(models),
        "error_code": error_code,
        "detail": detail,
        "recommended_lane": "ollama" if version and models else "fixture",
    }


def build_tool_prompt(user_message: str) -> str:
    """Describe the narrow read-only tool contract to the local model."""

    tool_description = {
        name: {"description": schema["description"], "required": list(schema["required"])}
        for name, schema in TOOL_SCHEMAS.items()
        if name == "read_public_text"
    }
    return f"""당신은 읽기 전용 업무 Agent의 planner다.
실행할 수 있는 도구는 아래 JSON에 있는 것뿐이다.
{json.dumps(tool_description, ensure_ascii=False)}

규칙:
- 사용자가 txt 또는 md 파일 읽기를 요청하면 read_public_text를 선택한다.
- 파일 경로를 바꾸거나 추측하지 않는다.
- 메일, 삭제, shell, 외부 쓰기를 제안하지 않는다.
- 출력은 설명 없이 다음 JSON object 한 개만 반환한다.
{{"name":"read_public_text","arguments":{{"path":"..."}}}}

사용자 요청: {user_message}
"""


def fixture_tool_call(user_message: str) -> dict[str, Any]:
    """Return the same call shape without requiring a model installation."""

    match = re.search(r"([^\s]+\.(?:txt|md))", user_message)
    if match:
        return {"name": "read_public_text", "arguments": {"path": match.group(1)}}
    return {"name": "unknown_tool", "arguments": {}}


def parse_tool_call(raw_text: str) -> dict[str, Any]:
    """Parse one JSON object and reject non-contract model output."""

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("TOOL_CALL_OBJECT_REQUIRED")
    if not isinstance(payload.get("name"), str):
        raise ValueError("TOOL_NAME_REQUIRED")
    if not isinstance(payload.get("arguments"), dict):
        raise ValueError("TOOL_ARGUMENTS_OBJECT_REQUIRED")
    return {"name": payload["name"], "arguments": payload["arguments"]}


def normalize_provider_failure(exc: Exception) -> str:
    """Keep fallback evidence short and avoid leaking request internals."""

    stable_codes = {
        "OPENAI_API_KEY_MISSING",
        "OPENAI_EMPTY_RESPONSE",
        "OPENAI_LIVE_OPT_IN_REQUIRED",
        "OPENAI_SINGLE_TOOL_CALL_REQUIRED",
        "OPENAI_STRUCTURED_OUTPUT_INVALID",
        "OPENAI_STRUCTURED_OUTPUT_MISSING",
        "OPENAI_TOOL_ARGUMENTS_OBJECT_REQUIRED",
        "OLLAMA_EMPTY_RESPONSE",
    }
    detail = str(exc).replace("\n", " ").strip()
    if detail in stable_codes:
        return detail
    if len(detail) > 160:
        detail = f"{detail[:157]}..."
    return f"{type(exc).__name__}: {detail}"


def default_model(provider: ProviderName) -> str | None:
    if provider == "ollama":
        return os.getenv("OLLAMA_MODEL", "qwen3:4b")
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    return None


def plan_tool_call(
    user_message: str,
    *,
    provider: ProviderName = "fixture",
    model: str | None = None,
    allow_fallback: bool = True,
    client: GenerateClient | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Create a tool proposal and make provider fallback explicit."""

    selected_model = model or default_model(provider)
    provider_used: ProviderName = provider
    fallback_reason: str | None = None
    raw_response: str | None = None
    if provider == "fixture":
        tool_call = fixture_tool_call(user_message)
    else:
        try:
            selected_client = client
            if selected_client is None:
                selected_client = (
                    OllamaGenerateClient()
                    if provider == "ollama"
                    else OpenAIResponsesToolClient(live_opt_in=True)
                )
            assert selected_model is not None
            raw_response = selected_client.generate(
                build_tool_prompt(user_message),
                model=selected_model,
                timeout=timeout,
            )
            tool_call = parse_tool_call(raw_response)
        except Exception as exc:
            if not allow_fallback:
                raise
            provider_used = "fixture"
            fallback_reason = normalize_provider_failure(exc)
            tool_call = fixture_tool_call(user_message)

    return {
        "provider_requested": provider,
        "provider_used": provider_used,
        "model": selected_model,
        "fallback_reason": fallback_reason,
        "raw_response": raw_response,
        "tool_call": tool_call,
    }


def run_tool_agent(
    user_message: str,
    *,
    workspace: Path | None = None,
    provider: ProviderName = "fixture",
    model: str | None = None,
    allow_fallback: bool = True,
    client: GenerateClient | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Plan with a selected provider, then execute through one safe boundary."""

    plan = plan_tool_call(
        user_message,
        provider=provider,
        model=model,
        allow_fallback=allow_fallback,
        client=client,
        timeout=timeout,
    )
    call = plan["tool_call"]
    result = SafeToolExecutor(workspace=workspace).execute(call["name"], call["arguments"])
    return {
        "status": "SUCCESS" if result.ok else "BLOCKED",
        "input": user_message,
        **plan,
        "tool_result": result.to_dict(),
        "needs_human_review": not result.ok or plan["fallback_reason"] is not None,
        "external_write": False,
        "automatic_email": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", default="data/meeting_sample_ko.txt를 읽어줘")
    parser.add_argument("--provider", choices=["fixture", "ollama", "openai"], default="fixture")
    parser.add_argument("--model")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()

    payload = probe_ollama() if args.probe else run_tool_agent(
        args.message,
        workspace=Path.cwd(),
        provider=args.provider,
        model=args.model,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
