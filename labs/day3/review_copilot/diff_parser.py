"""Minimal unified-diff parser with exact added-line mapping."""

from __future__ import annotations

import re

from .contracts import AddedLine, ParsedDiff


_HUNK = re.compile(
    r"^@@\s+-(?P<old>\d+)(?:,\d+)?\s+\+(?P<new>\d+)(?:,\d+)?\s+@@"
)


def _safe_diff_path(raw: str) -> str | None:
    path = raw.strip().split("\t", 1)[0]
    if path == "/dev/null":
        return None
    if path.startswith("b/"):
        path = path[2:]
    if not path or path.startswith("/") or ".." in path.split("/"):
        raise ValueError("DIFF_PATH_BLOCKED")
    return path


def parse_unified_diff(diff_text: str) -> ParsedDiff:
    """Return only changed paths and added source lines from a unified diff."""

    if not diff_text.strip():
        raise ValueError("EMPTY_DIFF")

    paths: list[str] = []
    added: list[AddedLine] = []
    current_path: str | None = None
    old_line: int | None = None
    new_line: int | None = None
    saw_hunk = False

    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            current_path = _safe_diff_path(raw[4:])
            if current_path and current_path not in paths:
                paths.append(current_path)
            old_line = new_line = None
            continue
        match = _HUNK.match(raw)
        if match:
            if current_path is None:
                raise ValueError("HUNK_WITHOUT_TARGET")
            old_line = int(match.group("old"))
            new_line = int(match.group("new"))
            saw_hunk = True
            continue
        if current_path is None or old_line is None or new_line is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            added.append(AddedLine(path=current_path, line=new_line, text=raw[1:]))
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            old_line += 1
        elif raw.startswith(" "):
            old_line += 1
            new_line += 1
        elif raw.startswith("\\ No newline"):
            continue

    if not saw_hunk:
        raise ValueError("UNIFIED_DIFF_HUNK_REQUIRED")
    return ParsedDiff(changed_paths=tuple(paths), added_lines=tuple(added))
