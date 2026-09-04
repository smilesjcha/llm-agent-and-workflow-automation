"""Build the deterministic, secret-free Day 3 student code bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = "llm-agent-workflow-day3"
DEFAULT_DESTINATION = ROOT / "dist/day3-student-code-bundle.zip"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
FORBIDDEN_PARTS = {
    ".env",
    ".git",
    ".venv",
    ".venv312",
    "__pycache__",
    "node_modules",
    "student-run",
}

# A deliberate allowlist prevents unrelated dirty or untracked worktree files from
# entering the student handout. Keep this list reviewable instead of using globs.
EXPLICIT_FILES = (
    "README.md",
    "AGENTS.md",
    "requirements-day3.txt",
    "requirements-local-llm-optional.txt",
    "requirements-openai-optional.txt",
    "materials/day3/2026_Day3_수강생_실습가이드.md",
    "materials/day3/GitHub_PR_자동화_런북.md",
    "materials/day3/day3_review_intelligence_lab.ipynb",
    "scripts/build_day3_notebook.py",
    "scripts/day3_pr_guard.py",
    "scripts/run_day3_preflight.py",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/codex/prompts/day3_pr_review.md",
    ".github/workflows/day3-pr-quality.yml",
    ".github/workflows/day3-codex-review-optional.yml",
    "labs/day3/review_copilot/AGENTS.md",
    "labs/day3/review_copilot/CODEX_TASK.md",
    "labs/day3/review_copilot/README.md",
    "labs/day3/review_copilot/__init__.py",
    "labs/day3/review_copilot/cli.py",
    "labs/day3/review_copilot/context_builder.py",
    "labs/day3/review_copilot/contracts.py",
    "labs/day3/review_copilot/day3.env.example",
    "labs/day3/review_copilot/diff_parser.py",
    "labs/day3/review_copilot/errors.py",
    "labs/day3/review_copilot/evaluation.py",
    "labs/day3/review_copilot/exports.py",
    "labs/day3/review_copilot/github_plan.py",
    "labs/day3/review_copilot/human_review.py",
    "labs/day3/review_copilot/langgraph_review.py",
    "labs/day3/review_copilot/providers.py",
    "labs/day3/review_copilot/review_engine.py",
    "labs/day3/review_copilot/safety.py",
    "labs/day3/review_copilot/test_evidence.py",
    "labs/day3/review_copilot/web.py",
    "labs/day3/review_copilot/web_app.py",
    "labs/day3/review_copilot/workflow.py",
    "labs/day3/review_copilot/workspace.py",
    "labs/day3/review_copilot/fixtures/cases.json",
    "labs/day3/review_copilot/fixtures/golden_findings.json",
    "labs/day3/review_copilot/fixtures/meeting_export_pr.diff",
    "labs/day3/review_copilot/fixtures/project_context.json",
    "labs/day3/review_copilot/fixtures/provider_fixture.json",
    "labs/day3/review_copilot/fixtures/cases/01_unsafe_exec.diff",
    "labs/day3/review_copilot/fixtures/cases/02_shell_injection.diff",
    "labs/day3/review_copilot/fixtures/cases/03_external_write.diff",
    "labs/day3/review_copilot/fixtures/cases/04_broad_exception.diff",
    "labs/day3/review_copilot/fixtures/cases/05_path_escape.diff",
    "labs/day3/review_copilot/fixtures/cases/06_secret_logging.diff",
    "labs/day3/review_copilot/fixtures/cases/07_timeout_idempotency.diff",
    "labs/day3/review_copilot/fixtures/cases/08_safe_negative.diff",
    "labs/day3/review_copilot/fixtures/repository/AGENTS.md",
    "labs/day3/review_copilot/fixtures/repository/__init__.py",
    "labs/day3/review_copilot/fixtures/repository/meeting_export.py",
    "labs/day3/review_copilot/fixtures/repository/test_meeting_export.py",
    "tests/test_day3_curriculum.py",
    "tests/test_day3_notebook.py",
    "tests/test_day3_preflight.py",
    "tests/test_day3_pr_guard.py",
    "tests/test_day3_review_copilot.py",
)

SECRET_PATTERNS = (
    re.compile(rb"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"lsv2_pt_[A-Za-z0-9_-]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def _inside(root: Path, candidate: Path) -> bool:
    return candidate == root or root in candidate.parents


def _validate_source(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"DAY3_BUNDLE_PATH_BLOCKED:{relative}")
    if any(part in FORBIDDEN_PARTS or part.startswith(".env") for part in relative.parts):
        raise ValueError(f"DAY3_BUNDLE_PATH_BLOCKED:{relative}")
    resolved = (root / relative).resolve()
    if not _inside(root, resolved):
        raise ValueError(f"DAY3_BUNDLE_PATH_OUTSIDE_WORKSPACE:{relative}")
    if not resolved.is_file():
        raise FileNotFoundError(f"DAY3_BUNDLE_FILE_MISSING:{relative}")
    return resolved


def _validate_content(path: Path) -> None:
    content = path.read_bytes()
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        raise ValueError(f"DAY3_BUNDLE_SECRET_DETECTED:{path.name}")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def student_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    selected = [_validate_source(root, Path(item)) for item in EXPLICIT_FILES]
    for path in selected:
        _validate_content(path)
    return selected


def _write_bytes(archive: zipfile.ZipFile, archive_name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def build_bundle(
    root: Path = ROOT,
    destination: Path = DEFAULT_DESTINATION,
    *,
    files: list[Path] | None = None,
) -> dict[str, object]:
    root = root.resolve()
    destination = destination.resolve()
    if not _inside(root, destination):
        raise ValueError("DAY3_BUNDLE_DESTINATION_OUTSIDE_WORKSPACE")

    selected = files if files is not None else student_files(root)
    entries: list[tuple[str, bytes]] = []
    for candidate in selected:
        try:
            relative = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError("DAY3_BUNDLE_PATH_OUTSIDE_WORKSPACE") from exc
        source = _validate_source(root, relative)
        _validate_content(source)
        entries.append((relative.as_posix(), source.read_bytes()))
    entries.sort(key=lambda item: item[0])

    manifest_files = [
        {"path": name, "bytes": len(content), "sha256": _sha256_bytes(content)}
        for name, content in entries
    ]
    manifest = {
        "bundle": BUNDLE_ROOT,
        "file_count": len(entries),
        "deterministic_build": True,
        "contains_secret_files": False,
        "external_write": False,
        "files": manifest_files,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as archive:
        for name, content in entries:
            _write_bytes(archive, f"{BUNDLE_ROOT}/{name}", content)
        _write_bytes(archive, f"{BUNDLE_ROOT}/BUNDLE_MANIFEST.json", manifest_bytes)

    return {
        "status": "SUCCESS",
        "archive": destination.relative_to(root).as_posix(),
        "file_count": len(entries),
        "sha256": _sha256_file(destination),
        "external_write": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    destination = args.out if args.out.is_absolute() else ROOT / args.out
    print(json.dumps(build_bundle(ROOT, destination), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
