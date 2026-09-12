"""Small, explicit boundaries for reviewing a PR; no remote write implementation."""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DEFAULT_REPO = "training-example/checkout-demo"
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA_PATTERN = re.compile(r"[a-f0-9]{40}\Z")
MAX_FILES = 30
MAX_PATCH_BYTES = 200_000


class LabError(ValueError):
    """Expected failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

    def as_dict(self) -> dict[str, str]:
        return {"status": "BLOCKED", "error_code": self.code, "message": str(self)}


def workspace_path(workspace: Path | str, path: Path | str) -> Path:
    root = Path(workspace).resolve()
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved == root or not resolved.is_relative_to(root):
        raise LabError("PATH_OUTSIDE_WORKSPACE", "작업 폴더 안의 하위 경로를 지정하세요.")
    return resolved


def _repo(repo: str) -> str:
    if not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo):
        raise LabError("INVALID_REPO", "저장소는 owner/repository 형식이어야 합니다.")
    if any(part in {".", ".."} for part in repo.split("/")):
        raise LabError("INVALID_REPO", "저장소 이름에 상대 경로를 사용할 수 없습니다.")
    return repo.lower()


def _number(number: int) -> int:
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise LabError("INVALID_PR_NUMBER", "PR 번호는 양의 정수여야 합니다.")
    return number


def _relative_file(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        raise LabError("INVALID_DIFF_PATH", "변경 파일 경로를 확인하세요.")
    value = PurePosixPath(path)
    if not value.parts or value.is_absolute() or ".." in value.parts or ":" in path:
        raise LabError("INVALID_DIFF_PATH", "변경 파일은 저장소 내부 상대 경로여야 합니다.")
    return path


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _snapshot_digest(snapshot: dict) -> str:
    # Review history changes after posting; it must not change the same review's identity.
    return _digest({key: value for key, value in snapshot.items() if key != "existing_reviews"})


def changed_lines(patch: str) -> set[int]:
    """Return RIGHT-side added line numbers, not old GitHub diff positions."""
    added: set[int] = set()
    line = 0
    for row in patch.splitlines():
        match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", row)
        if match:
            line = int(match.group(1))
        elif row.startswith("+") and not row.startswith("+++"):
            if line:
                added.add(line)
                line += 1
        elif line and not row.startswith(("-", "\\")):
            line += 1
    return added


def validate_snapshot(snapshot: dict, *, expected_repo: str, expected_pr: int) -> dict:
    """Validate destination, revision, diff budget, and supported PR state."""
    expected = _repo(expected_repo)
    number = _number(expected_pr)
    if not isinstance(snapshot, dict):
        raise LabError("INVALID_SNAPSHOT", "PR 입력은 객체여야 합니다.")
    if _repo(snapshot.get("repo", "")) != expected or _repo(snapshot.get("base_repo", "")) != expected:
        raise LabError("REPO_MISMATCH", "지정한 저장소와 PR 대상 저장소가 다릅니다.")
    if _number(snapshot.get("number")) != number:
        raise LabError("PR_MISMATCH", "지정한 번호와 PR 번호가 다릅니다.")
    if not isinstance(snapshot.get("url"), str) or snapshot["url"].lower() != f"https://github.com/{expected}/pull/{number}":
        raise LabError("PR_URL_MISMATCH", "PR URL과 대상 저장소·번호가 일치하지 않습니다.")
    for key in ("base_sha", "head_sha"):
        if not isinstance(snapshot.get(key), str) or not SHA_PATTERN.fullmatch(snapshot[key]):
            raise LabError("INVALID_SHA", "40자리 commit SHA가 필요합니다.")
    if snapshot.get("state") != "open":
        raise LabError("PR_NOT_OPEN", "열려 있는 PR만 준비할 수 있습니다.")
    files = snapshot.get("files")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise LabError("FILE_LIMIT", "변경 파일은 1~30개인 작은 PR을 사용하세요.")
    paths = set()
    patch_bytes = 0
    for item in files:
        if not isinstance(item, dict):
            raise LabError("INVALID_DIFF", "변경 파일 형식이 잘못되었습니다.")
        path = _relative_file(item.get("path", ""))
        if path in paths:
            raise LabError("DUPLICATE_DIFF_PATH", "변경 파일 경로가 중복되었습니다.")
        paths.add(path)
        patch = item.get("patch")
        if not isinstance(patch, str) or not patch.startswith("@@ "):
            raise LabError("PATCH_UNAVAILABLE", "binary·생략된 diff는 이 실습에서 지원하지 않습니다.")
        patch_bytes += len(patch.encode("utf-8"))
    if patch_bytes > MAX_PATCH_BYTES:
        raise LabError("PATCH_LIMIT", "diff가 너무 큽니다. 더 작은 PR로 나누세요.")
    return snapshot


def load_fixture() -> dict:
    snapshot = json.loads((FIXTURES / "pr.json").read_text(encoding="utf-8"))
    return validate_snapshot(snapshot, expected_repo=DEFAULT_REPO, expected_pr=42)


def prepare_exercise(workspace: Path | str, output: Path | str) -> dict:
    """Create a fresh learner folder. Never overwrite a learner's existing edits."""
    folder = workspace_path(workspace, output)
    if folder.exists():
        raise LabError("EXERCISE_EXISTS", "기존 수정 내용을 보호합니다. 새 폴더명을 지정하세요.")
    folder.mkdir(parents=True)
    for source, target in (("checkout.py", "checkout.py"), ("checkout_checks.py", "test_checkout.py"),
                           ("checkout_before.py", "checkout_before.py"), ("checkout_solution.py", "reference_solution.py")):
        (folder / target).write_text((FIXTURES / source).read_text(encoding="utf-8"), encoding="utf-8")
    (folder / ".day4-public-exercise").write_text("public synthetic example\n", encoding="utf-8")
    return {"status": "PREPARED", "exercise_dir": str(folder), "edit_file": str(folder / "checkout.py")}


