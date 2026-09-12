"""Day 4 safety contracts, all deterministic and network-free."""

import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from labs.day4.pr_review_lab import (
    LabError, approve_preview, build_review, check_exercise, fetch_public_pr,
    load_fixture, prepare_exercise, preview_publication, render_outputs,
    validate_snapshot,
)
from labs.day4.pr_review_lab.service import DEFAULT_REPO, FIXTURES, changed_lines, workspace_path


def approved_review():
    snapshot = load_fixture()
    review = build_review(snapshot)
    approval = approve_preview(snapshot, review, approved=True, reviewer="student")
    return snapshot, review, approval


def assert_blocked(code, function, *args, **kwargs):
    with pytest.raises(LabError) as exc:
        function(*args, **kwargs)
    assert exc.value.code == code
    assert exc.value.as_dict()["status"] == "BLOCKED"


def test_fixture_has_real_diff_and_actionable_review():
    snapshot = load_fixture()
    review = build_review(snapshot)
    assert changed_lines(snapshot["files"][0]["patch"]) == {1, 4, 5, 6}
    assert len(review["findings"]) == 2
    assert "checkout.py:6" in review["markdown"]
    assert "-4,000원" in review["markdown"]
    assert review["provider"] == "fixture"


@pytest.mark.parametrize("key,value,code", [
    ("repo", "another/repo", "REPO_MISMATCH"),
    ("base_repo", "another/repo", "REPO_MISMATCH"),
    ("number", 43, "PR_MISMATCH"),
    ("url", "https://github.com/another/repo/pull/42", "PR_URL_MISMATCH"),
    ("head_sha", "abc", "INVALID_SHA"),
    ("base_sha", None, "INVALID_SHA"),
    ("state", "closed", "PR_NOT_OPEN"),
])
def test_target_revision_validation(key, value, code):
    snapshot = load_fixture()
    snapshot[key] = value
    assert_blocked(code, validate_snapshot, snapshot, expected_repo=DEFAULT_REPO, expected_pr=42)


@pytest.mark.parametrize("path", ["../private.txt", "/etc/passwd", "C:\\secrets.txt", "a/../../b"])
def test_diff_path_traversal_blocked(path):
    snapshot = load_fixture()
    snapshot["files"][0]["path"] = path
    assert_blocked("INVALID_DIFF_PATH", validate_snapshot, snapshot, expected_repo=DEFAULT_REPO, expected_pr=42)


def test_missing_or_large_patch_is_not_silently_ignored():
    snapshot = load_fixture()
    snapshot["files"][0]["patch"] = None
    assert_blocked("PATCH_UNAVAILABLE", validate_snapshot, snapshot, expected_repo=DEFAULT_REPO, expected_pr=42)
    snapshot["files"][0]["patch"] = "@@ -1 +1 @@\n+" + "가" * 100_000
    assert_blocked("PATCH_LIMIT", validate_snapshot, snapshot, expected_repo=DEFAULT_REPO, expected_pr=42)


def test_finding_must_reference_changed_line_and_have_evidence():
    snapshot = load_fixture()
    findings = build_review(snapshot)["findings"]
    findings[0]["line"] = 999
    assert_blocked("FINDING_NOT_IN_DIFF", build_review, snapshot, findings)
    findings[0]["line"] = 6
    findings[0]["impact"] = ""
    assert_blocked("INCOMPLETE_FINDING", build_review, snapshot, findings)


def test_changed_fixture_does_not_claim_precomputed_findings():
    snapshot = load_fixture()
    snapshot["files"][0]["patch"] += "\n+# modified"
    assert_blocked("FINDINGS_REQUIRED", build_review, snapshot)


def test_comment_preview_has_sha_and_never_approves_or_publishes():
    snapshot, review, approval = approved_review()
    result = preview_publication(snapshot, review, approval, current_head_sha=snapshot["head_sha"])
    assert result["status"] == "PREVIEW_ONLY"
    assert result["remote_write_performed"] is False
    assert result["payload"]["event"] == "COMMENT"
    assert result["payload"]["commit_id"] == snapshot["head_sha"]
    assert result["endpoint"] == "/repos/training-example/checkout-demo/pulls/42/reviews"


def test_approval_required_and_decline_is_not_approval():
    snapshot, review, _ = approved_review()
    assert_blocked("HUMAN_APPROVAL_REQUIRED", approve_preview, snapshot, review, approved=False, reviewer="student")
    assert_blocked("HUMAN_APPROVAL_REQUIRED", preview_publication, snapshot, review, None, current_head_sha=snapshot["head_sha"])


def test_stale_sha_requires_new_review():
    snapshot, review, approval = approved_review()
    assert_blocked("STALE_HEAD_SHA", preview_publication, snapshot, review, approval, current_head_sha="3" * 40)


