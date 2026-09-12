"""Build a portable, explicit-allowlist Day 4 student package without secrets."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = "llm-agent-workflow-day4"
DEFAULT_DESTINATION = ROOT / "dist/day4-student-code-bundle.zip"
FIXED_ZIP_TIME = (2026, 9, 12, 0, 0, 0)

# Student runtime only. No private inputs, old course files, live workflows,
# authoring-runtime builders, QA images, or local dependency directories.
REQUIRED_FILES = (
    "AGENTS.md",
    "requirements-day4.txt",
    "scripts/build_day4_notebook.py",
    "scripts/build_day4_student_bundle.py",
    "materials/day4/day4_pr_document_automation.ipynb",
    "materials/day4/day4_pr_document_automation.executed.ipynb",
    "materials/day4/2026_Day4_수강생_실습가이드.md",
    "materials/day4/실습_단계별_길잡이.md",
    "materials/day5/업무자동화_프로젝트_선택가이드.md",
    "materials/day4/pr_lab_contract.md",
    "materials/day4/excel_lab_contract.md",
    "materials/day4/document_lab_contract.md",
    "materials/day4/Codex_실행사례_및_검증.md",
    "materials/day4/공식자료_및_이미지_출처.md",
    "materials/day4/아키텍처.md",
    "assets/components/day4/codex-live-review.raw.md",
    "assets/components/day4/codex-live-review.html",
    "tests/test_day4_pr_review_lab.py",
    "tests/test_day4_excel_lab.py",
    "tests/test_day4_document_lab.py",
    "labs/day4/pr_review_lab/__init__.py",
    "labs/day4/pr_review_lab/__main__.py",
    "labs/day4/pr_review_lab/service.py",
    "labs/day4/pr_review_lab/codex_review.py",
    "labs/day4/pr_review_lab/review_policy.md",
    "labs/day4/pr_review_lab/fixtures/checkout.py",
    "labs/day4/pr_review_lab/fixtures/checkout_before.py",
    "labs/day4/pr_review_lab/fixtures/checkout_checks.py",
    "labs/day4/pr_review_lab/fixtures/checkout_solution.py",
    "labs/day4/pr_review_lab/fixtures/pr.json",
    "labs/day4/pr_review_lab/fixtures/findings.json",
    "labs/day4/pr_review_lab/templates/workflow.yml",
    "labs/day4/pr_review_lab/templates/pull_request_template.md",
    "labs/day4/office_lab/documents/__init__.py",
    "labs/day4/office_lab/documents/resume_lab.py",
    "labs/day4/office_lab/documents/career_facts.json",
    "labs/day4/office_lab/sheets/student_excel.py",
    "labs/day4/office_lab/sheets/wbs_tasks.json",
    "labs/day4/office_lab/sheets/exam_sample.json",
    "labs/day4/office_lab/sheets/requirements.txt",
    "labs/day4/office_lab/google_sheets/Code.gs",
    "labs/day4/office_lab/google_sheets/appsscript.json",
    "labs/day4/office_lab/google_sheets/README.md",
    "labs/day4/office_lab/google_sheets/test_code.mjs",
    "labs/day4/office_lab/presentations/brief_data.py",
    "labs/day4/office_lab/presentations/student_ppt.mjs",
    "labs/day4/office_lab/presentations/package.json",
    "labs/day4/office_lab/presentations/project_brief.json",
    "outputs/day4-document-automation/WBS_Gantt.xlsx",
    "outputs/day4-document-automation/Exam_Grading.xlsx",
    "outputs/day4-document-automation/Resume_Before.docx",
    "outputs/day4-document-automation/Resume_After.docx",
    "outputs/day4-document-automation/Project_Brief.pptx",
    "outputs/day4-document-automation/Project_Brief.pdf",
    "outputs/day4-document-automation/Project_Brief_student.pptx",
    "outputs/day4-document-automation/Project_Brief_student.pdf",
)

# These are optional while the lecture deck is being rendered. The manifest
# records omissions rather than claiming that an absent deck was packaged.
OPTIONAL_FILES = (
    "materials/day5/미니프로젝트_사전안내.md",
    "materials/day5/개선기록_템플릿.md",
    "slides/IPA_LLM_Agent_업무자동화_Day4_2026_PR_DOCUMENT.pptx",
    "output/pdf/IPA_LLM_Agent_업무자동화_Day4_2026_PR_DOCUMENT.pdf",
)

FORBIDDEN_PARTS = {".git", ".env", ".venv", ".venv312", "node_modules", "__pycache__", ".pytest_cache", "private", "qa", "draft"}
SECRET_PATTERNS = (
    re.compile(rb"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"lsv2_pt_[A-Za-z0-9_-]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

STUDENT_README = """# 4주차 PR 리뷰와 문서 자동화

