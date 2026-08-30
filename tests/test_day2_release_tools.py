from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.build_day2_student_bundle import BUNDLE_ROOT, build_bundle, student_files
from scripts.day2_desktop_smoke import run_in_process_smoke, safe_output_path
from scripts.run_day2_preflight import (
    REFERENCE_RESULTS,
    required_checks,
    safe_output_dir,
    validate_package_checksums,
    validate_reference_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


def test_day2_preflight_is_offline_and_reference_outputs_are_safe() -> None:
    commands = [part for _, command, _ in required_checks() for part in command]
    assert "openai" not in commands
    assert "langsmith" not in commands
    assert "docker" not in commands
    result = validate_reference_outputs()
    assert result["status"] == "PASS"
    assert result["role"] == "CHECKED_IN_REFERENCE_EXAMPLES"
    assert result["human_review_markers"] > 0
    assert validate_package_checksums()["status"] == "PASS"


def test_day2_preflight_blocks_unsafe_reference_and_outside_output(tmp_path: Path) -> None:
    lab = tmp_path / "reference"
    lab.mkdir()
    for name in REFERENCE_RESULTS:
        payload = {"human_review_required": True, "external_write": False, "send": False}
        (lab / name).write_text(json.dumps(payload), encoding="utf-8")
    assert validate_reference_outputs(lab)["status"] == "PASS"
    (lab / REFERENCE_RESULTS[-1]).write_text(
        json.dumps({"human_review_required": True, "external_write": False, "send": True}),
        encoding="utf-8",
    )
    unsafe = validate_reference_outputs(lab)
    assert unsafe["status"] == "FAIL"
    assert "send=True" in unsafe["policy_violations"][0]
    with pytest.raises(ValueError, match="DAY2_PREFLIGHT_OUTPUT_OUTSIDE_WORKSPACE"):
        safe_output_dir(ROOT, tmp_path / "outside")


def test_day2_bundle_manifest_is_reviewed_and_secret_free(tmp_path: Path) -> None:
    relative = {path.relative_to(ROOT).as_posix() for path in student_files()}
    assert "materials/day2/day2_service_lab.ipynb" in relative
    assert "data/day2_public_audio/meeting_ko_ccby_excerpt_10m.mp3" in relative
    assert "desktop-app/meeting-intelligence/dist/MeetingIntelligence-Windows.exe" in relative
    assert not any("/.venv/" in f"/{item}/" or item.endswith("/.env") for item in relative)

    root = tmp_path / "workspace"
    root.mkdir()
    sample = root / "README.md"
    sample.write_text("day2 bundle", encoding="utf-8")
    destination = root / "release/day2.zip"
    result = build_bundle(root, destination, files=[sample])
    assert result["status"] == "SUCCESS"
    with zipfile.ZipFile(destination) as archive:
        names = archive.namelist()
        assert f"{BUNDLE_ROOT}/README.md" in names
        manifest = json.loads(archive.read(f"{BUNDLE_ROOT}/BUNDLE_MANIFEST.json"))
    assert manifest["contains_secret_files"] is False
    assert manifest["file_count"] == 1

    secret = root / ".env.local"
    secret.write_text("do-not-ship", encoding="utf-8")
    with pytest.raises(ValueError, match="DAY2_BUNDLE_PATH_BLOCKED"):
        build_bundle(root, destination, files=[secret])
    with pytest.raises(ValueError, match="DAY2_BUNDLE_DESTINATION_OUTSIDE_WORKSPACE"):
        build_bundle(root, tmp_path / "outside.zip", files=[sample])


def test_day2_desktop_source_smoke_preserves_review_boundary(tmp_path: Path) -> None:
    report = run_in_process_smoke()
    assert report["status"] == "PASS"
    assert report["execution_mode"] == "FASTAPI_TESTCLIENT"
    assert report["human_review_required"] is True
    assert report["external_write"] is False
    assert all(report["checks"].values())
    with pytest.raises(ValueError, match="DAY2_DESKTOP_SMOKE_OUTPUT_OUTSIDE_WORKSPACE"):
        safe_output_path(tmp_path / "outside.json")
