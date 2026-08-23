"""Executable Day 1 LangChain lab: prompt -> model adapter -> parser -> validator.

The default provider is deterministic and network-free so every learner can
execute the same LCEL pipeline. An Ollama provider can be selected after the
contract and tests pass; provider failure falls back to the same fixture
contract instead of stopping class.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    due_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    evidence_ids: list[str] = Field(min_length=1)


class MeetingBrief(BaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    decisions: list[str] = Field(min_length=1)
    action_items: list[ActionItem] = Field(min_length=1)
    risk_flags: list[str]
    requires_human_approval: bool
    automatic_email: bool


def fixture_payload() -> dict[str, Any]:
    """Return a stable classroom response that satisfies the same model contract."""

    return {
        "title": "고객 문의 자동화 PoC 범위 회의",
        "summary": "배송 지연과 반품 절차 안내만 1차 자동화 범위로 정하고, 외부 발행 전 사람이 검토한다.",
        "decisions": [
            "배송 지연과 반품 절차 안내만 자동화한다.",
            "개인정보·근거 부족·낮은 신뢰도는 상담원 검토 큐로 보낸다.",
        ],
        "action_items": [
            {
                "task": "공개 FAQ 30건 비식별 샘플 정리",
                "owner": "서연",
                "due_date": "2026-08-27",
                "evidence_ids": ["s12", "s18"],
            },
            {
                "task": "응답 JSON Schema와 실패 테스트 작성",
                "owner": "준호",
                "due_date": "2026-08-28",
                "evidence_ids": ["s27", "s31"],
            },
        ],
        "risk_flags": ["EXTERNAL_WRITE_REQUIRES_APPROVAL"],
        "requires_human_approval": True,
        "automatic_email": False,
    }


def _fixture_model(prompt_value: Any) -> str:
    """Act as a provider adapter while still executing the real LCEL chain."""

    _ = prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
    return json.dumps(fixture_payload(), ensure_ascii=False)


def normalize_provider_failure(exc: Exception) -> str:
    """Return a short, stable classroom error instead of the raw model output."""

    if isinstance(exc, OutputParserException):
        return "SCHEMA_PARSE_FAILED: model output did not match MeetingBrief"
    detail = str(exc).replace("\n", " ").strip()
    if len(detail) > 180:
        detail = f"{detail[:177]}..."
    return f"{type(exc).__name__}: {detail}"


def build_chain(*, provider: Literal["fixture", "ollama"] = "fixture", model: str = "qwen3:4b"):
    """Compose prompt, provider, typed parser, and policy validator with LCEL."""

    parser = PydanticOutputParser(pydantic_object=MeetingBrief)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "당신은 한국어 회의 기록 Agent다. 근거 ID가 없는 할 일은 만들지 말고 자동 메일을 발송하지 않는다.\n{format_instructions}",
            ),
            ("human", "다음 회의를 구조화하라.\n\n{transcript}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    if provider == "ollama":
        from langchain_ollama import ChatOllama  # type: ignore[import-not-found]

        model_runnable = ChatOllama(
            model=model,
            temperature=0,
            reasoning=False,
            num_predict=2048,
        )
    else:
        model_runnable = RunnableLambda(_fixture_model).with_config(
            run_name="fixture_meeting_model"
        )

    def policy_validator(result: MeetingBrief) -> MeetingBrief:
        if result.automatic_email:
            raise ValueError("POLICY_BLOCKED: automatic_email must remain false")
        if not result.requires_human_approval:
            raise ValueError("POLICY_BLOCKED: human approval is required")
        return result

    return (
        prompt.with_config(run_name="meeting_prompt")
        | model_runnable
        | parser.with_config(run_name="meeting_schema_parser")
        | RunnableLambda(policy_validator).with_config(run_name="policy_validator")
    )


def run_langchain_lab(
    transcript: str,
    *,
    provider: Literal["fixture", "ollama"] = "fixture",
    model: str = "qwen3:4b",
    allow_fallback: bool = True,
) -> dict[str, Any]:
    """Execute the chain and normalize optional provider failure."""

    selected_provider = provider
    fallback_reason: str | None = None
    try:
        result = build_chain(provider=provider, model=model).invoke({"transcript": transcript})
    except Exception as exc:
        if provider != "ollama" or not allow_fallback:
            raise
        fallback_reason = normalize_provider_failure(exc)
        selected_provider = "fixture"
        result = build_chain(provider="fixture").invoke({"transcript": transcript})

    return {
        "status": "SUCCESS",
        "framework": "LangChain LCEL",
        "provider_requested": provider,
        "provider_used": selected_provider,
        "fallback_reason": fallback_reason,
        "pipeline": ["ChatPromptTemplate", "Model Adapter", "PydanticOutputParser", "Policy Validator"],
        "result": result.model_dump(),
        "checks": {
            "schema_valid": True,
            "evidence_present": all(item.evidence_ids for item in result.action_items),
            "automatic_email_blocked": result.automatic_email is False,
            "human_approval_required": result.requires_human_approval is True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", type=Path, default=Path("data/meeting_sample_ko_12min.txt"))
    parser.add_argument("--out", type=Path, default=Path("output/day1-langchain/langchain_result.json"))
    parser.add_argument("--provider", choices=["fixture", "ollama"], default="fixture")
    parser.add_argument("--model", default="qwen3:4b")
    args = parser.parse_args()

    payload = run_langchain_lab(
        args.transcript.read_text(encoding="utf-8"),
        provider=args.provider,
        model=args.model,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
