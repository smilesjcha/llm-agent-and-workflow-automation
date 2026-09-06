"""Optional LangGraph interrupt/resume wrapper for the Human Review lesson."""

from __future__ import annotations

from typing import Any, TypedDict

from .contracts import ReviewDraft
from .errors import stable_error_code
from .human_review import apply_human_review


class ReviewState(TypedDict, total=False):
    draft: dict[str, Any]
    status: str
    review: dict[str, Any]
    findings: list[dict[str, Any]]
    audit: list[dict[str, Any]]
    external_write: bool


def _validate_draft_payload(payload: object) -> ReviewDraft:
    """Accept the stage-05 test evidence wrapper, but reject other contract drift."""

    if not isinstance(payload, dict):
        raise ValueError("REVIEW_DRAFT_OBJECT_REQUIRED")
    normalized = dict(payload)
    normalized.pop("test_evidence", None)
    return ReviewDraft.model_validate(normalized)


def build_review_graph():
    """Compile a graph that always pauses before accepting review findings."""

    try:
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.graph import END, START, StateGraph
        from langgraph.types import Command, interrupt
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise RuntimeError("LANGGRAPH_NOT_INSTALLED") from exc

    def validate_node(state: ReviewState) -> dict[str, Any]:
        try:
            draft = _validate_draft_payload(state.get("draft", {}))
            valid = draft.status == "DRAFT"
            error_code = None
        except (TypeError, ValueError) as exc:
            draft = None
            valid = False
            error_code = stable_error_code(exc)
        return {
            "status": "REVIEW_REQUIRED" if valid else "BLOCKED",
            "findings": [item.to_dict() for item in draft.findings] if draft else [],
            "review": {} if valid else {"status": "BLOCKED", "error_code": error_code},
            "external_write": False,
            "audit": [{"node": "validate", "status": "PASS" if valid else "FAIL"}],
        }

    def route_after_validate(state: ReviewState) -> str:
        return "review" if state["status"] == "REVIEW_REQUIRED" else "blocked"

    def review_node(state: ReviewState):
        answer = interrupt(
            {
                "question": "finding을 유지·수정·제외하시겠습니까?",
                "options": ["approve", "edit", "reject"],
                "findings": state["findings"],
                "external_write": False,
            }
        )
        draft = _validate_draft_payload(state["draft"])
        if not isinstance(answer, dict):
            answer = {"decision": "__invalid_input__"}
        review = apply_human_review(
            draft,
            decision=answer.get("decision"),
            reviewer=answer.get("reviewer"),
            rationale=answer.get("rationale"),
            edited_findings=answer.get("edited_findings"),
        )
        destination = "finalize" if review.status in {"APPROVED", "EDITED"} else "blocked"
        return Command(
            update={
                "status": "HUMAN_REVIEWED" if destination == "finalize" else "REJECTED",
                "review": review.to_dict(),
                "findings": [item.to_dict() for item in review.findings],
                "external_write": False,
                "audit": [
                    *state.get("audit", []),
                    {"node": "review", "status": review.status, "decision": review.decision},
                ],
            },
            goto=destination,
        )

    def finalize_node(state: ReviewState) -> dict[str, Any]:
        return {
            "status": "DRY_RUN_READY",
            "external_write": False,
            "audit": [*state.get("audit", []), {"node": "finalize", "write": "none"}],
        }

    def blocked_node(state: ReviewState) -> dict[str, Any]:
        return {
            "status": "BLOCKED",
            "external_write": False,
            "audit": [*state.get("audit", []), {"node": "blocked", "write": "none"}],
        }

    builder = StateGraph(ReviewState)
    builder.add_node("validate", validate_node)
    builder.add_node("review", review_node, destinations=("finalize", "blocked"))
    builder.add_node("finalize", finalize_node)
    builder.add_node("blocked", blocked_node)
    builder.add_edge(START, "validate")
    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {"review": "review", "blocked": "blocked"},
    )
    builder.add_edge("finalize", END)
    builder.add_edge("blocked", END)
    return builder.compile(checkpointer=InMemorySaver())


def run_langgraph_human_review(
    draft: dict[str, Any],
    *,
    decision: str | None,
    reviewer: str | None = "수강생",
    rationale: str | None = "근거를 확인했습니다.",
    edited_findings: list[dict[str, Any]] | None = None,
    thread_id: str = "day3-review-001",
) -> dict[str, Any]:
    """Show the interrupt payload and the resumed state in one notebook cell."""

    try:
        from langgraph.types import Command
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("LANGGRAPH_NOT_INSTALLED") from exc

    graph = build_review_graph()
    config = {"configurable": {"thread_id": thread_id}}
    first = graph.invoke(
        {"draft": draft, "status": "CREATED", "audit": [], "external_write": False},
        config=config,
    )
    pending = first.get("__interrupt__", ())
    if not pending:
        return {
            "status": first["status"],
            "interrupted": False,
            "final_state": first,
            "external_write": False,
        }
    if decision is None:
        pending_state = dict(first)
        pending_state.pop("__interrupt__", None)
        return {
            "status": "REVIEW_REQUIRED",
            "framework": "LangGraph",
            "thread_id": thread_id,
            "interrupted": True,
            "interrupt_payload": pending[0].value,
            "human_input": None,
            "final_state": pending_state,
            "external_write": False,
        }
    human_input: dict[str, Any] = {
        "decision": decision,
        "reviewer": reviewer,
        "rationale": rationale,
    }
    if edited_findings is not None:
        human_input["edited_findings"] = edited_findings
    final = graph.invoke(Command(resume=human_input), config=config)
    final.pop("__interrupt__", None)
    return {
        "status": final["status"],
        "framework": "LangGraph",
        "thread_id": thread_id,
        "interrupted": True,
        "interrupt_payload": pending[0].value,
        "human_input": human_input,
        "final_state": final,
        "external_write": False,
    }