## 시작

압축을 풀고 이 README가 있는 폴더 전체를 VS Code로 엽니다. Notebook만 따로 복사하지 않습니다.

1. Python 3.12 권장. 본인의 가상환경을 선택합니다.
2. 아래 명령을 터미널에서 실행합니다.
3. Notebook을 위에서부터 실행하고 차시별 ‘직접 수정 구간’을 진행합니다.

```bash
python -m pip install -r requirements-day4.txt
python -m jupyter lab materials/day4/day4_pr_document_automation.ipynb
```

Mac에서는 환경에 따라 python3을 사용합니다. Windows는 `py -3.12 -m venv .venv` 다음
`.venv\\Scripts\\python.exe -m pip install -r requirements-day4.txt`처럼 Python을 직접 지정할 수 있습니다.

PPT 생성은 Node.js 설치 후 다음 명령을 한 번 실행합니다.

```bash
npm install --prefix labs/day4/office_lab/presentations
```

## 자료

- [수강생 실습 가이드](materials/day4/2026_Day4_수강생_실습가이드.md)
- [파일·셀·오류 복구 단계 안내](materials/day4/실습_단계별_길잡이.md)
- [프로젝트 36개 선택 예시](materials/day5/업무자동화_프로젝트_선택가이드.md)
- [실습 Notebook](materials/day4/day4_pr_document_automation.ipynb)
- [실행 결과 비교용 Notebook](materials/day4/day4_pr_document_automation.executed.ipynb)
- [PR 리뷰와 CI](materials/day4/pr_lab_contract.md)
- [Excel WBS와 채점](materials/day4/excel_lab_contract.md)
- [Word와 PPT](materials/day4/document_lab_contract.md)
- 참고 문서: `outputs/day4-document-automation/`

Excel 템플릿은 WBS 14개 작업, 시험 40문항·28명 합성 데이터입니다.
`outputs/day4-document-automation/`의 파일은 실습 코드가 읽는 양식이므로 폴더 구조를 유지합니다.
기본 과정은 API key·LLM 계정·GitHub 게시 없이 실행됩니다. Codex·Claude 대화 과제는 본인 계정에서 선택합니다.

선택 Codex 실시간 리뷰는 CLI 로그인과 계정 사용량이 필요합니다. 공개 예시 세 파일을 읽어
새 Markdown으로 저장하며 실패하면 fixture로 바꾸지 않습니다.

```bash
python -m labs.day4.pr_review_lab.codex_review --live --output output/my-review.md
```

`--live`를 빼면 호출하지 않습니다. 모델이 반환한 파일 줄 번호와 재현 입력을 직접 검증합니다.

## 내 결과

실행할 때마다 `output/day4-notebook-runs/날짜_실행ID/`에 새 파일을 만듭니다.
마지막의 `index.html`에서 리뷰·Excel·Word·PPT를 확인합니다.
처음 결제 코드는 의도적으로 테스트 4개가 실패합니다. `checkout.py`를 직접 수정하세요.
자동 수정은 기본으로 꺼져 있고, 별도 참고 구현의 테스트 통과와 내 코드의 통과를 구분합니다.

