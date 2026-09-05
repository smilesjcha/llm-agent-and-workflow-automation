"""Workspace-only file access used by every classroom adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_workspace_path(
    candidate: str | Path,
    *,
    workspace_root: str | Path,
    must_exist: bool = True,
) -> Path:
    """Resolve first, then verify the path remains under the workspace root."""

    root = Path(workspace_root).resolve()
    path = Path(candidate)
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("WORKSPACE_PATH_BLOCKED")
    if must_exist and not resolved.exists():
        raise ValueError("WORKSPACE_FILE_NOT_FOUND")
    return resolved


def read_workspace_text(candidate: str | Path, *, workspace_root: str | Path) -> str:
    path = resolve_workspace_path(candidate, workspace_root=workspace_root)
    if not path.is_file():
        raise ValueError("WORKSPACE_FILE_REQUIRED")
    return path.read_text(encoding="utf-8")


def read_workspace_json(candidate: str | Path, *, workspace_root: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(read_workspace_text(candidate, workspace_root=workspace_root))
    except json.JSONDecodeError as exc:
        raise ValueError("WORKSPACE_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise ValueError("WORKSPACE_JSON_OBJECT_REQUIRED")
    return payload


def write_workspace_json(
    candidate: str | Path,
    payload: dict[str, Any],
    *,
    workspace_root: str | Path,
) -> Path:
    """Write only an explicit local artifact; never publish it externally."""

    path = resolve_workspace_path(
        candidate,
        workspace_root=workspace_root,
        must_exist=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