def check_exercise(workspace: Path | str, exercise_dir: Path | str) -> dict:
    """Run explicitly requested local learner tests, not fetched PR code."""
    folder = workspace_path(workspace, exercise_dir)
    for name in (".day4-public-exercise", "checkout.py", "test_checkout.py"):
        path = workspace_path(workspace, folder / name)
        if not path.is_file() or not path.is_relative_to(folder):
            raise LabError("INVALID_EXERCISE", "prepare로 생성한 실습 폴더가 필요합니다.")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--override-ini=addopts=", "test_checkout.py"],
            cwd=folder, capture_output=True, text=True, timeout=30, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise LabError("TEST_TIMEOUT", "테스트가 30초 안에 끝나지 않았습니다.") from exc
    return {"status": "PASSED" if result.returncode == 0 else "FAILED", "exit_code": result.returncode,
            "command": "python -m pytest -q test_checkout.py", "output": result.stdout + result.stderr}


def build_review(snapshot: dict, findings: list[dict] | None = None, *, provider: str = "fixture") -> dict:
    validate_snapshot(snapshot, expected_repo=snapshot.get("repo", ""), expected_pr=snapshot.get("number"))
    if findings is None:
        if _snapshot_digest(snapshot) != _snapshot_digest(load_fixture()):
            raise LabError("FINDINGS_REQUIRED", "실제 PR에는 직접 검토한 의견을 입력해야 합니다.")
        findings = json.loads((FIXTURES / "findings.json").read_text(encoding="utf-8"))
    if not isinstance(findings, list) or len(findings) > 30:
        raise LabError("INVALID_FINDINGS", "리뷰 의견은 최대 30개 목록이어야 합니다.")
    changed = {item["path"]: changed_lines(item["patch"]) for item in snapshot["files"]}
    sections = ["# 코드 리뷰 초안", "", f"대상: `{snapshot['repo']}#{snapshot['number']}`",
                f"기준 commit: `{snapshot['head_sha']}`", f"리뷰 출처: `{provider}`", "",
                "아래 내용은 게시 전 검토용입니다. 테스트와 사용자 영향을 사람이 확인합니다.", ""]
    for item in findings:
        if not isinstance(item, dict) or item.get("severity") not in {"P0", "P1", "P2", "P3"}:
            raise LabError("INVALID_FINDING", "리뷰 중요도와 형식을 확인하세요.")
        if item.get("path") not in changed or item.get("line") not in changed[item["path"]]:
            raise LabError("FINDING_NOT_IN_DIFF", "의견은 실제 추가·변경 줄에 연결되어야 합니다.")
        if any(not isinstance(item.get(key), str) or not item[key].strip()
               for key in ("title", "impact", "reproduction", "suggestion", "test")):
            raise LabError("INCOMPLETE_FINDING", "영향·재현·최소 수정·관련 테스트를 모두 작성하세요.")
        sections.extend([f"## [{item['severity']}] {item['title']}", "",
            f"- 위치: `{item['path']}:{item['line']}`", f"- 사용자 영향: {item['impact']}",
            f"- 재현 조건: `{item['reproduction']}`", f"- 최소 수정: {item['suggestion']}",
            f"- 확인 테스트: `{item['test']}`", ""])
    if not findings:
        sections += ["확인된 의견 없음. 버그가 없다는 보증이나 merge 승인이 아닙니다.", ""]
    review = {"repo": snapshot["repo"], "number": snapshot["number"], "head_sha": snapshot["head_sha"],
              "snapshot_sha256": _snapshot_digest(snapshot), "provider": provider, "findings": findings,
              "markdown": "\n".join(sections)}
    review["review_sha256"] = _digest(review)
    return review


