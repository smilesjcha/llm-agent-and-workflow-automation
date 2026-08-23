"""End-to-end meeting Agent: local STT -> LangChain -> LangGraph HITL -> trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.langchain_lab import ProviderName, normalize_provider_failure, run_langchain_lab
from src.langgraph_lab import Decision
from src.meeting_demo import ensure_workspace_path, run_demo
from src.observability_lab import (
    LocalTraceRecorder,
    disable_automatic_langsmith_tracing,
    langsmith_status,
    upload_summary_to_langsmith,
)
from src.openai_provider import load_project_env


TranscriptDecision = Literal["accept", "edit", "reject"]


class MeetingAgentState(TypedDict, total=False):
    request_id: str
    transcript: str
    segments: list[dict[str, Any]]
    stt_mode: str
    stt_quality_gate: dict[str, Any]
    transcript_review: dict[str, Any]
    meeting_brief: dict[str, Any]
    provider_requested: str
    provider_used: str
    provider_fallback_reason: str | None
    validation_errors: list[str]
    summary_review: dict[str, Any]
    status: str
    export_ready: bool
    automatic_email: bool
    audit_events: list[dict[str, Any]]


def _append_event(state: MeetingAgentState, event: dict[str, Any]) -> list[dict[str, Any]]:
    return [*state.get("audit_events", []), event]


def assess_stt_node(state: MeetingAgentState) -> dict[str, Any]:
    quality_gate = state.get("stt_quality_gate", {})
    ready = quality_gate.get("decision") == "READY"
    status = "STT_READY" if ready else "STT_REVIEW_REQUIRED"
    return {
        "status": status,
        "automatic_email": False,
        "export_ready": False,
        "audit_events": _append_event(
            state,
            {
                "node": "assess_stt",
                "status": status,
                "reasons": quality_gate.get("reasons", []),
            },
        ),
    }


def route_after_stt(state: MeetingAgentState) -> str:
    return "summarize" if state.get("status") == "STT_READY" else "review_transcript"


def transcript_review_node(state: MeetingAgentState) -> Command:
    flagged_segments = [
        {
            "id": segment.get("id"),
            "start": segment.get("start"),
            "text_preview": str(segment.get("text", ""))[:120],
            "quality_flags": segment.get("quality_flags", []),
        }
        for segment in state.get("segments", [])
        if segment.get("quality_flags")
    ][:5]
    human_input = interrupt(
        {
            "stage": "transcript_review",
            "question": "STT 결과를 확인했습니다. 수락·수정·거절 중 하나를 선택하세요.",
            "quality_gate": state.get("stt_quality_gate", {}),
            "flagged_segments": flagged_segments,
            "options": ["accept", "edit", "reject"],
            "automatic_email": False,
        }
    )
    decision: TranscriptDecision = human_input.get("decision", "reject")
    review = {
        "decision": decision,
        "reviewer": human_input.get("reviewer", "day1-learner"),
        "reason": human_input.get("reason", ""),
    }
    if decision == "reject":
        return Command(
            update={
                "transcript_review": review,
                "status": "TRANSCRIPT_REJECTED",
                "audit_events": _append_event(
                    state, {"node": "review_transcript", "decision": "reject"}
                ),
            },
            goto="rejected",
        )

    transcript = state.get("transcript", "")
    if decision == "edit":
        transcript = str(human_input.get("edited_transcript", "")).strip()
        if not transcript:
            return Command(
                update={
                    "transcript_review": {
                        **review,
                        "decision": "reject",
                        "reason": "edited_transcript가 비어 있음",
                    },
                    "status": "TRANSCRIPT_REJECTED",
                    "audit_events": _append_event(
                        state, {"node": "review_transcript", "decision": "reject"}
                    ),
                },
                goto="rejected",
            )

    if not transcript.strip():
        return Command(
            update={
                "transcript_review": {
                    **review,
                    "decision": "reject",
                    "reason": "transcript가 비어 있음",
                },
                "status": "TRANSCRIPT_REJECTED",
            },
            goto="rejected",
        )

    return Command(
        update={
            "transcript": transcript,
            "transcript_review": review,
            "status": "STT_HUMAN_ACCEPTED",
            "audit_events": _append_event(
                state, {"node": "review_transcript", "decision": decision}
            ),
        },
        goto="summarize",
    )


def make_summarize_node(
    *,
    provider: ProviderName,
    model: str | None,
    allow_provider_fallback: bool,
):
    def summarize_node(state: MeetingAgentState) -> dict[str, Any]:
        try:
            chain_result = run_langchain_lab(
                state.get("transcript", ""),
                provider=provider,
                model=model,
                allow_fallback=allow_provider_fallback,
            )
        except Exception as exc:
            return {
                "status": "SUMMARY_FAILED",
                "validation_errors": [normalize_provider_failure(exc)],
                "automatic_email": False,
                "audit_events": _append_event(
                    state,
                    {
                        "node": "summarize",
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                    },
                ),
            }
        return {
            "meeting_brief": chain_result["result"],
            "provider_requested": chain_result["provider_requested"],
            "provider_used": chain_result["provider_used"],
            "provider_fallback_reason": chain_result["fallback_reason"],
            "status": "SUMMARY_CREATED",
            "automatic_email": False,
            "audit_events": _append_event(
                state,
                {
                    "node": "summarize",
                    "status": "SUCCESS",
                    "provider_used": chain_result["provider_used"],
                },
            ),
        }

    return summarize_node


def validate_summary_node(state: MeetingAgentState) -> dict[str, Any]:
    existing_errors = state.get("validation_errors", [])
    brief = state.get("meeting_brief", {})
    errors = list(existing_errors)
    if not brief.get("summary"):
        errors.append("SUMMARY_REQUIRED")
    if not brief.get("action_items"):
        errors.append("ACTION_ITEMS_REQUIRED")
    for index, item in enumerate(brief.get("action_items", []), start=1):
        if not item.get("evidence_ids"):
            errors.append(f"ACTION_{index}_EVIDENCE_REQUIRED")
    if brief.get("automatic_email") is not False:
        errors.append("AUTOMATIC_EMAIL_MUST_BE_FALSE")
    status = "SUMMARY_REVIEW_REQUIRED" if not errors else "SUMMARY_VALIDATION_FAILED"
    return {
        "validation_errors": errors,
        "status": status,
        "automatic_email": False,
        "audit_events": _append_event(
            state, {"node": "validate_summary", "status": status, "errors": errors}
        ),
    }


def route_after_summary_validation(state: MeetingAgentState) -> str:
    return "review_summary" if not state.get("validation_errors") else "failed"


def summary_review_node(state: MeetingAgentState) -> Command:
    brief = state.get("meeting_brief", {})
    human_input = interrupt(
        {
            "stage": "summary_review",
            "question": "회의 요약과 할 일을 승인·수정·거절하시겠습니까?",
            "summary": brief.get("summary"),
            "action_items": brief.get("action_items", []),
            "options": ["approve", "edit", "reject"],
            "automatic_email": False,
        }
    )
    decision: Decision = human_input.get("decision", "reject")
    review = {
        "decision": decision,
        "reviewer": human_input.get("reviewer", "day1-learner"),
        "reason": human_input.get("reason", ""),
    }
    if decision == "reject":
        return Command(
            update={
                "summary_review": review,
                "status": "SUMMARY_REJECTED",
                "audit_events": _append_event(
                    state, {"node": "review_summary", "decision": "reject"}
                ),
            },
            goto="rejected",
        )

    updated_brief = dict(brief)
    if decision == "edit":
        edited_summary = str(human_input.get("edited_summary", "")).strip()
        if not edited_summary:
            return Command(
                update={
                    "summary_review": {
                        **review,
                        "decision": "reject",
                        "reason": "edited_summary가 비어 있음",
                    },
                    "status": "SUMMARY_REJECTED",
                },
                goto="rejected",
            )
        updated_brief["summary"] = edited_summary

    return Command(
        update={
            "meeting_brief": updated_brief,
            "summary_review": review,
            "status": "SUMMARY_APPROVED",
            "audit_events": _append_event(
                state, {"node": "review_summary", "decision": decision}
            ),
        },
        goto="finalize",
    )


def finalize_node(state: MeetingAgentState) -> dict[str, Any]:
    return {
        "status": "READY_FOR_EXPORT",
        "export_ready": True,
        "automatic_email": False,
        "audit_events": _append_event(
            state,
            {
                "node": "finalize",
                "side_effect": "local_json_only",
                "automatic_email": False,
            },
        ),
    }


def rejected_node(state: MeetingAgentState) -> dict[str, Any]:
    return {
        "status": "REJECTED",
        "export_ready": False,
        "automatic_email": False,
        "audit_events": _append_event(state, {"node": "rejected"}),
    }


def failed_node(state: MeetingAgentState) -> dict[str, Any]:
    return {
        "status": "FAILED",
        "export_ready": False,
        "automatic_email": False,
        "audit_events": _append_event(
            state,
            {"node": "failed", "errors": state.get("validation_errors", [])},
        ),
    }


def build_meeting_graph(
    *,
    provider: ProviderName = "fixture",
    model: str | None = None,
    allow_provider_fallback: bool = True,
):
    builder = StateGraph(MeetingAgentState)
    builder.add_node("assess_stt", assess_stt_node)
    builder.add_node(
        "review_transcript",
        transcript_review_node,
        destinations=("summarize", "rejected"),
    )
    builder.add_node(
        "summarize",
        make_summarize_node(
            provider=provider,
            model=model,
            allow_provider_fallback=allow_provider_fallback,
        ),
    )
    builder.add_node("validate_summary", validate_summary_node)
    builder.add_node(
        "review_summary",
        summary_review_node,
        destinations=("finalize", "rejected"),
    )
    builder.add_node("finalize", finalize_node)
    builder.add_node("rejected", rejected_node)
    builder.add_node("failed", failed_node)
    builder.add_edge(START, "assess_stt")
    builder.add_conditional_edges(
        "assess_stt",
        route_after_stt,
        {"summarize": "summarize", "review_transcript": "review_transcript"},
    )
    builder.add_edge("summarize", "validate_summary")
    builder.add_conditional_edges(
        "validate_summary",
        route_after_summary_validation,
        {"review_summary": "review_summary", "failed": "failed"},
    )
    builder.add_edge("finalize", END)
    builder.add_edge("rejected", END)
    builder.add_edge("failed", END)
    return builder.compile(checkpointer=InMemorySaver())


def _interrupt_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    pending = result.get("__interrupt__", ())
    return pending[0].value if pending else None


def run_meeting_graph(
    *,
    transcript: str,
    segments: list[dict[str, Any]],
    stt_mode: str,
    stt_quality_gate: dict[str, Any],
    request_id: str,
    transcript_decision: TranscriptDecision = "accept",
    summary_decision: Decision = "approve",
    edited_transcript: str | None = None,
    edited_summary: str | None = None,
    provider: ProviderName = "fixture",
    model: str | None = None,
    allow_provider_fallback: bool = True,
) -> dict[str, Any]:
    disable_automatic_langsmith_tracing()
    graph = build_meeting_graph(
        provider=provider,
        model=model,
        allow_provider_fallback=allow_provider_fallback,
    )
    config = {"configurable": {"thread_id": request_id}}
    result = graph.invoke(
        {
            "request_id": request_id,
            "transcript": transcript,
            "segments": segments,
            "stt_mode": stt_mode,
            "stt_quality_gate": stt_quality_gate,
            "transcript_review": {},
            "meeting_brief": {},
            "validation_errors": [],
            "summary_review": {},
            "status": "CREATED",
            "export_ready": False,
            "automatic_email": False,
            "audit_events": [],
        },
        config=config,
    )

    interruptions: list[dict[str, Any]] = []
    for _ in range(2):
        payload = _interrupt_payload(result)
        if payload is None:
            break
        interruptions.append(payload)
        if payload.get("stage") == "transcript_review":
            human_input: dict[str, Any] = {
                "decision": transcript_decision,
                "reviewer": "day1-learner",
                "reason": "STT 품질 확인 후 선택",
            }
            if edited_transcript is not None:
                human_input["edited_transcript"] = edited_transcript
        elif payload.get("stage") == "summary_review":
            human_input = {
                "decision": summary_decision,
                "reviewer": "day1-learner",
                "reason": "회의 결과 확인 후 선택",
            }
            if edited_summary is not None:
                human_input["edited_summary"] = edited_summary
        else:
            human_input = {"decision": "reject", "reason": "UNKNOWN_INTERRUPT_STAGE"}
        result = graph.invoke(Command(resume=human_input), config=config)

    unresolved_interrupt = _interrupt_payload(result)
    result.pop("__interrupt__", None)
    return {
        "framework": "LangGraph",
        "request_id": request_id,
        "thread_id_reused": True,
        "interruptions": interruptions,
        "unresolved_interrupt": unresolved_interrupt,
        "final_state": result,
    }


def evaluate_meeting_agent(graph_result: dict[str, Any]) -> dict[str, Any]:
    final_state = graph_result.get("final_state", {})
    quality_gate = final_state.get("stt_quality_gate", {})
    transcript_review = final_state.get("transcript_review", {})
    stt_resolved = quality_gate.get("decision") == "READY" or transcript_review.get(
        "decision"
    ) in {"accept", "edit"}
    checks = {
        "stt_quality_resolved": stt_resolved,
        "summary_schema_valid": not final_state.get("validation_errors"),
        "summary_human_approved": final_state.get("summary_review", {}).get("decision")
        in {"approve", "edit"},
        "automatic_email_blocked": final_state.get("automatic_email") is False,
        "approved_for_local_export": final_state.get("status") == "READY_FOR_EXPORT",
    }
    return {
        "decision": "READY" if all(checks.values()) else "HOLD",
        "checks": checks,
        "metrics": {
            "segment_count": len(final_state.get("segments", [])),
            "flagged_segment_count": quality_gate.get("flagged_segment_count", 0),
            "interrupt_count": len(graph_result.get("interruptions", [])),
        },
    }


def run_meeting_agent_workflow(
    *,
    audio_path: Path,
    transcript_fixture_path: Path,
    output_dir: Path,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "ko",
    beam_size: int = 5,
    hotwords: str | None = None,
    local_files_only: bool = False,
    compare_reference: bool = True,
    transcript_decision: TranscriptDecision = "accept",
    summary_decision: Decision = "approve",
    edited_transcript: str | None = None,
    edited_summary: str | None = None,
    provider: ProviderName = "fixture",
    llm_model: str | None = None,
    allow_provider_fallback: bool = True,
    upload_langsmith: bool = False,
    data_classification: str = "local_only",
    langsmith_client: Any | None = None,
    transcriber: Callable[..., tuple[str, list[dict[str, Any]], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    disable_automatic_langsmith_tracing()
    request_id = f"meeting-agent-{summary_decision}"
    trace = LocalTraceRecorder(
        run_name="audio-meeting-agent-workflow",
        metadata={
            "request_id": request_id,
            "data_classification": data_classification,
            "contains_pii": False
            if data_classification in {"synthetic", "deidentified"}
            else None,
            "external_write": False,
        },
    )
    stt_output_dir = output_dir / "stt"
    with trace.span("local_stt_and_quality_gate", inputs={"audio": audio_path.name}) as span:
        demo_result = run_demo(
            audio_path=audio_path,
            transcript_path=transcript_fixture_path,
            output_dir=stt_output_dir,
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            language=language,
            beam_size=beam_size,
            hotwords=hotwords,
            local_files_only=local_files_only,
            compare_reference=compare_reference,
            transcriber=transcriber,
        )
        span["mode"] = demo_result["mode"]
        span["quality_decision"] = demo_result["quality_gate"]["decision"]

    transcript = (stt_output_dir / "transcript.txt").read_text(encoding="utf-8")
    with trace.span(
        "langgraph_stt_and_summary_review",
        inputs={
            "transcript_decision": transcript_decision,
            "summary_decision": summary_decision,
        },
    ) as span:
        graph_result = run_meeting_graph(
            transcript=transcript,
            segments=demo_result["segments"],
            stt_mode=demo_result["mode"],
            stt_quality_gate=demo_result["quality_gate"],
            request_id=request_id,
            transcript_decision=transcript_decision,
            summary_decision=summary_decision,
            edited_transcript=edited_transcript,
            edited_summary=edited_summary,
            provider=provider,
            model=llm_model,
            allow_provider_fallback=allow_provider_fallback,
        )
        span["final_status"] = graph_result["final_state"].get("status")
        span["interrupt_count"] = len(graph_result["interruptions"])

    with trace.span("meeting_release_gate", inputs={"request_id": request_id}) as span:
        evaluation = evaluate_meeting_agent(graph_result)
        span["decision"] = evaluation["decision"]

    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace.write_json(output_dir / "trace.json")
    if upload_langsmith:
        langsmith_result = upload_summary_to_langsmith(
            trace=trace.to_dict(),
            evaluation=evaluation,
            client=langsmith_client,
        )
    else:
        langsmith_result = {
            "uploaded": False,
            "requested": False,
            **langsmith_status(),
        }
    result = {
        "status": "SUCCESS",
        "request_id": request_id,
        "stt": demo_result,
        "langgraph": graph_result,
        "evaluation": evaluation,
        "langsmith": langsmith_result,
        "outputs": {
            "transcript_text": str(stt_output_dir / "transcript.txt"),
            "transcript_json": str(stt_output_dir / "transcript.json"),
            "meeting_result": str(stt_output_dir / "meeting_result.json"),
            "trace": str(trace_path),
            "workflow_result": str(output_dir / "workflow_result.json"),
        },
    }
    (output_dir / "workflow_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    load_project_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path, default=Path("data/demo_meeting.wav"))
    parser.add_argument(
        "--transcript-fixture",
        type=Path,
        default=Path("data/demo_meeting_transcript.txt"),
    )
    parser.add_argument("--out", type=Path, default=Path("output/day1-meeting-agent"))
    parser.add_argument("--stt-model", default="small")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="ko")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--hotwords")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--skip-reference-check", action="store_true")
    parser.add_argument(
        "--transcript-decision",
        choices=["accept", "edit", "reject"],
        default="accept",
    )
    parser.add_argument(
        "--summary-decision",
        choices=["approve", "edit", "reject"],
        default="approve",
    )
    parser.add_argument("--edited-transcript")
    parser.add_argument("--edited-summary")
    parser.add_argument("--provider", choices=["fixture", "ollama", "openai"], default="fixture")
    parser.add_argument("--llm-model")
    parser.add_argument("--no-provider-fallback", action="store_true")
    parser.add_argument("--upload-langsmith", action="store_true")
    parser.add_argument(
        "--data-classification",
        choices=["local_only", "synthetic", "deidentified"],
        default="local_only",
    )
    args = parser.parse_args()
    workspace_root = Path.cwd().resolve()
    audio_path = ensure_workspace_path(args.audio, workspace_root)
    transcript_fixture_path = ensure_workspace_path(args.transcript_fixture, workspace_root)
    output_dir = ensure_workspace_path(args.out, workspace_root)
    result = run_meeting_agent_workflow(
        audio_path=audio_path,
        transcript_fixture_path=transcript_fixture_path,
        output_dir=output_dir,
        model_size=args.stt_model,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
        hotwords=args.hotwords,
        local_files_only=args.local_files_only,
        compare_reference=not args.skip_reference_check,
        transcript_decision=args.transcript_decision,
        summary_decision=args.summary_decision,
        edited_transcript=args.edited_transcript,
        edited_summary=args.edited_summary,
        provider=args.provider,
        llm_model=args.llm_model,
        allow_provider_fallback=not args.no_provider_fallback,
        upload_langsmith=args.upload_langsmith,
        data_classification=args.data_classification,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "stt_mode": result["stt"]["mode"],
                "stt_quality_gate": result["stt"]["quality_gate"]["decision"],
                "graph_status": result["langgraph"]["final_state"].get("status"),
                "release_gate": result["evaluation"]["decision"],
                "interrupt_stages": [
                    item.get("stage") for item in result["langgraph"]["interruptions"]
                ],
                "provider_used": result["langgraph"]["final_state"].get("provider_used"),
                "langsmith": result["langsmith"],
                "outputs": result["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.upload_langsmith and not result["langsmith"].get("uploaded"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
