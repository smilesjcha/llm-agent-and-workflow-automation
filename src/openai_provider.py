"""OpenAI Responses API adapters for the Day 1 provider comparison lab.

The adapters never execute tools themselves. They normalize model output into
the same contract used by the fixture and Ollama lanes, while the existing
``SafeToolExecutor`` keeps workspace and side-effect policy enforcement.
"""

from __future__ import annotations

from importlib.util import find_spec
import json
import os
from pathlib import Path
from typing import Any

from src.day1_agent import TOOL_SCHEMAS


DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"
ALLOWED_REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}


def load_project_env(path: Path | None = None) -> bool:
    """Load a local gitignored .env without overriding process variables."""

    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except ImportError:
        return False
    return bool(load_dotenv(dotenv_path=path or Path.cwd() / ".env", override=False))


def selected_openai_model(model: str | None = None) -> str:
    return model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def selected_reasoning_effort() -> str:
    requested = os.getenv("OPENAI_REASONING_EFFORT", "low").lower()
    return requested if requested in ALLOWED_REASONING_EFFORTS else "low"


def probe_openai(*, load_env: bool = True) -> dict[str, Any]:
    """Report readiness without returning or validating the secret itself."""

    if load_env:
        load_project_env()
    sdk_installed = find_spec("openai") is not None
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    live_opt_in = os.getenv("RUN_OPENAI_LIVE", "0") == "1"
    direct_call_ready = sdk_installed and api_key_configured
    return {
        "sdk_installed": sdk_installed,
        "api_key_configured": api_key_configured,
        "live_opt_in": live_opt_in,
        "direct_call_ready": direct_call_ready,
        "model": selected_openai_model(),
        "reasoning_effort": selected_reasoning_effort(),
        "error_code": None
        if sdk_installed and api_key_configured
        else "OPENAI_SDK_MISSING"
        if not sdk_installed
        else "OPENAI_API_KEY_MISSING",
        "recommended_lane": "openai" if direct_call_ready else "fixture",
        "run_all_lane": "openai" if direct_call_ready and live_opt_in else "fixture",
    }


def _function_tool_schema(name: str) -> dict[str, Any]:
    schema = TOOL_SCHEMAS[name]
    properties = {
        argument: {"type": "string"}
        for argument, argument_type in schema["required"].items()
        if argument_type is str
    }
    return {
        "type": "function",
        "name": name,
        "description": schema["description"],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(schema["required"]),
            "additionalProperties": False,
        },
        "strict": True,
    }


def _extract_function_call(response: Any) -> dict[str, Any]:
    calls = [
        item
        for item in getattr(response, "output", [])
        if getattr(item, "type", None) == "function_call"
    ]
    if len(calls) != 1:
        raise ValueError("OPENAI_SINGLE_TOOL_CALL_REQUIRED")
    call = calls[0]
    arguments = getattr(call, "arguments", None)
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if not isinstance(arguments, dict):
        raise ValueError("OPENAI_TOOL_ARGUMENTS_OBJECT_REQUIRED")
    return {"name": getattr(call, "name", ""), "arguments": arguments}


class OpenAIResponsesToolClient:
    """Request one read-only function call and return the common JSON shape."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        sdk_client: Any | None = None,
        live_opt_in: bool | None = None,
    ) -> None:
        self._api_key = api_key
        self._sdk_client = sdk_client
        self._live_opt_in = live_opt_in

    def _client(self, *, timeout: int) -> Any:
        load_project_env()
        live_opt_in = (
            self._live_opt_in
            if self._live_opt_in is not None
            else os.getenv("RUN_OPENAI_LIVE", "0") == "1"
        )
        if not live_opt_in:
            raise RuntimeError("OPENAI_LIVE_OPT_IN_REQUIRED")
        if self._sdk_client is not None:
            return self._sdk_client
        api_key = self._api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY_MISSING")
        from openai import OpenAI  # type: ignore[import-not-found]

        return OpenAI(api_key=api_key, timeout=timeout)

    def generate(self, prompt: str, *, model: str, timeout: int) -> str:
        response = self._client(timeout=timeout).responses.create(
            model=model,
            input=prompt,
            tools=[_function_tool_schema("read_public_text")],
            tool_choice="required",
            reasoning={"effort": selected_reasoning_effort()},
            store=False,
        )
        return json.dumps(_extract_function_call(response), ensure_ascii=False)


class OpenAIResponsesTextClient:
    """Return schema-constrained Responses API text for the LCEL parser."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        sdk_client: Any | None = None,
        live_opt_in: bool | None = None,
        response_model: type[Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._sdk_client = sdk_client
        self._live_opt_in = live_opt_in
        self._response_model = response_model

    def _client(self, *, timeout: int) -> Any:
        load_project_env()
        live_opt_in = (
            self._live_opt_in
            if self._live_opt_in is not None
            else os.getenv("RUN_OPENAI_LIVE", "0") == "1"
        )
        if not live_opt_in:
            raise RuntimeError("OPENAI_LIVE_OPT_IN_REQUIRED")
        if self._sdk_client is not None:
            return self._sdk_client
        api_key = self._api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY_MISSING")
        from openai import OpenAI  # type: ignore[import-not-found]

        return OpenAI(api_key=api_key, timeout=timeout)

    def generate(self, prompt: str, *, model: str, timeout: int) -> str:
        responses = self._client(timeout=timeout).responses
        if self._response_model is not None:
            response = responses.parse(
                model=model,
                input=prompt,
                text_format=self._response_model,
                reasoning={"effort": selected_reasoning_effort()},
                store=False,
            )
            parsed = getattr(response, "output_parsed", None)
            if parsed is None:
                raise ValueError("OPENAI_STRUCTURED_OUTPUT_MISSING")
            if hasattr(parsed, "model_dump_json"):
                return parsed.model_dump_json()
            if isinstance(parsed, dict):
                return json.dumps(parsed, ensure_ascii=False)
            raise ValueError("OPENAI_STRUCTURED_OUTPUT_INVALID")

        response = responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": selected_reasoning_effort()},
            store=False,
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise ValueError("OPENAI_EMPTY_RESPONSE")
        return output_text
