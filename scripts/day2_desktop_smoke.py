"""Exercise the Day 2 desktop API with fixture data and save safe evidence.

The default mode uses FastAPI's in-process TestClient, so Docker and a network
connection are not required. ``--base-url`` can target an already running local
source/Docker app, but non-loopback URLs are rejected.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "desktop-app/meeting-intelligence"
DEFAULT_OUTPUT = ROOT / "output/course-labs/day2-v2/student-run/08_desktop_smoke.json"


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def safe_output_path(path: Path) -> Path:
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    if not _inside(ROOT.resolve(), resolved):
        raise ValueError("DAY2_DESKTOP_SMOKE_OUTPUT_OUTSIDE_WORKSPACE")
    return resolved


def _request_payload(client: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    fixtures = APP_ROOT / "fixtures"
    health_response = client.get("/health")
    process_response = client.post(
        "/api/process",
        files={
            "transcript_file": (
                "google_meet_sample_ko.txt",
                (fixtures / "google_meet_sample_ko.txt").read_bytes(),
                "text/plain",
            )
        },
        data={
            "source_mode": "google_meet",
            "participants": (fixtures / "participants_sample.json").read_text(encoding="utf-8"),
            "requested_outputs": "summary,participant_perspectives,todos,insights",
            "execution_mode": "auto",
            "provider": "fixture",
            "allow_fixture_fallback": "true",
        },
    )
    if health_response.status_code != 200:
        raise RuntimeError(f"DAY2_DESKTOP_HEALTH_FAILED:{health_response.status_code}")
    if process_response.status_code != 200:
        raise RuntimeError(f"DAY2_DESKTOP_PROCESS_FAILED:{process_response.status_code}")
    return health_response.json(), process_response.json()


def run_in_process_smoke() -> dict[str, Any]:
    sys.path.insert(0, str(APP_ROOT))
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            health, result = _request_payload(client)
    finally:
        if sys.path and sys.path[0] == str(APP_ROOT):
            sys.path.pop(0)
    return _build_report("FASTAPI_TESTCLIENT", health, result)


def _validate_loopback(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("DAY2_DESKTOP_SMOKE_NON_LOOPBACK_BLOCKED")
    return base_url.rstrip("/")


def run_http_smoke(base_url: str) -> dict[str, Any]:
    import httpx

    base_url = _validate_loopback(base_url)
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        health, result = _request_payload(client)
    return _build_report("LOOPBACK_HTTP", health, result)


def _build_report(mode: str, health: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    plan = result.get("integration_plan") or []
    checks = {
        "health_ok": health.get("status") == "ok",
        "pipeline_ready": result.get("status") == "READY",
        "fixture_provider_used": result.get("provider_used") == "fixture",
        "human_review_required": result.get("human_review_required") is True,
        "external_write_blocked": result.get("external_write") is False,
        "integration_plan_only": bool(plan)
        and all(item.get("status") == "PLAN_ONLY" and item.get("approval_required") is True for item in plan),
        "evidence_present": bool((result.get("meeting_record") or {}).get("summary", {}).get("evidence_ids")),
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "execution_mode": mode,
        "source_mode": result.get("source_mode"),
        "provider_requested": result.get("provider_requested"),
        "provider_used": result.get("provider_used"),
        "result_status": result.get("status"),
        "human_review_required": result.get("human_review_required"),
        "external_write": result.get("external_write"),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Optional running local app, for example http://127.0.0.1:8766")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = run_http_smoke(args.base_url) if args.base_url else run_in_process_smoke()
    output = safe_output_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
