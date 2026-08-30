"""Build a reviewed, secret-free Day 2 student distribution ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = "llm-agent-workflow-day2"
FORBIDDEN_PARTS = {".env", ".git", ".venv", ".venv312", "__pycache__", "node_modules"}

EXPLICIT_FILES = (
    "README.md",
    "AGENTS.md",
    ".env.sample",
    "requirements-day2.txt",
    "requirements-local-llm-optional.txt",
    "requirements-openai-optional.txt",
    "requirements-stt-optional.txt",
    "materials/day2/2026_Day2_수강생_실습가이드.md",
    "materials/day2/일반인을_위한_회의기록_Agent_설계.md",
    "materials/day2/Codex_Claude_대화_시나리오.md",
    "materials/day2/공개_한국어_회의음성_가이드.md",
    "materials/day2/day2_service_lab.ipynb",
    "materials/day2/day2_service_lab.executed.ipynb",
    "slides/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pptx",
    "output/pdf/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pdf",
    "src/course_services/__init__.py",
    "src/course_services/day2_meeting_workflow.py",
    "tests/test_day2_meeting_workflow.py",
    "tests/test_day2_notebook.py",
    "tests/test_day2_localhost_app.py",
    "scripts/build_days2_5_notebooks.py",
    "scripts/day2_public_audio.py",
    "scripts/day2_public_audio_verify.py",
    "scripts/day2_desktop_smoke.py",
    "scripts/run_day2_local_app.py",
    "scripts/run_day2_preflight.py",
    "data/day2_public_audio/meeting_ko_ccby_excerpt_10m.mp3",
    "data/day2_public_audio/SHA256SUMS",
    "data/day2_public_audio/sources.json",
    "desktop-app/meeting-intelligence/.env.example",
    "desktop-app/meeting-intelligence/Dockerfile",
    "desktop-app/meeting-intelligence/Makefile",
    "desktop-app/meeting-intelligence/README.md",
    "desktop-app/meeting-intelligence/docker-compose.yml",
    "desktop-app/meeting-intelligence/go.mod",
    "desktop-app/meeting-intelligence/main.go",
    "desktop-app/meeting-intelligence/main_test.go",
    "desktop-app/meeting-intelligence/requirements.txt",
    "desktop-app/meeting-intelligence/requirements-localhost.txt",
    "desktop-app/meeting-intelligence/tests/__init__.py",
    "desktop-app/meeting-intelligence/tests/conftest.py",
    "desktop-app/meeting-intelligence/tests/test_api.py",
    "desktop-app/meeting-intelligence/tests/test_live_dependencies.py",
    "desktop-app/meeting-intelligence/tests/test_pipeline.py",
    "desktop-app/meeting-intelligence/tests/test_providers_v2.py",
    "desktop-app/meeting-intelligence/tests/test_scenarios.py",
    "desktop-app/meeting-intelligence/dist/MeetingIntelligence-Windows.exe",
    "desktop-app/meeting-intelligence/dist/MeetingIntelligence-macOS.pkg",
    "desktop-app/meeting-intelligence/dist/SHA256SUMS",
    "desktop-app/meeting-intelligence/dist/RELEASE_STATUS.json",
)
GLOB_PATTERNS = (
    "labs/day2/codex-task/**/*.md",
    "labs/day2/codex-task/**/*.py",
    "output/course-labs/day2-v2/*",
    "desktop-app/meeting-intelligence/app/*.py",
    "desktop-app/meeting-intelligence/fixtures/*",
    "desktop-app/meeting-intelligence/static/*",
    "desktop-app/meeting-intelligence/scripts/*.sh",
    "desktop-app/meeting-intelligence/scripts/*.command",
    "desktop-app/meeting-intelligence/scripts/*.cmd",
    "desktop-app/meeting-intelligence/packaging/macos/*",
)


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _forbidden(part: str) -> bool:
    if part in FORBIDDEN_PARTS:
        return True
    return part.startswith(".env.") and part not in {".env.sample", ".env.example"}


def _validate_relative_path(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or any(_forbidden(part) for part in relative.parts):
        raise ValueError(f"DAY2_BUNDLE_PATH_BLOCKED:{relative}")
    resolved = (root / relative).resolve()
    if not _inside(root, resolved):
        raise ValueError(f"DAY2_BUNDLE_PATH_OUTSIDE_WORKSPACE:{relative}")
    if not resolved.is_file():
        raise FileNotFoundError(f"DAY2_BUNDLE_FILE_MISSING:{relative}")
    return resolved


def student_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    relatives = {Path(item) for item in EXPLICIT_FILES}
    for pattern in GLOB_PATTERNS:
        relatives.update(path.relative_to(root) for path in root.glob(pattern) if path.is_file())
    return sorted((_validate_relative_path(root, item) for item in relatives), key=str)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_bundle(
    root: Path,
    destination: Path,
    *,
    files: list[Path] | None = None,
) -> dict[str, object]:
    root = root.resolve()
    destination = destination.resolve()
    if not _inside(root, destination):
        raise ValueError("DAY2_BUNDLE_DESTINATION_OUTSIDE_WORKSPACE")
    selected = files or student_files(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_files: list[dict[str, object]] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in selected:
            relative = source.resolve().relative_to(root)
            source = _validate_relative_path(root, relative)
            archive.write(source, Path(BUNDLE_ROOT) / relative)
            manifest_files.append(
                {"path": relative.as_posix(), "bytes": source.stat().st_size, "sha256": _sha256(source)}
            )
        manifest = {
            "bundle": BUNDLE_ROOT,
            "file_count": len(manifest_files),
            "contains_secret_files": False,
            "external_write": False,
            "files": manifest_files,
        }
        archive.writestr(
            f"{BUNDLE_ROOT}/BUNDLE_MANIFEST.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return {
        "status": "SUCCESS",
        "archive": str(destination.relative_to(root)),
        "file_count": len(selected),
        "sha256": _sha256(destination),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist/day2-student-lab-bundle.zip")
    args = parser.parse_args(argv)
    destination = args.out if args.out.is_absolute() else ROOT / args.out
    print(json.dumps(build_bundle(ROOT, destination), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
