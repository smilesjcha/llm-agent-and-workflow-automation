"""Start the Day 2 meeting-record UI on localhost without Docker.

The launcher binds only to 127.0.0.1, uses the current Python environment,
and defaults every external provider to an explicit offline-safe state. Use
``--smoke-and-exit`` to create deterministic evidence without leaving a server
running.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "desktop-app/meeting-intelligence"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766
DEFAULT_REPORT = ROOT / "output/course-labs/day2-v2/student-run/08_localhost_launch.json"
REQUIRED_MODULES = ("fastapi", "pydantic", "multipart", "uvicorn")


class LocalAppError(RuntimeError):
    """Stable launcher failure with a user-facing error code."""


def validate_port(port: int) -> int:
    if port < 1024 or port > 65535:
        raise ValueError("DAY2_LOCAL_APP_PORT_INVALID")
    return port


def resolve_port(port: int) -> int:
    if port != 0:
        return validate_port(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((DEFAULT_HOST, 0))
        return int(probe.getsockname()[1])


def missing_modules() -> list[str]:
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


def runtime_environment(port: int = DEFAULT_PORT) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "APP_DELIVERY_MODE": "localhost",
            "APP_LOCAL_URL": app_url(port),
            "OLLAMA_BASE_URL": environment.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            "HOST_BRIDGE_URL": "http://127.0.0.1:8765",
            "HOST_BRIDGE_TOKEN": "disabled",
        }
    )
    return environment


def server_command(port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        str(APP_ROOT),
        "--host",
        DEFAULT_HOST,
        "--port",
        str(validate_port(port)),
        "--no-access-log",
    ]


def health_url(port: int) -> str:
    return f"http://{DEFAULT_HOST}:{validate_port(port)}/health"


def app_url(port: int) -> str:
    return f"http://{DEFAULT_HOST}:{validate_port(port)}"


def fetch_health(port: int, *, timeout: float = 1.0) -> dict[str, Any] | None:
    try:
        with urlopen(health_url(port), timeout=timeout) as response:  # noqa: S310 - fixed loopback URL
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return None
    if payload.get("service") != "meeting-intelligence":
        return None
    return payload


def port_is_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((DEFAULT_HOST, validate_port(port)))
        except OSError:
            return False
    return True


def wait_until_ready(process: subprocess.Popen[Any], port: int, *, timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise LocalAppError(f"DAY2_LOCAL_APP_EXITED:{process.returncode}")
        health = fetch_health(port)
        if health is not None:
            return health
        time.sleep(0.2)
    raise LocalAppError("DAY2_LOCAL_APP_START_TIMEOUT")


def stop_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def launch_server(port: int, *, quiet: bool = False) -> subprocess.Popen[Any]:
    output = subprocess.DEVNULL if quiet else None
    return subprocess.Popen(
        server_command(port),
        cwd=ROOT,
        env=runtime_environment(port),
        stdout=output,
        stderr=output,
    )


def safe_report_path(path: Path) -> Path:
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    root = ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("DAY2_LOCAL_APP_REPORT_OUTSIDE_WORKSPACE")
    return resolved


def write_launch_report(path: Path, *, port: int, health: dict[str, Any], smoke: dict[str, Any] | None) -> Path:
    destination = safe_report_path(path)
    smoke = smoke or {}
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "PASS",
        "service_version": smoke.get("service_version") or health.get("version"),
        "delivery_mode": "localhost",
        "url": app_url(port),
        "health": health,
        "smoke": smoke,
        "stage": smoke.get("stage"),
        "email_status": smoke.get("email_status"),
        "integration_plan_only": smoke.get("integration_plan_only"),
        "network_required": False,
        "external_write": False,
        "human_review_required": True,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--smoke-and-exit", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    port = resolve_port(args.port)

    missing = missing_modules()
    if missing:
        print(json.dumps({"status": "HOLD", "error_code": "DAY2_LOCAL_APP_DEPENDENCY_MISSING", "modules": missing}, ensure_ascii=False))
        print(f"설치: {sys.executable} -m pip install -r desktop-app/meeting-intelligence/requirements-localhost.txt")
        return 2

    existing = fetch_health(port)
    if existing is not None:
        if args.smoke_and_exit:
            from day2_desktop_smoke import run_http_smoke

            smoke = run_http_smoke(app_url(port))
            if smoke.get("status") != "PASS":
                print(json.dumps({"status": "HOLD", "error_code": "DAY2_LOCAL_APP_SMOKE_FAILED"}, ensure_ascii=False))
                return 4
            report = write_launch_report(args.report, port=port, health=existing, smoke=smoke)
            print(json.dumps({"status": "PASS", "url": app_url(port), "reason": "ALREADY_RUNNING", "report": str(report)}, ensure_ascii=False))
            return 0
        print(json.dumps({"status": "READY", "url": app_url(port), "reason": "ALREADY_RUNNING"}, ensure_ascii=False))
        if not args.no_browser and not args.smoke_and_exit:
            webbrowser.open(app_url(port))
        return 0
    if not port_is_available(port):
        print(json.dumps({"status": "HOLD", "error_code": "DAY2_LOCAL_APP_PORT_IN_USE", "port": port}, ensure_ascii=False))
        return 3

    process = launch_server(port, quiet=args.smoke_and_exit)
    try:
        health = wait_until_ready(process, port)
        smoke = None
        if args.smoke_and_exit:
            from day2_desktop_smoke import run_http_smoke

            smoke = run_http_smoke(app_url(port))
            if smoke.get("status") != "PASS":
                raise LocalAppError("DAY2_LOCAL_APP_SMOKE_FAILED")
        report = write_launch_report(args.report, port=port, health=health, smoke=smoke)
        print(json.dumps({"status": "PASS", "url": app_url(port), "report": str(report)}, ensure_ascii=False))
        if args.smoke_and_exit:
            return 0
        if not args.no_browser:
            webbrowser.open(app_url(port))
        print("종료하려면 이 Terminal에서 Ctrl+C를 누르세요.")
        return process.wait()
    except KeyboardInterrupt:
        return 0
    except LocalAppError as exc:
        print(json.dumps({"status": "HOLD", "error_code": str(exc)}, ensure_ascii=False))
        return 4
    finally:
        stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
