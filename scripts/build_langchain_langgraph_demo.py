"""Build reproducible LangChain, LangGraph, and web-demo output fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.langchain_lab import run_langchain_lab
from src.langgraph_lab import run_langgraph_lab
from src.observability_lab import evaluate_workflow


def main() -> None:
    transcript_path = ROOT / "data/meeting_sample_ko_12min.txt"
    transcript = transcript_path.read_text(encoding="utf-8")
    chain_result = run_langchain_lab(transcript)

    chain_out = ROOT / "output/day1-langchain/langchain_result.json"
    chain_out.parent.mkdir(parents=True, exist_ok=True)
    chain_out.write_text(json.dumps(chain_result, ensure_ascii=False, indent=2), encoding="utf-8")

    scenarios = {}
    graph_out = ROOT / "output/day1-langgraph"
    graph_out.mkdir(parents=True, exist_ok=True)
    for decision in ("approve", "edit", "reject"):
        result = run_langgraph_lab(
            chain_result["result"],
            decision=decision,
            request_id=f"meeting-{decision}-001",
            edited_summary=(
                "배송 지연 안내만 자동화하고 반품 문의는 상담원이 검토한다."
                if decision == "edit"
                else None
            ),
        )
        result["evaluation"] = evaluate_workflow(chain_result, result)
        scenarios[decision] = result
        (graph_out / f"langgraph_{decision}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    web_payload = {
        "generated_from": "LangChain LCEL + LangGraph interrupt/resume",
        "transcript": str(transcript_path.relative_to(ROOT)),
        "langchain": chain_result,
        "scenarios": scenarios,
    }
    web_out = ROOT / "web-demo/public/demo-data.json"
    web_out.parent.mkdir(parents=True, exist_ok=True)
    web_out.write_text(json.dumps(web_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "SUCCESS",
                "langchain": str(chain_out.relative_to(ROOT)),
                "langgraph": [str((graph_out / f"langgraph_{d}.json").relative_to(ROOT)) for d in scenarios],
                "web": str(web_out.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
