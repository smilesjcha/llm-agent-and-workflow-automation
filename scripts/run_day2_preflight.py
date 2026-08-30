"""Run the required offline Day 2 checks and write one instructor report.

The default path is deterministic and does not call a paid model, download a
model, open an MCP connector, upload a trace, or write to an external service.
Reference outputs are checked for safety invariants; learner executions belong
under ``output/course-labs/day2-v2/student-run``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_OUTPUT_DIR = ROOT / "output/course-labs/day2-v2"
REFERENCE_RESULTS = (
    "01_architecture.json",
    "02_inputs.json",
    "03_domain_context.json",
    "04_meeting_record_contract.json",
    "05_workflow_runs.json",
    "06_provider_diagnostics.json",
    "07_human_review.json",
    "08_export_drafts.json",
)
REQUIRED_FILES = (
    "slides/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pptx",
    "output/pdf/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pdf",
    "materials/day2/2026_Day2_수강생_실습가이드.md",
    "materials/day2/day2_service_lab.ipynb",
    "materials/day2/day2_service_lab.executed.ipynb",
    "src/course_services/day2_meeting_workflow.py",
    "desktop-app/meeting-intelligence/README.md",
    "desktop-app/meeting-intelligence/requirements-localhost.txt",
    "desktop-app/meeting-intelligence/scripts/run-local.command",
    "desktop-app/meeting-intelligence/scripts/run-local.cmd",
    "scripts/run_day2_local_app.py",
)
BLOCKED_TRUE_KEYS = frozenset({"external_write", "automatic_email", "send"})


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: list[str]
    status: str
    return_code: int | None
    stdout_tail: str
    stderr_tail: str


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _tail(value: str, *, max_chars: int = 1800) -> str:
    return value[-max_chars:]


def safe_output_dir(root: Path, requested: Path) -> Path:
    root = root.resolve()
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    if not _inside(root, resolved):
        raise ValueError("DAY2_PREFLIGHT_OUTPUT_OUTSIDE_WORKSPACE")
    return resolved


def run_check(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path = ROOT,
    timeout_seconds: int = 300,
) -> CheckResult:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CheckResult(
            name=name,
            command=list(command),
            status="PASS" if completed.returncode == 0 else "FAIL",
            return_code=completed.returncode,
            stdout_tail=_tail(completed.stdout),
            stderr_tail=_tail(completed.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            name=name,
            command=list(command),
            status="TIMEOUT",
            return_code=None,
            stdout_tail=_tail(exc.stdout or ""),
            stderr_tail=_tail(exc.stderr or ""),
        )
    except FileNotFoundError:
        return CheckResult(
            name=name,
            command=list(command),
            status="MISSING_DEPENDENCY",
            return_code=None,
            stdout_tail="",
            stderr_tail=f"{command[0]} was not found",
        )


def required_checks(
    *,
    include_full_suite: bool = False,
    include_package_suite: bool = False,
) -> list[tuple[str, list[str], Path]]:
    python = sys.executable
    checks = [
        (
            "day2_focused_tests",
            [
                python,
                "-m",
                "pytest",
                "-q",
                "tests/test_day2_meeting_workflow.py",
                "tests/test_day2_notebook.py",
            ],
            ROOT,
        ),
        (
            "public_audio_offline_verification",
            [python, "scripts/day2_public_audio_verify.py"],
            ROOT,
        ),
        (
            "desktop_python_tests",
            [python, "-m", "pytest", "-q", "tests"],
            ROOT / "desktop-app/meeting-intelligence",
        ),
        (
            "desktop_source_smoke",
            [
                python,
                "scripts/day2_desktop_smoke.py",
                "--output",
                "output/day2-preflight/desktop_smoke.json",
            ],
            ROOT,
        ),
        (
            "desktop_loopback_http_smoke",
            [
                python,
                "scripts/run_day2_local_app.py",
                "--smoke-and-exit",
                "--port",
                "0",
                "--report",
                "output/day2-preflight/localhost_smoke.json",
            ],
            ROOT,
        ),
    ]
    if include_full_suite:
        checks.append(("full_repository_tests", [python, "-m", "pytest", "-q"], ROOT))
    if include_package_suite:
        checks.append(("desktop_go_launcher_tests", [shutil.which("go") or "go", "test", "./..."], ROOT / "desktop-app/meeting-intelligence"))
    return checks


def _walk_values(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    found: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            found.append((child_path, key, child))
            found.extend(_walk_values(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_values(child, f"{path}[{index}]"))
    return found


def _is_schema_path(path: str) -> bool:
    return any(marker in path for marker in (".schema.", ".$defs.", ".definitions."))


def validate_reference_outputs(directory: Path = REFERENCE_OUTPUT_DIR) -> dict[str, Any]:
    directory = directory.resolve()
    missing: list[str] = []
    invalid_json: list[str] = []
    policy_violations: list[str] = []
    human_review_markers = 0
    for name in REFERENCE_RESULTS:
        path = directory / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            invalid_json.append(name)
            continue
        for json_path, key, value in _walk_values(payload):
            if key in BLOCKED_TRUE_KEYS and value is not False and not _is_schema_path(json_path):
                policy_violations.append(f"{name}:{json_path}={value!r}")
            if key == "human_review_required" and value is True:
                human_review_markers += 1
    status = "PASS" if not (missing or invalid_json or policy_violations) and human_review_markers else "FAIL"
    return {
        "status": status,
        "role": "CHECKED_IN_REFERENCE_EXAMPLES",
        "directory": str(directory),
        "missing": missing,
        "invalid_json": invalid_json,
        "policy_violations": policy_violations,
        "human_review_markers": human_review_markers,
    }


def validate_required_files(root: Path = ROOT) -> dict[str, Any]:
    missing = [item for item in REQUIRED_FILES if not (root / item).is_file()]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def validate_package_checksums(
    directory: Path = ROOT / "desktop-app/meeting-intelligence/dist",
) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS"
    if not manifest.is_file():
        return {"status": "NOT_BUILT", "checked": [], "errors": ["SHA256SUMS_MISSING"]}
    checked: list[str] = []
    errors: list[str] = []
    release_status: dict[str, Any] | None = None
    release_path = directory / "RELEASE_STATUS.json"
    if not release_path.is_file():
        errors.append("RELEASE_STATUS_MISSING")
    else:
        try:
            release_status = json.loads(release_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append("RELEASE_STATUS_INVALID")
        else:
            if release_status.get("version") != "2.1.0":
                errors.append("RELEASE_VERSION_MISMATCH")
            if release_status.get("default_delivery") != "localhost":
                errors.append("RELEASE_DEFAULT_DELIVERY_INVALID")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            errors.append("SHA256SUMS_INVALID")
            continue
        expected, filename = parts
        path = directory / filename.strip()
        if not path.is_file():
            errors.append(f"PACKAGE_MISSING:{filename.strip()}")
            continue
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected:
            errors.append(f"PACKAGE_CHECKSUM_MISMATCH:{filename.strip()}")
            continue
        checked.append(filename.strip())
    return {
        "status": "PASS" if checked and not errors else "FAIL",
        "checked": checked,
        "errors": errors,
        "release": release_status,
    }


def optional_environment() -> dict[str, Any]:
    tools = {name: shutil.which(name) for name in ("docker", "ollama", "codex", "claude", "go", "node")}
    ollama_models: list[str] = []
    if tools["ollama"]:
        check = run_check("ollama_list", [tools["ollama"], "list"], timeout_seconds=20)
        if check.status == "PASS":
            ollama_models = [line.split()[0] for line in check.stdout_tail.splitlines()[1:] if line.strip()]
    return {
        "tools": {name: {"available": bool(path), "path": path} for name, path in tools.items()},
        "ollama_models": ollama_models,
        "qwen3_4b_ready": "qwen3:4b" in ollama_models,
        "live_provider_executed": False,
        "mcp_connector_executed": False,
        "langsmith_upload_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("output/day2-preflight"))
    parser.add_argument("--full-suite", action="store_true")
    parser.add_argument("--require-packages", action="store_true")
    args = parser.parse_args(argv)

    output_dir = safe_output_dir(ROOT, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checks = [
        run_check(name, command, cwd=cwd)
        for name, command, cwd in required_checks(
            include_full_suite=args.full_suite,
            include_package_suite=args.require_packages,
        )
    ]
    files = validate_required_files()
    references = validate_reference_outputs()
    packages = validate_package_checksums()
    required_ok = all(check.status == "PASS" for check in checks)
    package_ok = packages["status"] == "PASS" if args.require_packages else True
    status = "PASS" if required_ok and files["status"] == "PASS" and references["status"] == "PASS" and package_ok else "FAIL"
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "python": sys.executable,
        "network_required": False,
        "paid_llm_required": False,
        "external_write": False,
        "checks": [asdict(check) for check in checks],
        "required_files": files,
        "reference_outputs": references,
        "packages": packages,
        "delivery": {
            "primary": "localhost",
            "start_command": "python scripts/run_day2_local_app.py",
            "smoke_command": "python scripts/run_day2_local_app.py --smoke-and-exit --port 0",
            "package_role": "OPTIONAL_UNSIGNED_EDUCATION_BUILD",
            "package_requires_docker": True,
            "package_required_for_this_run": args.require_packages,
        },
        "optional_environment": optional_environment(),
        "learner_output_directory": "output/course-labs/day2-v2/student-run",
    }
    report_path = output_dir / "preflight_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_path)}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
