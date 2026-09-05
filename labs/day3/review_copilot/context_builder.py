"""Small, auditable context pack for a code-review model."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

from .contracts import ParsedDiff, ReviewPolicy
from .safety import contains_secret_like_text, is_sensitive_path, redact_payload
from .workspace import resolve_workspace_path


_TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".yml", ".yaml"}


def _test_candidates(path: str) -> list[str]:
    parsed = PurePosixPath(path)
    if parsed.suffix != ".py" or parsed.parts[0] == "tests":
        return []
    values = [
        (parsed.parent / f"test_{parsed.stem}.py").as_posix(),
        f"tests/test_{parsed.stem}.py",
    ]
    return list(dict.fromkeys(values))


def build_context_pack(
    parsed: ParsedDiff,
    *,
    policy: ReviewPolicy,
    project_context: dict[str, Any] | None = None,
    max_bytes: int = 20_000,
    workspace_root: str | Path | None = None,
    max_files: int = 6,
    context_lines: int = 4,
) -> dict[str, Any]:
    """Expose only review-relevant metadata, never repository-wide content."""

    if max_bytes < 1:
        raise ValueError("CONTEXT_BYTE_LIMIT_INVALID")
    if max_files < 1:
        raise ValueError("CONTEXT_FILE_LIMIT_INVALID")
    if context_lines < 0 or context_lines > 20:
        raise ValueError("CONTEXT_LINE_WINDOW_INVALID")

    blocked = sorted(path for path in parsed.changed_paths if is_sensitive_path(path))
    allowed_paths = [path for path in parsed.changed_paths if path not in blocked]

    project_context = project_context or {}
    allowed_keys = {"service_name", "purpose", "runtime", "quality_rules"}
    raw_context = {
        key: project_context[key] for key in sorted(allowed_keys & project_context.keys())
    }
    context, context_redaction_count = redact_payload(raw_context)
    tests = sorted(
        {candidate for path in allowed_paths for candidate in _test_candidates(path)}
    )
    result = {
        "changed_paths": list(parsed.changed_paths),
        "added_line_count": len(parsed.added_lines),
        "test_candidates": tests,
        "review_focus": list(policy.focus),
        "ignored_focus": list(policy.ignored),
        "project_context": context,
        "excluded_data": ["credentials", "environment_values", "unrelated_files"],
        "redaction_count": context_redaction_count,
        "excluded_paths": [
            {"path": path, "reason": "SENSITIVE_PATH_NOT_READ"} for path in blocked
        ],
        "repository_context": [],
        "existing_tests": [],
        "applicable_policies": [],
        "limits": {
            "max_bytes": max_bytes,
            "max_files": max_files,
            "context_lines": context_lines,
        },
    }

    if _finalized_size(result, max_bytes=max_bytes) > max_bytes:
        raise ValueError("CONTEXT_BUDGET_EXCEEDED")

    if workspace_root is not None:
        _add_repository_context(
            result,
            parsed=parsed,
            allowed_paths=allowed_paths,
            test_candidates=tests,
            workspace_root=Path(workspace_root),
            max_bytes=max_bytes,
            max_files=max_files,
            context_lines=context_lines,
        )

    return _finalize_payload(result, max_bytes=max_bytes)


def _byte_size(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def _finalized_size(payload: dict[str, Any], *, max_bytes: int) -> int:
    return _byte_size(_finalize_payload(payload, max_bytes=max_bytes, enforce_limit=False))


def _finalize_payload(
    payload: dict[str, Any],
    *,
    max_bytes: int,
    enforce_limit: bool = True,
) -> dict[str, Any]:
    final = {**payload, "context_byte_limit": max_bytes, "context_bytes": 0}
    for _ in range(8):
        size = _byte_size(final)
        if final["context_bytes"] == size:
            break
        final["context_bytes"] = size
    if final["context_bytes"] != _byte_size(final):
        raise ValueError("CONTEXT_SIZE_STABILIZATION_FAILED")
    if enforce_limit and final["context_bytes"] > max_bytes:
        raise ValueError("CONTEXT_BUDGET_EXCEEDED")
    return final


def _append_if_budget(
    result: dict[str, Any],
    *,
    field: str,
    item: dict[str, Any],
    max_bytes: int,
) -> bool:
    values = result[field]
    assert isinstance(values, list)
    candidate = {**result, field: [*values, item]}
    if _finalized_size(candidate, max_bytes=max_bytes) > max_bytes:
        _record_exclusion(
            result,
            path=str(item.get("path", field)),
            reason="BYTE_BUDGET",
            max_bytes=max_bytes,
        )
        return False
    values.append(item)
    return True


def _record_exclusion(
    result: dict[str, Any],
    *,
    path: str,
    reason: str,
    max_bytes: int,
) -> None:
    excluded = result["excluded_paths"]
    assert isinstance(excluded, list)
    item = {"path": path, "reason": reason}
    candidate = {**result, "excluded_paths": [*excluded, item]}
    if _finalized_size(candidate, max_bytes=max_bytes) <= max_bytes:
        excluded.append(item)


def _line_snippet(path: Path, line_numbers: list[int], *, context_lines: int) -> dict[str, Any]:
    if path.stat().st_size > 250_000:
        raise ValueError("CONTEXT_FILE_TOO_LARGE")
    lines = path.read_text(encoding="utf-8").splitlines()
    first = max(1, min(line_numbers) - context_lines)
    last = min(len(lines), max(line_numbers) + context_lines)
    numbered = [f"{index}: {lines[index - 1]}" for index in range(first, last + 1)]
    return {"line_start": first, "line_end": last, "content": "\n".join(numbered)}


def _add_repository_context(
    result: dict[str, Any],
    *,
    parsed: ParsedDiff,
    allowed_paths: list[str],
    test_candidates: list[str],
    workspace_root: Path,
    max_bytes: int,
    max_files: int,
    context_lines: int,
) -> None:
    """Add bounded real files only when they exist inside the workspace."""

    root = workspace_root.resolve()
    line_numbers: dict[str, list[int]] = {}
    for added in parsed.added_lines:
        line_numbers.setdefault(added.path, []).append(added.line)

    files_added = 0
    for raw_path in allowed_paths:
        if files_added >= max_files:
            _record_exclusion(result, path=raw_path, reason="FILE_LIMIT", max_bytes=max_bytes)
            continue
        if PurePosixPath(raw_path).suffix not in _TEXT_SUFFIXES:
            _record_exclusion(
                result,
                path=raw_path,
                reason="UNSUPPORTED_TEXT_TYPE",
                max_bytes=max_bytes,
            )
            continue
        try:
            path = resolve_workspace_path(raw_path, workspace_root=root)
        except ValueError as exc:
            reason = "FILE_NOT_PRESENT_IN_FIXTURE_REPOSITORY" if str(exc) == "WORKSPACE_FILE_NOT_FOUND" else str(exc)
            _record_exclusion(result, path=raw_path, reason=reason, max_bytes=max_bytes)
            continue
        try:
            snippet = _line_snippet(
                path,
                line_numbers.get(raw_path, [1]),
                context_lines=context_lines,
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            _record_exclusion(
                result,
                path=raw_path,
                reason=str(exc),
                max_bytes=max_bytes,
            )
            continue
        if contains_secret_like_text(str(snippet["content"])):
            _record_exclusion(
                result,
                path=raw_path,
                reason="SECRET_LIKE_CONTENT",
                max_bytes=max_bytes,
            )
            continue
        if _append_if_budget(
            result,
            field="repository_context",
            item={"path": raw_path, **snippet},
            max_bytes=max_bytes,
        ):
            files_added += 1

    for raw_path in test_candidates:
        if files_added >= max_files:
            _record_exclusion(result, path=raw_path, reason="FILE_LIMIT", max_bytes=max_bytes)
            continue
        try:
            path = resolve_workspace_path(raw_path, workspace_root=root)
        except ValueError:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()[:80]
        except (OSError, UnicodeDecodeError):
            continue
        content = "\n".join(lines)
        if contains_secret_like_text(content):
            _record_exclusion(
                result,
                path=raw_path,
                reason="SECRET_LIKE_CONTENT",
                max_bytes=max_bytes,
            )
            continue
        if _append_if_budget(
            result,
            field="existing_tests",
            item={"path": raw_path, "content": content},
            max_bytes=max_bytes,
        ):
            files_added += 1

    policy_paths = [root / "AGENTS.md"]
    for raw_path in allowed_paths:
        current = (root / raw_path).parent
        while current.is_relative_to(root) and current != root:
            policy_paths.append(current / "AGENTS.md")
            current = current.parent
    seen: set[Path] = set()
    for policy_path in policy_paths:
        resolved = policy_path.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        relative = resolved.relative_to(root).as_posix()
        try:
            content = resolved.read_text(encoding="utf-8")[:4000]
        except (OSError, UnicodeDecodeError):
            continue
        _append_if_budget(
            result,
            field="applicable_policies",
            item={"path": relative, "content": content},
            max_bytes=max_bytes,
        )
