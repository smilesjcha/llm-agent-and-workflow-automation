"""Preflight contracts without recursively launching pytest or using accounts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from scripts import run_day3_preflight as preflight


@pytest.fixture
def offline_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, list]:
    for relative in preflight.REQUIRED_CODE_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n.env.*\n!.env.sample\n", encoding="utf-8")
    calls = []

    def fake_command(*args: str, **kwargs: object) -> dict:
        calls.append((args, kwargs))
        return {"status": "PASS", "return_code": 0, "stdout_tail": [], "stderr_tail": []}

    monkeypatch.setattr(preflight, "_command", fake_command)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(preflight.shutil, "which", lambda name: None)
    return tmp_path, calls


def test_extracted_code_bundle_passes_without_git_or_codex(offline_workspace: tuple) -> None:
    root, calls = offline_workspace
    report = preflight.build_report(code_only=True, root=root)

    assert report["status"] == "PASS"
    assert report["mode"] == "code-only"
    assert not (root / ".git").exists()
    assert report["commands"]["required"] == {}
    assert report["codex_cli"]["status"] == "NOT_INSTALLED"
    assert len(calls) == 2
    assert set(preflight.OFFLINE_TESTS).issubset(calls[0][0])
    assert "tests/test_day3_deep_dive.py" in calls[0][0]
    assert not set(preflight.CLASSROOM_TESTS).intersection(calls[0][0])
    assert report["secret_boundary"]["env_values_read"] is False
    assert report["secret_boundary"]["git_metadata_required"] is False


def test_full_classroom_requires_deck_while_code_mode_does_not(offline_workspace: tuple) -> None:
    root, _ = offline_workspace
    report = preflight.build_report(root=root)

    assert report["status"] == "FAIL"
    assert report["required_files"]["slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx"] is False
    assert preflight.build_report(code_only=True, root=root)["status"] == "PASS"


def test_missing_runtime_file_fails_even_in_code_mode(offline_workspace: tuple) -> None:
    root, _ = offline_workspace
    (root / "labs/day3/review_copilot/exercise.py").unlink()
    report = preflight.build_report(code_only=True, root=root)

    assert report["status"] == "FAIL"
    assert report["required_files"]["labs/day3/review_copilot/exercise.py"] is False


@pytest.mark.parametrize("relative", [
    "labs/day3/review_copilot/deep_dive.py",
    "tests/test_day3_deep_dive.py",
    "materials/day3/day3_global_references.json",
    "materials/day3/글로벌_사례_해설.md",
])
def test_missing_deep_dive_or_reference_file_fails_code_preflight(offline_workspace: tuple, relative: str) -> None:
    root, _ = offline_workspace
    assert relative in preflight.REQUIRED_CODE_FILES
    (root / relative).unlink()
    report = preflight.build_report(code_only=True, root=root)
    assert report["status"] == "FAIL"
    assert report["required_files"][relative] is False


def test_full_classroom_passes_with_all_assets_and_git(offline_workspace: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    root, calls = offline_workspace
    for relative in preflight.REQUIRED_CLASSROOM_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("public classroom asset", encoding="utf-8")
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/tool/git" if name == "git" else None)
    report = preflight.build_report(full_suite=True, root=root)

    assert report["status"] == "PASS"
    assert len(calls) == 3
    assert set(preflight.CLASSROOM_TESTS).issubset(calls[0][0])
    assert set(preflight.DAY1_TESTS).issubset(calls[2][0])


def test_failed_test_is_not_hidden_by_available_files(offline_workspace: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = offline_workspace
    monkeypatch.setattr(preflight, "_command", lambda *args, **kwargs: {"status": "FAIL", "return_code": 1})
    assert preflight.build_report(code_only=True, root=root)["status"] == "FAIL"


@pytest.mark.parametrize("negation", ["!.env", "!*"])
def test_ignore_negation_is_not_treated_as_secret_protection(offline_workspace: tuple, negation: str) -> None:
    root, _ = offline_workspace
    (root / ".gitignore").write_text(f".env\n{negation}\n", encoding="utf-8")
    report = preflight.build_report(code_only=True, root=root)

    assert report["status"] == "FAIL"
    assert report["secret_boundary"]["env_file_ignored"] is False


def test_codex_login_check_discards_text_and_excludes_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/tool/codex")
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-credential")
    seen = {}

    def fake_run(args: list, **kwargs: object) -> SimpleNamespace:
        seen.update({"args": args, **kwargs})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    report = preflight.codex_readiness()

    assert report["status"] == "READY"
    assert report["model_request_sent"] is False
    assert seen["args"] == ["/tool/codex", "login", "status"]
    assert seen["stdout"] == subprocess.DEVNULL
    assert seen["stderr"] == subprocess.DEVNULL
    assert "OPENAI_API_KEY" not in seen["env"]


@pytest.mark.parametrize("return_code,expected", [(1, "LOGIN_REQUIRED"), (0, "READY")])
def test_codex_login_state_is_separate_from_offline_pass(return_code: int, expected: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/tool/codex")
    monkeypatch.setattr(preflight.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=return_code))
    report = preflight.codex_readiness()
    assert report["status"] == expected
    assert report["required_for_offline_checks"] is False


def test_command_timeout_preserves_structured_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("test-command", 1)

    monkeypatch.setattr(preflight.subprocess, "run", timeout)
    report = preflight._command("test-command")
    assert report["status"] == "FAIL"
    assert report["error_code"] == "COMMAND_TIMEOUT"
    assert report["stdout_tail"] == []


def test_codex_status_timeout_keeps_offline_work_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/tool/codex")

    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("codex login status", 10)

    monkeypatch.setattr(preflight.subprocess, "run", timeout)
    report = preflight.codex_readiness()
    assert report["status"] == "STATUS_TIMEOUT"
    assert report["required_for_offline_checks"] is False
    assert report["credential_values_recorded"] is False


def test_ignore_check_does_not_follow_an_outside_symlink(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside-ignore"
    outside.write_text(".env\n", encoding="utf-8")
    (root / ".gitignore").symlink_to(outside)
    assert preflight._env_ignore_check(root)["env_file_ignored"] is False


def test_cli_rejects_incompatible_modes_before_running_checks() -> None:
    with pytest.raises(SystemExit) as exc:
        preflight.main(["--code-only", "--full-suite"])
    assert exc.value.code == 2