## 테스트

```bash
python -m pytest -q tests/test_day4_pr_review_lab.py tests/test_day4_excel_lab.py tests/test_day4_document_lab.py
```

실제 Google Sheets 성적표·회사 데이터·비밀키는 포함하지 않았습니다. Apps Script는 본인 소유의 합성 연습 시트에만 적용합니다.
GitHub Actions 파일은 `templates/` 안의 비활성 예시이며, 사람이 개인 저장소에 복사해야 실행됩니다.

`BUNDLE_MANIFEST.json`에 실제 포함 파일과 선택 자료의 누락 여부를 기록했습니다.
"""

STUDENT_GITIGNORE = """.env
.env.*
.venv/
.venv312/
node_modules/
__pycache__/
.pytest_cache/
output/
dist/
"""


def _source(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or any(part.lower() in FORBIDDEN_PARTS or part.startswith(".env") for part in path.parts):
        raise ValueError("DAY4_BUNDLE_PATH_BLOCKED")
    candidate = root / path
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("DAY4_BUNDLE_PATH_OUTSIDE_WORKSPACE")
    if not resolved.is_file():
        raise FileNotFoundError(f"DAY4_BUNDLE_FILE_MISSING:{relative}")
    return resolved


def _scan_content(name: str, content: bytes) -> None:
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        raise ValueError(f"DAY4_BUNDLE_SECRET_DETECTED:{Path(name).name}")
    if Path(name).suffix.lower() in {".xlsx", ".docx", ".pptx"}:
        with zipfile.ZipFile(io.BytesIO(content)) as package:
            for info in package.infolist():
                if info.file_size > 20_000_000:
                    raise ValueError("DAY4_BUNDLE_EMBEDDED_PART_TOO_LARGE")
                if info.filename.endswith((".xml", ".rels", ".txt")):
                    if any(pattern.search(package.read(info)) for pattern in SECRET_PATTERNS):
                        raise ValueError(f"DAY4_BUNDLE_SECRET_DETECTED:{Path(name).name}")


def selected_files(root: Path = ROOT) -> list[tuple[str, Path]]:
    root = root.resolve()
    selected = [(name, _source(root, name)) for name in REQUIRED_FILES]
    for name in OPTIONAL_FILES:
        if (root / name).exists():
            selected.append((name, _source(root, name)))
    return sorted(selected)


def _write(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(f"{BUNDLE_ROOT}/{name}", date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def build_bundle(root: Path = ROOT, destination: Path = DEFAULT_DESTINATION) -> dict:
    root, destination = root.resolve(), destination.resolve()
    if not destination.is_relative_to(root) or destination.suffix != ".zip":
        raise ValueError("DAY4_BUNDLE_DESTINATION_BLOCKED")
    entries = {"README.md": STUDENT_README.encode("utf-8"), ".gitignore": STUDENT_GITIGNORE.encode("utf-8")}
    for name, path in selected_files(root):
        content = path.read_bytes()
        _scan_content(name, content)
        entries[name] = content
    manifest = {
        "bundle": BUNDLE_ROOT,
        "file_count": len(entries),
        "default_network": False,
        "automatic_publish": False,
        "scope": "public synthetic Day4 student labs and reference documents",
        "excluded": ["secrets", "private student grades", "node_modules", "QA", "other course files"],
        "optional_not_included": [name for name in OPTIONAL_FILES if name not in entries],
        "files": [{"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
                  for name, content in sorted(entries.items())],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in sorted(entries.items()):
            _write(archive, name, content)
        _write(archive, "BUNDLE_MANIFEST.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    data = buffer.getvalue()
    destination.write_bytes(data)
    return {"status": "SUCCESS", "archive": str(destination.relative_to(root)),
            "file_count": len(entries), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "optional_not_included": manifest["optional_not_included"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    output = args.out if args.out.is_absolute() else ROOT / args.out
    print(json.dumps(build_bundle(ROOT, output), ensure_ascii=False, indent=2))
