"""Executable Day 1 LangGraph lab with interrupt and human resume."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


Decision = Literal["approve", "edit", "reject"]


class WorkflowState(TypedDict, total=False):
    request_id: str
    draft: dict[str, Any]
    validation_errors: list[str]
    status: str
    review: dict[str, Any]
    audit_events: list[dict[str, Any]]
    export_ready: bool
    automatic_email: bool


def _append_event(state: WorkflowState, event: dict[str, Any]) -> list[dict[str, Any]]:
    return [*state.get("audit_events", []), event]


def validate_node(state: WorkflowState) -> dict[str, Any]:
    errors: list[str] = []
    draft = state.get("draft", {})
    if not draft.get("summary"):
        errors.append("SUMMARY_REQUIRED")
    if not draft.get("action_items"):
        errors.append("ACTION_ITEMS_REQUIRED")
    for index, item in enumerate(draft.get("action_items", []), start=1):
        if not item.get("evidence_ids"):
            errors.append(f"ACTION_{index}_EVIDENCE_REQUIRED")
    status = "FAILED" if errors else "REVIEW_REQUIRED"
    return {
        "validation_errors": errors,
        "status": status,
        "automatic_email": False,
        "export_ready": False,
        "audit_events": _append_event(
            state,
            {"node": "validate", "status": status, "errors": errors},
        ),
    }


def route_after_validate(state: WorkflowState) -> str:
    return "review" if not state.get("validation_errors") else "failed"


def review_node(state: WorkflowState) -> Command:
    payload = {
        "question": "회의 결과를 승인·수정·거절하시겠습니까?",
        "request_id": state["request_id"],
        "summary": state["draft"]["summary"],
        "action_items": state["draft"]["action_items"],
        "risk_flags": state["draft"].get("risk_flags", []),
        "options": ["approve", "edit", "reject"],
        "automatic_email": False,
    }
    human_input = interrupt(payload)
    decision: Decision = human_input.get("decision", "reject")
    review = {
        "decision": decision,
        "reviewer": human_input.get("reviewer", "learner"),
        "reason": human_input.get("reason", ""),
    }
    draft = dict(state["draft"])
    if decision == "edit":
        edited_summary = human_input.get("edited_summary", "").strip()
        if not edited_summary:
            return Command(
                update={
                    "status": "REJECTED",
                    "review": {**review, "reason": "edited_summary가 비어 있음"},
                    "audit_events": _append_event(state, {"node": "review", "decision": "reject"}),
                },
                goto="rejected",
            )
        draft["summary"] = edited_summary
    destination = "finalize" if decision in {"approve", "edit"} else "rejected"
    return Command(
        update={
            "draft": draft,
            "review": review,
            "status": "APPROVED" if destination == "finalize" else "REJECTED",
            "audit_events": _append_event(state, {"node": "review", "decision": decision}),
        },
        goto=destination,
    )


def finalize_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": "READY_FOR_EXPORT",
        "export_ready": True,
        "automatic_email": False,
        "audit_events": _append_event(
            state,
            {"node": "finalize", "side_effect": "local_json_only", "automatic_email": False},
        ),
    }


def rejected_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": "REJECTED",
        "export_ready": False,
        "automatic_email": False,
        "audit_events": _append_event(state, {"node": "rejected", "export_ready": False}),
    }


def failed_node(state: WorkflowState) -> dict[str, Any]:
    return {
        "status": "FAILED",
        "export_ready": False,
        "automatic_email": False,
        "audit_events": _append_event(state, {"node": "failed", "export_ready": False}),
    }


def build_graph():
    builder = StateGraph(WorkflowState)
    builder.add_node("validate", validate_node)
    builder.add_node("review", review_node, destinations=("finalize", "rejected"))
    builder.add_node("finalize", finalize_node)
    builder.add_node("rejected", rejected_node)
    builder.add_node("failed", failed_node)
    builder.add_edge(START, "validate")
    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {"review": "review", "failed": "failed"},
    )
    builder.add_edge("finalize", END)
    builder.add_edge("rejected", END)
    builder.add_edge("failed", END)
    return builder.compile(checkpointer=InMemorySaver())


def _interrupt_payload(first_result: dict[str, Any]) -> dict[str, Any] | None:
    pending = first_result.get("__interrupt__", ())
    if not pending:
        return None
    return pending[0].value


def run_langgraph_lab(
    draft: dict[str, Any],
    *,
    decision: Decision,
    request_id: str,
    edited_summary: str | None = None,
) -> dict[str, Any]:
    graph = build_graph()
    config = {"configurable": {"thread_id": request_id}}
    first = graph.invoke(
        {
            "request_id": request_id,
            "draft": draft,
            "validation_errors": [],
            "status": "CREATED",
            "review": {},
            "audit_events": [],
            "export_ready": False,
            "automatic_email": False,
        },
        config=config,
    )
    payload = _interrupt_payload(first)
    if payload is None:
        return {
            "status": first["status"],
            "framework": "LangGraph",
            "request_id": request_id,
            "interrupted": False,
            "interrupt_payload": None,
            "final_state": first,
        }

    human_input = {
        "decision": decision,
        "reviewer": "day1-learner",
        "reason": "실습에서 선택한 결정",
    }
    if edited_summary is not None:
        human_input["edited_summary"] = edited_summary
    final = graph.invoke(Command(resume=human_input), config=config)
    final.pop("__interrupt__", None)
    return {
        "status": final["status"],
        "framework": "LangGraph",
        "request_id": request_id,
        "thread_id_reused": True,
        "interrupted": True,
        "interrupt_payload": payload,
        "human_input": human_input,
        "final_state": final,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, default=Path("output/day1-langchain/langchain_result.json"))
    parser.add_argument("--out", type=Path, default=Path("output/day1-langgraph"))
    parser.add_argument("--decision", choices=["approve", "edit", "reject", "all"], default="all")
    args = parser.parse_args()

    chain_result = json.loads(args.draft.read_text(encoding="utf-8"))
    draft = chain_result["result"]
    decisions = ["approve", "edit", "reject"] if args.decision == "all" else [args.decision]
    args.out.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Any] = {}
    for value in decisions:
        edited = "배송 지연 안내만 자동화하고 반품 문의는 상담원이 검토한다." if value == "edit" else None
        result = run_langgraph_lab(
            draft,
            decision=value,  # type: ignore[arg-type]
            request_id=f"meeting-{value}-001",
            edited_summary=edited,
        )
        outputs[value] = result
        (args.out / f"langgraph_{value}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
