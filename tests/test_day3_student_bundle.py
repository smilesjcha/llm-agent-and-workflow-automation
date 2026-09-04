"""Safety and reproducibility checks for the Day 3 student code bundle."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.build_day3_student_bundle import BUNDLE_ROOT, build_bundle, student_files


ROOT = Path(__file__).resolve().parents[1]


def test_day3_bundle_allowlist_contains_only_student_code_assets() -> None:
    relative = {path.relative_to(ROOT).as_posix() for path in student_files()}

    assert "materials/day3/day3_review_intelligence_lab.ipynb" in relative
    assert "labs/day3/review_copilot/web_app.py" in relative
    assert "labs/day3/review_copilot/day3.env.example" in relative
    assert ".github/workflows/day3-pr-quality.yml" in relative
    assert "tests/test_day3_review_copilot.py" in relative
    assert "materials/day3/day3_review_intelligence_lab.executed.ipynb" not in relative
    assert "materials/day3/2026_Day3_강사용_상세교안.md" not in relative
    assert not any("student-run" in item or item.startswith("output/") for item in relative)
    assert not any(part.startswith(".env") for item in relative for part in Path(item).parts)


def test_day3_bundle_is_deterministic_and_has_safe_manifest(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "lesson.py"
    source.write_text("print('day3')\n", encoding="utf-8")

    first = root / "dist/first.zip"
    second = root / "dist/second.zip"
    first_result = build_bundle(root, first, files=[source])
    second_result = build_bundle(root, second, files=[source])

    assert first_result["sha256"] == second_result["sha256"]
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert names == [
            f"{BUNDLE_ROOT}/lesson.py",
            f"{BUNDLE_ROOT}/BUNDLE_MANIFEST.json",
        ]
        manifest = json.loads(archive.read(f"{BUNDLE_ROOT}/BUNDLE_MANIFEST.json"))
    assert manifest["deterministic_build"] is True
    assert manifest["contains_secret_files"] is False
    assert manifest["external_write"] is False
    assert manifest["files"][0]["path"] == "lesson.py"


def test_day3_bundle_blocks_secret_file_and_outside_paths(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    safe = root / "safe.txt"
    safe.write_text("safe", encoding="utf-8")
    secret_file = root / ".env"
    secret_file.write_text("OPENAI_API_KEY=not-for-shipping", encoding="utf-8")
    secret_content = root / "secret.txt"
    fake_token = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz"
    secret_content.write_text(f"token={fake_token}", encoding="utf-8")

    with pytest.raises(ValueError, match="DAY3_BUNDLE_PATH_BLOCKED"):
        build_bundle(root, root / "dist/release.zip", files=[secret_file])
    with pytest.raises(ValueError, match="DAY3_BUNDLE_SECRET_DETECTED"):
        build_bundle(root, root / "dist/release.zip", files=[secret_content])
    with pytest.raises(ValueError, match="DAY3_BUNDLE_DESTINATION_OUTSIDE_WORKSPACE"):
        build_bundle(root, tmp_path / "outside.zip", files=[safe])
    outside_source = tmp_path / "outside.txt"
    outside_source.write_text("safe", encoding="utf-8")
    with pytest.raises(ValueError, match="DAY3_BUNDLE_PATH_OUTSIDE_WORKSPACE"):
        build_bundle(root, root / "dist/release.zip", files=[outside_source])
