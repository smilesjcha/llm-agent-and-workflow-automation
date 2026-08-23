"""Local-first observability and evaluation for the Day 1 workflow.

The JSON trace is the classroom default because it works without an account or
network. The same metadata can optionally be uploaded to LangSmith after the
learner explicitly enables tracing with environment variables.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4


LANGSMITH_SAFE_CLASSIFICATIONS = frozenset({"synthetic", "deidentified"})


def disable_automatic_langsmith_tracing() -> bool:
    """Prevent raw LangChain inputs from bypassing the redacted upload boundary."""

    was_enabled = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
    os.environ["LANGSMITH_TRACING"] = "false"
    return was_enabled


class LocalTraceRecorder:
    """Record named spans without sending meeting contents to an external service."""

    def __init__(self, *, run_name: str, metadata: dict[str, Any]) -> None:
        self.run_name = run_name
        self.metadata = metadata
        self.started_at = datetime.now(UTC)
        self.spans: list[dict[str, Any]] = []

    @contextmanager
    def span(self, name: str, *, inputs: dict[str, Any]) -> Iterator[dict[str, Any]]:
        started = perf_counter()
        record: dict[str, Any] = {
            "name": name,
            "status": "RUNNING",
            "input_keys": sorted(inputs),
        }
        try:
            yield record
        except Exception as exc:
            record.update(
                {
                    "status": "ERROR",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            raise
        else:
            record["status"] = "SUCCESS"
        finally:
            record["latency_ms"] = round((perf_counter() - started) * 1000, 2)
            self.spans.append(record)

    def to_dict(self) -> dict[str, Any]:
        finished_at = datetime.now(UTC)
        return {
            "run_name": self.run_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "metadata": self.metadata,
            "spans": self.spans,
        }

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


def evaluate_workflow(chain_result: dict[str, Any], graph_result: dict[str, Any]) -> dict[str, Any]:
    """Apply deterministic release checks before any external publication."""

    result = chain_result.get("result", {})
    action_items = result.get("action_items", [])
    evidence_linked = sum(bool(item.get("evidence_ids")) for item in action_items)
    evidence_rate = evidence_linked / max(1, len(action_items))
    final_state = graph_result.get("final_state", {})
    checks = {
        "schema_valid": bool(chain_result.get("checks", {}).get("schema_valid")),
        "evidence_rate_at_least_0_90": evidence_rate >= 0.90,
        "human_decision_recorded": bool(final_state.get("review", {}).get("decision")),
        "automatic_email_blocked": final_state.get("automatic_email") is False,
        "approved_for_local_export": final_state.get("status") == "READY_FOR_EXPORT",
    }
    return {
        "decision": "READY" if all(checks.values()) else "HOLD",
        "checks": checks,
        "metrics": {
            "evidence_rate": round(evidence_rate, 3),
            "action_item_count": len(action_items),
        },
    }


def langsmith_status() -> dict[str, Any]:
    """Report LangSmith configuration without printing the API key."""

    auto_tracing_enabled = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
    has_key = bool(os.getenv("LANGSMITH_API_KEY", "").strip())
    return {
        "enabled": auto_tracing_enabled and has_key,
        "auto_tracing_enabled": auto_tracing_enabled,
        "manual_upload_ready": has_key,
        "project": os.getenv("LANGSMITH_PROJECT", "ipa-day1-software-lab"),
        "api_key_present": has_key,
        "fallback": "local_json_trace" if not (auto_tracing_enabled and has_key) else None,
    }


def upload_summary_to_langsmith(
    *,
    trace: dict[str, Any],
    evaluation: dict[str, Any],
    client: Any | None = None,
) -> dict[str, Any]:
    """Upload one redacted run summary after an explicit caller opt-in.

    Transcript text, model output, file paths, and secrets are intentionally
    excluded. The default classroom command never calls this function.
    """

    status = langsmith_status()
    if not status["api_key_present"]:
        return {
            "requested": True,
            "uploaded": False,
            "error_code": "LANGSMITH_API_KEY_MISSING",
            **status,
        }

    metadata = trace.get("metadata", {})
    classification = metadata.get("data_classification", "local_only")
    if classification not in LANGSMITH_SAFE_CLASSIFICATIONS:
        return {
            "requested": True,
            "uploaded": False,
            "error_code": "LANGSMITH_DATA_CLASSIFICATION_BLOCKED",
            "allowed_classifications": sorted(LANGSMITH_SAFE_CLASSIFICATIONS),
            **status,
        }

    run_id = uuid4()
    request_id_hash = sha256(
        str(metadata.get("request_id", "missing-request-id")).encode("utf-8")
    ).hexdigest()[:16]
    safe_spans = [
        {
            "name": span.get("name"),
            "status": span.get("status"),
            "latency_ms": span.get("latency_ms"),
        }
        for span in trace.get("spans", [])
    ]
    try:
        if client is None:
            from langsmith import Client

            client = Client(
                api_key=os.environ["LANGSMITH_API_KEY"],
                api_url=os.getenv("LANGSMITH_ENDPOINT") or None,
                workspace_id=os.getenv("LANGSMITH_WORKSPACE_ID") or None,
            )

        client.create_run(
            name=trace.get("run_name", "meeting-agent-workflow"),
            run_type="chain",
            inputs={
                "request_id_hash": request_id_hash,
                "data_classification": classification,
                "contains_pii": False,
            },
            outputs={
                "release_decision": evaluation.get("decision"),
                "checks": evaluation.get("checks", {}),
                "metrics": evaluation.get("metrics", {}),
                "spans": safe_spans,
            },
            project_name=status["project"],
            id=run_id,
            start_time=datetime.fromisoformat(trace["started_at"]),
            end_time=datetime.fromisoformat(trace["finished_at"]),
            tags=["day1", "redacted-summary", classification],
            extra={
                "metadata": {
                    "human_upload_approval": True,
                    "transcript_uploaded": False,
                    "external_action_executed": False,
                }
            },
        )
        for span in safe_spans:
            child_timestamp = datetime.now(UTC)
            client.create_run(
                name=span["name"] or "unnamed-workflow-step",
                run_type="chain",
                inputs={"redacted": True},
                outputs={
                    "status": span["status"],
                    "latency_ms": span["latency_ms"],
                },
                project_name=status["project"],
                id=uuid4(),
                parent_run_id=run_id,
                trace_id=run_id,
                start_time=child_timestamp,
                end_time=child_timestamp,
                tags=["redacted-step", classification],
            )
        client.flush()
    except Exception as exc:
        return {
            "requested": True,
            "uploaded": False,
            "error_code": "LANGSMITH_UPLOAD_FAILED",
            "error_type": type(exc).__name__,
            "project": status["project"],
        }

    return {
        "requested": True,
        "uploaded": True,
        "error_code": None,
        "project": status["project"],
        "run_id": str(run_id),
        "web_url": "https://smith.langchain.com",
        "transcript_uploaded": False,
    }
