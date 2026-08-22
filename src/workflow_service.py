"""End-to-end meeting workflow assembled from the Day 1 software labs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.langchain_lab import run_langchain_lab
from src.langgraph_lab import Decision, run_langgraph_lab
from src.observability_lab import LocalTraceRecorder, evaluate_workflow, langsmith_status


def run_workflow(
    *,
    transcript_path: Path,
    decision: Decision,
    output_dir: Path,
    edited_summary: str | None = None,
) -> dict[str, Any]:
    """Run LCEL, pause/resume LangGraph, evaluate, and persist an audit bundle."""

    transcript = transcript_path.read_text(encoding="utf-8")
    request_id = f"{transcript_path.stem}-{decision}"
    trace = LocalTraceRecorder(
        run_name="meeting-agent-workflow",
        metadata={
            "request_id": request_id,
            "dataset": transcript_path.name,
            "contains_pii": False,
            "external_write": False,
        },
    )

    with trace.span("langchain_lcel", inputs={"transcript_path": str(transcript_path)}) as span:
        chain_result = run_langchain_lab(transcript)
        span["provider"] = chain_result["provider_used"]
        span["pipeline"] = chain_result["pipeline"]

    with trace.span("langgraph_interrupt_resume", inputs={"decision": decision}) as span:
        graph_result = run_langgraph_lab(
            chain_result["result"],
            decision=decision,
            request_id=request_id,
            edited_summary=edited_summary,
        )
        span["interrupted"] = graph_result["interrupted"]
        span["final_status"] = graph_result["final_state"]["status"]

    with trace.span("release_gate", inputs={"request_id": request_id}) as span:
        evaluation = evaluate_workflow(chain_result, graph_result)
        span["decision"] = evaluation["decision"]

    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace.write_json(output_dir / "trace.json")
    result = {
        "status": "SUCCESS",
        "request_id": request_id,
        "langchain": chain_result,
        "langgraph": graph_result,
        "evaluation": evaluation,
        "langsmith": langsmith_status(),
        "outputs": {
            "trace": str(trace_path),
            "bundle": str(output_dir / "workflow_result.json"),
        },
    }
    (output_dir / "workflow_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transcript",
        type=Path,
        default=Path("data/meeting_sample_ko_12min.txt"),
    )
    parser.add_argument("--decision", choices=["approve", "edit", "reject"], default="approve")
    parser.add_argument("--edited-summary")
    parser.add_argument("--out", type=Path, default=Path("output/day1-workflow"))
    args = parser.parse_args()
    result = run_workflow(
        transcript_path=args.transcript,
        decision=args.decision,
        output_dir=args.out,
        edited_summary=args.edited_summary,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "request_id": result["request_id"],
                "graph_status": result["langgraph"]["final_state"]["status"],
                "release_gate": result["evaluation"]["decision"],
                "langsmith": result["langsmith"],
                "outputs": result["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

