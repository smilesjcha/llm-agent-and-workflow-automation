from pathlib import Path
import zipfile

import pytest

from scripts.build_day1_student_bundle import BUNDLE_ROOT, build_bundle, student_files


ROOT = Path(__file__).resolve().parents[1]


def test_student_manifest_contains_notebooks_without_private_or_large_audio() -> None:
    relative = {path.relative_to(ROOT).as_posix() for path in student_files(ROOT)}
    assert "materials/day1/04_ollama_agent_workflow.ipynb" in relative
    assert "materials/day1/07_langchain_langgraph_workflow.ipynb" in relative
    assert ".env.sample" in relative
    assert "requirements-openai-optional.txt" in relative
    assert "data/meeting_sample_ko_12min.wav" not in relative
    assert ".env" not in relative


def test_bundle_builds_inside_workspace_and_blocks_outside_destination(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    sample = root / "README.md"
    sample.write_text("student bundle", encoding="utf-8")
    destination = root / "dist/bundle.zip"

    result = build_bundle(root, destination, files=[sample])
    assert result["status"] == "SUCCESS"
    with zipfile.ZipFile(destination) as archive:
        assert archive.namelist() == [f"{BUNDLE_ROOT}/README.md"]

    with pytest.raises(ValueError, match="BUNDLE_DESTINATION_OUTSIDE_WORKSPACE"):
        build_bundle(root, tmp_path / "outside.zip", files=[sample])

    local_secret = root / ".env.local"
    local_secret.write_text("must-not-ship", encoding="utf-8")
    with pytest.raises(ValueError, match="BUNDLE_PATH_BLOCKED"):
        build_bundle(root, destination, files=[local_secret])