@pytest.mark.parametrize("field,value", [("repo", "other/repo"), ("number", 1), ("head_sha", "a" * 40),
                                          ("review_sha256", "bad"), ("scope", "publish")])
def test_approval_is_bound_to_exact_target_and_content(field, value):
    snapshot, review, approval = approved_review()
    approval[field] = value
    assert_blocked("APPROVAL_MISMATCH", preview_publication, snapshot, review, approval, current_head_sha=snapshot["head_sha"])


def test_changed_review_is_not_covered_by_old_approval():
    snapshot, review, approval = approved_review()
    review["markdown"] += "\n추가 의견"
    assert_blocked("REVIEW_CHANGED", preview_publication, snapshot, review, approval, current_head_sha=snapshot["head_sha"])


def test_duplicate_marker_survives_updated_review_history():
    snapshot, review, approval = approved_review()
    first = preview_publication(snapshot, review, approval, current_head_sha=snapshot["head_sha"])
    snapshot["existing_reviews"] = [{"body": first["payload"]["body"]}]
    rebuilt = build_review(snapshot)
    assert rebuilt["review_sha256"] == review["review_sha256"]
    assert_blocked("DUPLICATE_REVIEW", preview_publication, snapshot, rebuilt, approval, current_head_sha=snapshot["head_sha"])


def test_learner_edit_failing_then_passing(tmp_path):
    result = prepare_exercise(tmp_path, "exercise")
    first = check_exercise(tmp_path, "exercise")
    assert first["status"] == "FAILED"
    assert "4 failed, 1 passed" in first["output"]
    Path(result["edit_file"]).write_text((FIXTURES / "checkout_solution.py").read_text(), encoding="utf-8")
    second = check_exercise(tmp_path, "exercise")
    assert second["status"] == "PASSED"
    assert "5 passed" in second["output"]
    assert_blocked("EXERCISE_EXISTS", prepare_exercise, tmp_path, "exercise")


def test_workspace_escape_and_symlink_blocked(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    assert_blocked("PATH_OUTSIDE_WORKSPACE", workspace_path, root, "../secret")
    (root / "link").symlink_to(tmp_path, target_is_directory=True)
    assert_blocked("PATH_OUTSIDE_WORKSPACE", workspace_path, root, "link/out.txt")


def test_html_output_escapes_untrusted_code(tmp_path):
    snapshot = load_fixture()
    findings = build_review(snapshot)["findings"]
    findings[0]["title"] = "<script>alert(1)</script>"
    review = build_review(snapshot, findings, provider="human-reviewed")
    paths = render_outputs(tmp_path, "report", snapshot, review)
    page = Path(paths["review.html"]).read_text()
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "AWAITING_HUMAN_REVIEW" in Path(paths["publication_preview.json"]).read_text()


def test_output_symlink_never_overwrites_other_location(tmp_path):
    (tmp_path / "report").mkdir()
    protected = tmp_path / "protected.txt"
    protected.write_text("keep")
    (tmp_path / "report" / "review.md").symlink_to(protected)
    snapshot = load_fixture()
    assert_blocked("PATH_OUTSIDE_WORKSPACE", render_outputs, tmp_path, "report", snapshot, build_review(snapshot))
    assert protected.read_text() == "keep"


def public_runner(*, private=False, stale=False, failure=False):
    snapshot = load_fixture()
    pull = {"changed_files": 1, "title": snapshot["title"], "state": "open", "html_url": snapshot["url"],
            "base": {"repo": {"full_name": DEFAULT_REPO}, "sha": snapshot["base_sha"]},
            "head": {"sha": snapshot["head_sha"]}}
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        assert command[:4] == ["gh", "api", "--method", "GET"]
        assert command[4:6] == ["--hostname", "github.com"]
        endpoint = command[-1]
        if endpoint.endswith("/files?per_page=100"):
            data = [{"filename": "checkout.py", "status": "modified", "patch": snapshot["files"][0]["patch"]}]
        elif endpoint.endswith("/reviews?per_page=100"):
            data = []
        elif endpoint.endswith("/pulls/42"):
            data = copy.deepcopy(pull)
            if stale and len(calls) == 5:
                data["head"]["sha"] = "3" * 40
        else:
            data = {"private": private}
        return SimpleNamespace(returncode=1 if failure else 0, stdout=json.dumps(data), stderr="not exposed")
    return run, calls


def test_network_opt_in_required_before_any_request():
    runner, calls = public_runner()
    assert_blocked("NETWORK_OPT_IN_REQUIRED", fetch_public_pr, DEFAULT_REPO, 42, runner=runner)
    assert calls == []


def test_public_fetch_is_only_get_and_cannot_use_fixture_review():
    runner, calls = public_runner()
    result = fetch_public_pr(DEFAULT_REPO, 42, allow_network=True, runner=runner)
    assert len(calls) == 5
    assert result["source"] == "github_public_readonly"
    assert_blocked("FINDINGS_REQUIRED", build_review, result)


def test_private_repo_blocked_before_reading_pr():
    runner, calls = public_runner(private=True)
    assert_blocked("PUBLIC_REPO_REQUIRED", fetch_public_pr, DEFAULT_REPO, 42, allow_network=True, runner=runner)
    assert len(calls) == 1


def test_sha_change_during_fetch_blocked():
    runner, _ = public_runner(stale=True)
    assert_blocked("STALE_HEAD_SHA", fetch_public_pr, DEFAULT_REPO, 42, allow_network=True, runner=runner)


def test_gh_error_contract_does_not_echo_auth_output():
    runner, _ = public_runner(failure=True)
    with pytest.raises(LabError) as exc:
        fetch_public_pr(DEFAULT_REPO, 42, allow_network=True, runner=runner)
    assert exc.value.code == "GH_READ_FAILED"
    assert "not exposed" not in str(exc.value)


@pytest.mark.parametrize("repo", ["--help", "../repo", "a/b/c", "a/b;echo hi"])
def test_repo_injection_blocked_before_network(repo):
    runner, calls = public_runner()
    assert_blocked("INVALID_REPO", fetch_public_pr, repo, 42, allow_network=True, runner=runner)
    assert calls == []


def test_workflow_template_is_not_an_active_publishing_workflow():
    source = (FIXTURES.parent / "templates" / "workflow.yml").read_text()
    active = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    assert "pull_request:" in active
    assert "contents: read" in active
    assert "persist-credentials: false" in active
    assert "working-directory: exercise" in active
    assert "python -m pytest -q test_checkout.py" in active
    for forbidden in ("pull_request_target:", "secrets.", "pull-requests: write", "gh pr merge", "APPROVE"):
        assert forbidden not in active


def test_malformed_gh_json_has_stable_error_code():
    runner = lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="[]")
    assert_blocked("GH_INVALID_RESPONSE", fetch_public_pr, DEFAULT_REPO, 42, allow_network=True, runner=runner)


