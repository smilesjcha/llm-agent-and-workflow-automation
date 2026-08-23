from pathlib import Path

from src.langchain_lab import run_langchain_lab
from src.langgraph_lab import run_langgraph_lab
from src.observability_lab import (
    LocalTraceRecorder,
    evaluate_workflow,
    langsmith_status,
    upload_summary_to_langsmith,
)
from src.workflow_service import run_workflow


ROOT = Path(__file__).resolve().parents[1]


class FakeLangSmithClient:
    def __init__(self) -> None:
        self.created_runs: list[dict] = []
        self.flushed = False

    def create_run(self, name, inputs, run_type, **kwargs) -> None:
        self.created_runs.append(
            {"name": name, "inputs": inputs, "run_type": run_type, **kwargs}
        )

    def flush(self) -> None:
        self.flushed = True


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


def test_workflow_disables_raw_automatic_langsmith_tracing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    result = run_workflow(
        transcript_path=ROOT / "data/meeting_sample_ko_12min.txt",
        decision="approve",
        output_dir=tmp_path,
    )
    assert result["langsmith"]["auto_tracing_enabled"] is False


def test_langsmith_upload_blocks_unclassified_data(monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    recorder = LocalTraceRecorder(
        run_name="blocked-run",
        metadata={"request_id": "blocked", "data_classification": "local_only"},
    )
    result = upload_summary_to_langsmith(
        trace=recorder.to_dict(),
        evaluation={"decision": "HOLD"},
        client=FakeLangSmithClient(),
    )
    assert result["uploaded"] is False
    assert result["error_code"] == "LANGSMITH_DATA_CLASSIFICATION_BLOCKED"


def test_langsmith_upload_builds_client_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("LANGSMITH_WORKSPACE_ID", "test-workspace")
    created_with: dict = {}
    fake_client = FakeLangSmithClient()

    def client_factory(**kwargs):
        created_with.update(kwargs)
        return fake_client

    monkeypatch.setattr("langsmith.Client", client_factory)
    recorder = LocalTraceRecorder(
        run_name="environment-client-run",
        metadata={"request_id": "safe-id", "data_classification": "synthetic"},
    )
    result = upload_summary_to_langsmith(
        trace=recorder.to_dict(),
        evaluation={"decision": "READY", "checks": {}, "metrics": {}},
    )
    assert result["uploaded"] is True
    assert created_with == {
        "api_key": "test-key",
        "api_url": "https://example.invalid",
        "workspace_id": "test-workspace",
    }


def test_end_to_end_workflow_uploads_only_redacted_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "test-day1")
    client = FakeLangSmithClient()
    result = run_workflow(
        transcript_path=ROOT / "data/meeting_sample_ko_12min.txt",
        decision="approve",
        output_dir=tmp_path,
        upload_langsmith=True,
        data_classification="synthetic",
        langsmith_client=client,
    )
    assert result["langsmith"]["uploaded"] is True
    assert client.flushed is True
    uploaded_payload = client.created_runs[0]
    assert uploaded_payload["inputs"]["data_classification"] == "synthetic"
    assert set(uploaded_payload["inputs"]) == {
        "request_id_hash",
        "data_classification",
        "contains_pii",
    }
    assert len(uploaded_payload["inputs"]["request_id_hash"]) == 16
    assert uploaded_payload["outputs"]["release_decision"] == "READY"
    assert len(client.created_runs) == 4
    assert all("transcript" not in str(run["inputs"]).lower() for run in client.created_runs)