def _review_matches(snapshot: dict, review: dict) -> None:
    original = {key: value for key, value in review.items() if key != "review_sha256"}
    if review.get("review_sha256") != _digest(original):
        raise LabError("REVIEW_CHANGED", "리뷰 내용이 바뀌었습니다. 다시 확인하세요.")
    if (review.get("repo"), review.get("number"), review.get("head_sha"), review.get("snapshot_sha256")) != (
        snapshot["repo"], snapshot["number"], snapshot["head_sha"], _snapshot_digest(snapshot)
    ):
        raise LabError("REVIEW_TARGET_MISMATCH", "리뷰가 생성된 PR 입력과 현재 입력이 다릅니다.")


def approve_preview(snapshot: dict, review: dict, *, approved: bool, reviewer: str) -> dict:
    """An explicit human choice, bound to both revision and exact reviewed content."""
    validate_snapshot(snapshot, expected_repo=review.get("repo", ""), expected_pr=review.get("number"))
    _review_matches(snapshot, review)
    if approved is not True or not isinstance(reviewer, str) or not reviewer.strip():
        raise LabError("HUMAN_APPROVAL_REQUIRED", "리뷰 내용을 읽고 검토자와 승인 여부를 명시하세요.")
    return {"approved": True, "reviewer": reviewer.strip(), "repo": snapshot["repo"],
            "number": snapshot["number"], "head_sha": snapshot["head_sha"],
            "review_sha256": review["review_sha256"], "scope": "payload_preview_only"}


def preview_publication(snapshot: dict, review: dict, approval: dict | None, *, current_head_sha: str,
                        existing_reviews: list[dict] | None = None) -> dict:
    """Build a COMMENT payload; no API call. Repeated/stale publication is blocked."""
    validate_snapshot(snapshot, expected_repo=review.get("repo", ""), expected_pr=review.get("number"))
    _review_matches(snapshot, review)
    if current_head_sha != snapshot["head_sha"]:
        raise LabError("STALE_HEAD_SHA", "PR에 새 commit이 생겼습니다. 새 diff로 다시 리뷰하세요.")
    if not approval or approval.get("approved") is not True:
        raise LabError("HUMAN_APPROVAL_REQUIRED", "게시용 내용 미리보기에 사람의 명시적인 확인이 필요합니다.")
    expected = (snapshot["repo"], snapshot["number"], snapshot["head_sha"], review["review_sha256"], "payload_preview_only")
    actual = tuple(approval.get(key) for key in ("repo", "number", "head_sha", "review_sha256", "scope"))
    if actual != expected or not approval.get("reviewer"):
        raise LabError("APPROVAL_MISMATCH", "승인한 저장소·PR·commit·리뷰 내용이 일치하지 않습니다.")
    marker = f"<!-- day4-review:{review['review_sha256']} -->"
    existing = snapshot.get("existing_reviews", []) if existing_reviews is None else existing_reviews
    if not isinstance(existing, list) or any(not isinstance(row, dict) for row in existing):
        raise LabError("INVALID_REVIEW_HISTORY", "기존 리뷰 이력 형식을 확인하세요.")
    if any(marker in str(row.get("body", "")) for row in existing):
        raise LabError("DUPLICATE_REVIEW", "같은 리뷰가 이미 있습니다. 다시 게시하지 않습니다.")
    return {"status": "PREVIEW_ONLY", "remote_write_performed": False,
            "method": "POST", "endpoint": f"/repos/{snapshot['repo']}/pulls/{snapshot['number']}/reviews",
            "payload": {"commit_id": snapshot["head_sha"], "event": "COMMENT",
                        "body": review["markdown"] + "\n\n" + marker},
            "dedupe_marker": marker, "reviewer": approval["reviewer"]}