def test_day4_notebook_cells_compile_and_keep_safe_defaults():
    path = Path(__file__).resolve().parents[1] / "materials/day4/day4_pr_document_automation.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    assert 60 <= len(cells) <= 90
    sources = ["".join(cell["source"]) for cell in cells]
    for index, cell in enumerate(cells):
        if cell["cell_type"] == "code":
            compile(sources[index], f"day4-cell-{index}", "exec")
    joined = "\n".join(sources)
    for lesson in range(1, 9):
        assert f"## {lesson}차시 " in joined
    for required in ("APPLY_REFERENCE_FIX = False", "HUMAN_CONFIRMED = False", "ALLOW_PUBLIC_GITHUB_READ = False", "RUN_CODEX_LIVE = False"):
        assert required in joined
    assert "prepare_brief(ROOT, as_of=AS_OF, tasks=tasks_my)" in joined


def test_day4_executed_notebook_completes_without_error_outputs():
    path = Path(__file__).resolve().parents[1] / "materials/day4/day4_pr_document_automation.executed.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is not None
            assert all(output["output_type"] != "error" for output in cell.get("outputs", []))


def test_bundle_allowlist_blocks_private_paths_and_secret_content(tmp_path):
    from scripts.build_day4_student_bundle import _source, _scan_content
    with pytest.raises(ValueError, match="DAY4_BUNDLE_PATH_BLOCKED"):
        _source(tmp_path, ".env")
    with pytest.raises(ValueError, match="DAY4_BUNDLE_PATH_BLOCKED"):
        _source(tmp_path, "../outside.txt")
    sample = ('sk-' + 'proj-' + 'X' * 32).encode()
    with pytest.raises(ValueError, match="DAY4_BUNDLE_SECRET_DETECTED"):
        _scan_content("sample.txt", sample)


def test_bundle_build_is_deterministic_and_keeps_source_tree(tmp_path, monkeypatch):
    import zipfile
    from scripts import build_day4_student_bundle as bundle
    monkeypatch.setattr(bundle, "REQUIRED_FILES", ("requirements-day4.txt",))
    monkeypatch.setattr(bundle, "OPTIONAL_FILES", ())
    (tmp_path / "requirements-day4.txt").write_text("pytest==8.3.5\n")
    first = bundle.build_bundle(tmp_path, tmp_path / "dist/first.zip")
    second = bundle.build_bundle(tmp_path, tmp_path / "dist/second.zip")
    assert first["sha256"] == second["sha256"]
    with zipfile.ZipFile(tmp_path / "dist/first.zip") as archive:
        assert f"{bundle.BUNDLE_ROOT}/requirements-day4.txt" in archive.namelist()
        assert f"{bundle.BUNDLE_ROOT}/README.md" in archive.namelist()
        assert f"{bundle.BUNDLE_ROOT}/BUNDLE_MANIFEST.json" in archive.namelist()
    assert (tmp_path / "requirements-day4.txt").read_text() == "pytest==8.3.5\n"


