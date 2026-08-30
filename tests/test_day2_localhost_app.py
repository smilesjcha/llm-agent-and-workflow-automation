from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from scripts.day2_desktop_smoke import run_http_smoke
from scripts.run_day2_local_app import (
    DEFAULT_HOST,
    fetch_health,
    launch_server,
    port_is_available,
    runtime_environment,
    safe_report_path,
    server_command,
    stop_process,
    validate_port,
    resolve_port,
    wait_until_ready,
    write_launch_report,
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((DEFAULT_HOST, 0))
        return int(probe.getsockname()[1])


def test_localhost_launcher_uses_loopback_and_offline_safe_defaults() -> None:
    command = server_command(8766)
    environment = runtime_environment()

    assert command[command.index("--host") + 1] == "127.0.0.1"
    assert command[command.index("--port") + 1] == "8766"
    assert environment["APP_DELIVERY_MODE"] == "localhost"
    assert environment["APP_LOCAL_URL"] == "http://127.0.0.1:8766"
    assert environment["OLLAMA_BASE_URL"] == "http://127.0.0.1:11434"
    assert environment["HOST_BRIDGE_URL"] == "http://127.0.0.1:8765"
    assert environment["HOST_BRIDGE_TOKEN"] == "disabled"


def test_localhost_launcher_blocks_invalid_port_and_outside_report(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="DAY2_LOCAL_APP_PORT_INVALID"):
        validate_port(80)
    with pytest.raises(ValueError, match="DAY2_LOCAL_APP_REPORT_OUTSIDE_WORKSPACE"):
        safe_report_path(tmp_path / "outside.json")
    assert resolve_port(0) >= 1024

    port = _free_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((DEFAULT_HOST, port))
        assert port_is_available(port) is False


def test_localhost_server_runs_real_fixture_smoke() -> None:
    port = _free_port()
    process = launch_server(port, quiet=True)
    try:
        health = wait_until_ready(process, port)
        report = run_http_smoke(f"http://127.0.0.1:{port}")
    finally:
        stop_process(process)

    assert health["service"] == "meeting-intelligence"
    assert health["external_write"] is False
    assert fetch_health(port) is None
    assert report["status"] == "PASS"
    assert report["execution_mode"] == "LOOPBACK_HTTP"
    assert report["delivery_mode"] == "localhost"
    assert report["stage"] == "human_review"
    assert report["email_status"] == "DRAFT_ONLY"
    assert report["integration_plan_only"] is True
    assert all(report["checks"].values())


def test_launch_report_exposes_student_facing_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.run_day2_local_app as launcher

    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    report_path = write_launch_report(
        tmp_path / "08_localhost_launch.json",
        port=8766,
        health={"status": "ok", "service": "meeting-intelligence", "version": "2.1.0"},
        smoke={
            "service_version": "2.1.0",
            "stage": "human_review",
            "email_status": "DRAFT_ONLY",
            "integration_plan_only": True,
        },
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["service_version"] == "2.1.0"
    assert report["delivery_mode"] == "localhost"
    assert report["stage"] == "human_review"
    assert report["email_status"] == "DRAFT_ONLY"
    assert report["integration_plan_only"] is True
    assert report["external_write"] is False
