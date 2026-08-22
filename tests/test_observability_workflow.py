from pathlib import Path

from src.langchain_lab import run_langchain_lab
from src.langgraph_lab import run_langgraph_lab
from src.observability_lab import LocalTraceRecorder, evaluate_workflow, langsmith_status
from src.workflow_service import run_workflow


ROOT = Path(__file__).resolve().parents[1]


def test_release_gate_is_ready_after_human_approval() -> None:
    chain = run_langchain_lab("합성 회의")
    graph = run_langgraph_lab(
        chain["result"],
        decision="approve",
        request_id="evaluation-approve",
    )
    evaluation = evaluate_workflow(chain, graph)
    assert evaluation["decision"] == "READY"
    assert evaluation["checks"]["automatic_email_blocked"] is True


def test_release_gate_holds_rejected_result() -> None:
    chain = run_langchain_lab("합성 회의")
    graph = run_langgraph_lab(
        chain["result"],
        decision="reject",
        request_id="evaluation-reject",
    )
    assert evaluate_workflow(chain, graph)["decision"] == "HOLD"


def test_local_trace_records_success_and_writes_json(tmp_path: Path) -> None:
    recorder = LocalTraceRecorder(run_name="test-run", metadata={"contains_pii": False})
    with recorder.span("node", inputs={"safe": True}) as span:
        span["output"] = "ok"
    path = recorder.write_json(tmp_path / "trace.json")
    assert path.exists()
    assert recorder.spans[0]["status"] == "SUCCESS"
    assert recorder.spans[0]["latency_ms"] >= 0


def test_langsmith_defaults_to_local_fallback(monkeypatch) -> None:
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    status = langsmith_status()
    assert status["enabled"] is False
    assert status["fallback"] == "local_json_trace"


def test_end_to_end_workflow_writes_bundle(tmp_path: Path) -> None:
    result = run_workflow(
        transcript_path=ROOT / "data/meeting_sample_ko_12min.txt",
        decision="approve",
        output_dir=tmp_path,
    )
    assert result["evaluation"]["decision"] == "READY"
    assert (tmp_path / "trace.json").exists()
    assert (tmp_path / "workflow_result.json").exists()
    assert result["langgraph"]["final_state"]["automatic_email"] is False