def codex_test_workspace(tmp_path, monkeypatch):
    from labs.day4.pr_review_lab import codex_review
    root = Path(__file__).resolve().parents[1]
    for relative in codex_review.INPUT_FILES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())
    monkeypatch.setattr(codex_review.shutil, "which", lambda command: "/mock/codex")
    return codex_review


def test_codex_live_requires_explicit_opt_in(tmp_path):
    from labs.day4.pr_review_lab.codex_review import run_codex_review
    calls = []
    assert_blocked("LIVE_NOT_REQUESTED", run_codex_review, tmp_path, "review.md", runner=lambda *a, **k: calls.append(a))
    assert not calls and not (tmp_path / "review.md").exists()


def test_codex_live_mock_preserves_raw_output_and_safe_flags(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    raw = "# 리뷰\n위치: checkout.py:5\n줄 번호는 사람이 검토합니다.\n"
    def runner(command, **kwargs):
        assert "--ignore-user-config" in command and "--ephemeral" in command
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert "--skip-git-repo-check" in command
        assert command[command.index("--model") + 1] == "gpt-5.6-sol"
        assert kwargs["stdout"] == subprocess.DEVNULL and kwargs["stderr"] == subprocess.DEVNULL
        assert sorted(path.name for path in kwargs["cwd"].iterdir()) == ["checkout.py", "checkout_checks.py", "review_policy.md"]
        Path(command[command.index("--output-last-message") + 1]).write_text(raw, encoding="utf-8")
        return SimpleNamespace(returncode=0)
    result = module.run_codex_review(tmp_path, "out/review.md", live=True, runner=runner)
    assert result["markdown"] == raw
    assert (tmp_path / "out/review.md").read_text() == raw
    assert result["provider_used"] == "codex_cli"
    assert result["line_references_verified"] is False
    assert result["fixture_fallback"] is False
    assert result["remote_write_performed"] is False
    assert not list((tmp_path / "out").glob(".day4-codex-*"))


def test_codex_output_overwrite_and_outside_path_blocked(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    existing = tmp_path / "existing.md"
    existing.write_text("original")
    calls = []
    runner = lambda *a, **k: calls.append(a)
    assert_blocked("OUTPUT_EXISTS", module.run_codex_review, tmp_path, existing, live=True, runner=runner)
    assert_blocked("PATH_OUTSIDE_WORKSPACE", module.run_codex_review, tmp_path, "../outside.md", live=True, runner=runner)
    assert existing.read_text() == "original" and not calls


def test_codex_timeout_is_named_and_never_falls_back(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], output="do not print", stderr="account log")
    assert_blocked("CODEX_TIMEOUT", module.run_codex_review, tmp_path, "review.md", live=True, runner=runner)
    assert not (tmp_path / "review.md").exists()


def test_codex_output_directory_permission_failure_is_named(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    calls = []
    original_mkdir = Path.mkdir

    def mkdir(path, *args, **kwargs):
        if path == tmp_path / "denied":
            raise PermissionError("private operating-system detail")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)
    with pytest.raises(LabError) as error:
        module.run_codex_review(tmp_path, "denied/review.md", live=True,
                                runner=lambda *args, **kwargs: calls.append(args))
    assert error.value.code == "CODEX_FILE_ACCESS_FAILED"
    assert "private operating-system detail" not in str(error.value)
    assert not calls and not (tmp_path / "denied/review.md").exists()


def test_codex_auth_or_model_failure_hides_raw_logs(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="account info", stderr="sensitive debug")
    with pytest.raises(LabError) as error:
        module.run_codex_review(tmp_path, "review.md", live=True, runner=runner)
    assert error.value.code == "CODEX_EXEC_FAILED"
    assert "sensitive" not in str(error.value) and "account info" not in str(error.value)
    assert not (tmp_path / "review.md").exists()


def test_codex_missing_final_message_is_not_success(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    assert_blocked("CODEX_OUTPUT_MISSING", module.run_codex_review, tmp_path, "review.md", live=True,
                   runner=lambda *args, **kwargs: SimpleNamespace(returncode=0))


def test_codex_sensitive_output_is_not_saved(tmp_path, monkeypatch):
    module = codex_test_workspace(tmp_path, monkeypatch)
    def runner(command, **kwargs):
        Path(command[command.index("--output-last-message") + 1]).write_text('sk-' + 'proj-' + 'X' * 32)
        return SimpleNamespace(returncode=0)
    assert_blocked("CODEX_OUTPUT_SENSITIVE", module.run_codex_review, tmp_path, "review.md", live=True, runner=runner)
    assert not (tmp_path / "review.md").exists()
