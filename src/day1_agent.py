"""Day 1: a safe, dependency-free tool-calling loop for classroom use.

The module intentionally uses only the Python standard library. It lets every
learner run the Agent control loop before LangChain, LangGraph, or a real LLM is
introduced. A real Ollama adapter is included as an optional extension.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable
from urllib import error, request


class ToolValidationError(ValueError):
    """Raised when a requested tool or its arguments are unsafe or invalid."""


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    tool: str
    data: dict[str, Any] | None = None
    error_code: str | None = None
    message: str | None = None
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_public_text(path: str, *, workspace: Path | None = None) -> dict[str, Any]:
    """Read UTF-8 text only from the configured workspace.

    This is deliberately stricter than a general file reader so learners can
    see that tools should expose the minimum capability needed by the task.
    """

    root = (workspace or Path.cwd()).resolve()
    candidate = (root / path).resolve()
    if root != candidate and root not in candidate.parents:
        raise ToolValidationError("workspace 밖의 파일은 읽을 수 없습니다.")
    if candidate.suffix.lower() not in {".txt", ".md"}:
        raise ToolValidationError("Day 1에서는 .txt와 .md만 허용합니다.")
    if not candidate.exists():
        raise FileNotFoundError(path)
    text = candidate.read_text(encoding="utf-8")
    return {"path": str(candidate.relative_to(root)), "chars": len(text), "text": text}


def count_action_markers(text: str) -> dict[str, Any]:
    """Count simple Korean action/due-date markers without an LLM."""

    action_terms = ["까지", "하겠습니다", "작성", "정리", "검토", "승인"]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = [line for line in lines if any(term in line for term in action_terms)]
    return {"count": len(matches), "evidence": matches}


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "read_public_text": {
        "description": "워크스페이스 안의 공개 .txt/.md 파일을 읽는다.",
        "required": {"path": str},
    },
    "count_action_markers": {
        "description": "회의문에서 Action Item 후보 문장을 찾는다.",
        "required": {"text": str},
    },
}


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "read_public_text": read_public_text,
    "count_action_markers": count_action_markers,
}


def _validate_call(tool_name: str, arguments: dict[str, Any]) -> None:
    if tool_name not in TOOL_SCHEMAS:
        raise ToolValidationError(f"허용되지 않은 도구: {tool_name}")
    if not isinstance(arguments, dict):
        raise ToolValidationError("arguments는 JSON object여야 합니다.")

    required = TOOL_SCHEMAS[tool_name]["required"]
    missing = [name for name in required if name not in arguments]
    if missing:
        raise ToolValidationError(f"필수 인자 누락: {', '.join(missing)}")
    unexpected = sorted(set(arguments) - set(required))
    if unexpected:
        raise ToolValidationError(f"허용되지 않은 인자: {', '.join(unexpected)}")
    for name, expected_type in required.items():
        if not isinstance(arguments[name], expected_type):
            raise ToolValidationError(f"{name}은(는) {expected_type.__name__} 타입이어야 합니다.")


def _call_id(tool_name: str, arguments: dict[str, Any]) -> str:
    raw = json.dumps({"tool": tool_name, "arguments": arguments}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class SafeToolExecutor:
    """Validate, execute, normalize errors, and prevent duplicate side effects."""

    def __init__(self, *, workspace: Path | None = None) -> None:
        self.workspace = (workspace or Path.cwd()).resolve()
        self._cache: dict[str, ToolResult] = {}

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        try:
            _validate_call(tool_name, arguments)
        except ToolValidationError as exc:
            return ToolResult(False, tool_name, error_code="VALIDATION_ERROR", message=str(exc))

        call_id = _call_id(tool_name, arguments)
        if call_id in self._cache:
            previous = self._cache[call_id]
            return ToolResult(**{**previous.to_dict(), "cached": True})

        try:
            kwargs = dict(arguments)
            if tool_name == "read_public_text":
                kwargs["workspace"] = self.workspace
            data = TOOL_REGISTRY[tool_name](**kwargs)
            result = ToolResult(True, tool_name, data=data)
        except FileNotFoundError as exc:
            result = ToolResult(False, tool_name, error_code="NOT_FOUND", message=str(exc))
        except ToolValidationError as exc:
            result = ToolResult(False, tool_name, error_code="POLICY_BLOCKED", message=str(exc))
        except Exception as exc:  # normalized boundary; log full stack in production
            result = ToolResult(False, tool_name, error_code="TOOL_RUNTIME_ERROR", message=str(exc))

        self._cache[call_id] = result
        return result


def rule_based_planner(user_message: str) -> dict[str, Any]:
    """A deterministic stand-in for an LLM tool call.

    Keeping the planner deterministic makes the first Agent loop testable. Day 2
    replaces it with a model adapter while preserving the executor contract.
    """

    match = re.search(r"([\w./-]+\.(?:txt|md))", user_message)
    if match:
        return {"name": "read_public_text", "arguments": {"path": match.group(1)}}
    return {"name": "unknown_tool", "arguments": {}}


def run_agent_once(user_message: str, *, workspace: Path | None = None) -> dict[str, Any]:
    """Plan one tool call, execute it safely, and return an auditable event."""

    call = rule_based_planner(user_message)
    result = SafeToolExecutor(workspace=workspace).execute(call["name"], call["arguments"])
    return {
        "input": user_message,
        "planned_call": call,
        "tool_result": result.to_dict(),
        "needs_human_review": not result.ok,
    }


def call_ollama(prompt: str, *, model: str | None = None, timeout: int = 60) -> dict[str, Any]:
    """Call a local Ollama server with no third-party Python dependency."""

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    selected_model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")
    payload = json.dumps(
        {"model": selected_model, "prompt": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    req = request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return {"ok": True, "data": json.loads(response.read().decode("utf-8"))}
    except error.URLError as exc:
        return {
            "ok": False,
            "error_code": "OLLAMA_UNAVAILABLE",
            "message": "Ollama 서버와 모델을 확인하세요.",
            "detail": str(exc),
        }


def build_day1_summary(meeting_text: str) -> dict[str, Any]:
    """Create a deterministic fixture used before a real summarization model."""

    marker_result = count_action_markers(meeting_text)
    return {
        "title": "고객 문의 자동화 PoC 범위 회의",
        "summary": "배송 지연·반품 안내를 1차 범위로 정하고 외부 발행 전 휴먼 검토를 적용한다.",
        "decisions": [
            "1차 자동화 범위는 배송 지연 문의와 반품 절차 안내로 제한한다.",
            "개인정보·낮은 정확도·근거 없음은 상담원 검토 큐로 보낸다.",
        ],
        "action_items": [
            {"task": "공개 FAQ 30건 비식별 샘플 정리", "owner": "서연", "due_date": "2026-08-27"},
            {"task": "응답 JSON 스키마와 실패 테스트 작성", "owner": "준호", "due_date": "2026-08-28"},
        ],
        "evidence_line_count": marker_result["count"],
        "generated_on": date.today().isoformat(),
        "requires_human_approval": True,
    }


if __name__ == "__main__":
    event = run_agent_once("data/meeting_sample_ko.txt를 읽어줘")
    print(json.dumps(event, ensure_ascii=False, indent=2))