def render_outputs(workspace: Path | str, output: Path | str, snapshot: dict, review: dict,
                   preview: dict | None = None, test_result: dict | None = None) -> dict[str, str]:
    """Escape all PR text before HTML display. No scripts, external fonts, or trackers."""
    _review_matches(snapshot, review)
    folder = workspace_path(workspace, output)
    folder.mkdir(parents=True, exist_ok=True)
    diff = "\n\n".join(f"diff --git a/{row['path']} b/{row['path']}\n{row['patch']}" for row in snapshot["files"])
    payload = json.dumps(preview or {"status": "AWAITING_HUMAN_REVIEW"}, ensure_ascii=False, indent=2)
    page = """<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PR 리뷰 작업대</title><style>body{font:18px/1.65 -apple-system,BlinkMacSystemFont,'Malgun Gothic',sans-serif;background:#f5f5f5;color:#111;max-width:1160px;margin:40px auto;padding:0 24px}h1{font-size:38px}h2{font-size:24px}section{background:#fff;border:1px solid #ddd;border-radius:12px;padding:24px;margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.65 ui-monospace,monospace}.tag{background:#111;color:#fff;padding:6px 12px;border-radius:5px;display:inline-block}p{max-width:900px}</style>
<h1>PR 리뷰 작업대</h1><p class="tag">로컬 미리보기 · GitHub 게시 없음</p>"""
    for title, text in (("01 · 리뷰 기준 PR 변경 코드", diff), ("02 · 현재 로컬 작업 코드의 테스트", (test_result or {}).get("output", "실습 폴더에서 테스트를 실행하세요.")),
                        ("03 · 리뷰 초안", review["markdown"]), ("04 · 게시용 내용 미리보기", payload)):
        page += f"<section><h2>{title}</h2><pre>{html.escape(text)}</pre></section>"
    page += "<p>fixture는 수업용 정답 예시입니다. 실제 PR·Codex 실행 결과와 구분합니다. 로컬 수정 후 테스트 결과는 위 PR commit의 CI 결과가 아닙니다. 이 화면은 원본 리뷰와 수정 후 결과를 비교하는 작업대입니다.</p></html>"
    contents = {"review.md": review["markdown"], "changes.diff": diff, "review.html": page,
                "publication_preview.json": payload, "snapshot.json": json.dumps(snapshot, ensure_ascii=False, indent=2),
                "review.json": json.dumps(review, ensure_ascii=False, indent=2)}
    if test_result:
        contents["test_result.txt"] = test_result["output"]
    for name, content in contents.items():
        target = workspace_path(workspace, folder / name)
        if not target.is_relative_to(folder):
            raise LabError("PATH_OUTSIDE_WORKSPACE", "결과 파일 링크가 출력 폴더 밖을 가리킵니다.")
        target.write_text(content, encoding="utf-8")
    return {name: str(folder / name) for name in contents}


