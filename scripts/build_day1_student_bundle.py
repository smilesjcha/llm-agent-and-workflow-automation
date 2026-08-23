"""Build a secret-free Day 1 student lab bundle with an explicit manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = "llm-agent-workflow-day1"
FORBIDDEN_NAMES = {".env", ".git", "__pycache__", "node_modules"}

EXPLICIT_FILES = (
    "README.md",
    "AGENTS.md",
    "requirements-day1.txt",
    "requirements-local-llm-optional.txt",
    "requirements-stt-optional.txt",
    "materials/day1/01_agent_foundation.ipynb",
    "materials/day1/01_agent_foundation.executed.ipynb",
    "materials/day1/04_ollama_agent_workflow.ipynb",
    "materials/day1/04_ollama_agent_workflow.executed.ipynb",
    "materials/day1/07_langchain_langgraph_workflow.ipynb",
    "materials/day1/07_langchain_langgraph_workflow.executed.ipynb",
    "materials/day1/수강생용_4-8차시_실습패키지_가이드.md",
    "materials/day1/실행파일_차시별_맵.md",
    "data/demo_meeting.wav",
    "data/demo_meeting_transcript.txt",
    "data/meeting_sample_ko.txt",
    "data/meeting_sample_ko_12min.txt",
    "data/meeting_sample_ko_12min_DATASET_CARD.md",
    "data/meeting_sample_ko_12min_expected.json",
)
GLOB_PATTERNS = (
    "src/*.py",
    "tests/*.py",
    "web-demo/*",
)


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _validate_relative_path(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or any(part in FORBIDDEN_NAMES for part in relative.parts):
        raise ValueError(f"BUNDLE_PATH_BLOCKED: {relative}")
    resolved = (root / relative).resolve()
    if not _inside(root, resolved):
        raise ValueError(f"BUNDLE_PATH_OUTSIDE_WORKSPACE: {relative}")
    if not resolved.is_file():
        raise FileNotFoundError(f"BUNDLE_FILE_MISSING: {relative}")
    return resolved


def student_files(root: Path, *, include_long_audio: bool = False) -> list[Path]:
    """Return the reviewed student manifest relative to ``root``."""

    root = root.resolve()
    relatives = {Path(item) for item in EXPLICIT_FILES}
    for pattern in GLOB_PATTERNS:
        relatives.update(path.relative_to(root) for path in root.glob(pattern) if path.is_file())
    if include_long_audio:
        relatives.add(Path("data/meeting_sample_ko_12min.wav"))
    return sorted((_validate_relative_path(root, item) for item in relatives), key=str)


def build_bundle(
    root: Path,
    destination: Path,
    *,
    include_long_audio: bool = False,
    files: list[Path] | None = None,
) -> dict[str, object]:
    """Create one zip inside the configured workspace and return its evidence."""

    root = root.resolve()
    destination = destination.resolve()
    if not _inside(root, destination):
        raise ValueError("BUNDLE_DESTINATION_OUTSIDE_WORKSPACE")
    selected = files or student_files(root, include_long_audio=include_long_audio)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in selected:
            source = _validate_relative_path(root, source.resolve().relative_to(root))
            relative = source.relative_to(root)
            archive.write(source, Path(BUNDLE_ROOT) / relative)
    return {
        "status": "SUCCESS",
        "archive": str(destination.relative_to(root)),
        "file_count": len(selected),
        "includes_long_audio": include_long_audio,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "dist/day1-student-lab-bundle.zip",
    )
    parser.add_argument("--include-long-audio", action="store_true")
    args = parser.parse_args()
    print(build_bundle(ROOT, args.out, include_long_audio=args.include_long_audio))


if __name__ == "__main__":
    main()