def _gh_json(endpoint: str, *, runner: Callable = subprocess.run) -> Any:
    try:
        result = runner(["gh", "api", "--method", "GET", "--hostname", "github.com", endpoint], capture_output=True, text=True,
                        timeout=30, check=False)
    except FileNotFoundError as exc:
        raise LabError("GH_NOT_INSTALLED", "선택 실습에는 GitHub CLI가 필요합니다.") from exc
    except subprocess.TimeoutExpired as exc:
        raise LabError("GH_TIMEOUT", "GitHub 읽기 요청 시간이 초과되었습니다.") from exc
    if result.returncode:
        # gh stderr may include identifying information; never echo it to notebooks.
        raise LabError("GH_READ_FAILED", "로그인·저장소 접근권한·API 요청 한도를 확인하세요.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LabError("GH_INVALID_RESPONSE", "GitHub 응답이 JSON 형식이 아닙니다.") from exc


def fetch_public_pr(repo: str, number: int, *, allow_network: bool = False,
                    runner: Callable = subprocess.run) -> dict:
    """Opt-in GET-only adapter. Never checks out, executes, or publishes fetched code."""
    repo = _repo(repo)
    number = _number(number)
    if allow_network is not True:
        raise LabError("NETWORK_OPT_IN_REQUIRED", "공개 PR 읽기는 allow_network=True로 직접 선택하세요.")
    metadata = _gh_json(f"repos/{repo}", runner=runner)
    if not isinstance(metadata, dict):
        raise LabError("GH_INVALID_RESPONSE", "저장소 정보 형식을 확인하세요.")
    if metadata.get("private") is not False or metadata.get("visibility", "public") != "public":
        raise LabError("PUBLIC_REPO_REQUIRED", "수업에서는 공개 저장소만 사용합니다.")
    pull = _gh_json(f"repos/{repo}/pulls/{number}", runner=runner)
    if not isinstance(pull, dict) or any(not isinstance(pull.get(key), dict) for key in ("base", "head")):
        raise LabError("GH_INVALID_RESPONSE", "PR 정보 형식을 확인하세요.")
    if not isinstance(pull.get("changed_files"), int) or not 0 < pull["changed_files"] <= MAX_FILES:
        raise LabError("FILE_LIMIT", "변경 파일 1~30개인 공개 PR을 선택하세요.")
    files = _gh_json(f"repos/{repo}/pulls/{number}/files?per_page=100", runner=runner)
    reviews = _gh_json(f"repos/{repo}/pulls/{number}/reviews?per_page=100", runner=runner)
    if not isinstance(files, list) or len(files) != pull["changed_files"] or any(not isinstance(row, dict) for row in files):
        raise LabError("INCOMPLETE_DIFF", "변경 파일 목록이 누락되었습니다.")
    if not isinstance(reviews, list) or len(reviews) >= 100 or any(not isinstance(row, dict) for row in reviews):
        raise LabError("REVIEW_HISTORY_LIMIT", "리뷰 100개 이상인 PR은 이 실습에서 지원하지 않습니다.")
    latest = _gh_json(f"repos/{repo}/pulls/{number}", runner=runner)
    if not isinstance(latest, dict) or not isinstance(latest.get("head"), dict):
        raise LabError("GH_INVALID_RESPONSE", "최신 PR 정보 형식을 확인하세요.")
    if latest.get("head", {}).get("sha") != pull.get("head", {}).get("sha"):
        raise LabError("STALE_HEAD_SHA", "읽는 동안 PR commit이 변경되었습니다. 다시 읽어 주세요.")
    if latest.get("state") != "open":
        raise LabError("PR_NOT_OPEN", "읽는 동안 PR이 닫혔습니다.")
    snapshot = {"source": "github_public_readonly", "repo": repo, "number": number,
        "title": pull.get("title", ""), "state": pull.get("state"), "url": pull.get("html_url"),
        "base_repo": (pull["base"].get("repo") or {}).get("full_name", ""),
        "base_sha": pull.get("base", {}).get("sha"), "head_sha": pull.get("head", {}).get("sha"),
        "files": [{"path": row.get("filename"), "status": row.get("status"), "patch": row.get("patch")} for row in files],
        "existing_reviews": [{"body": row.get("body", ""), "commit_id": row.get("commit_id")} for row in reviews]}
    return validate_snapshot(snapshot, expected_repo=repo, expected_pr=number)
