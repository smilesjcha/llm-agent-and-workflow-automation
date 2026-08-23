"""Deterministic diff parsing and review baseline for Day 3.

The rule-based reviewer is intentionally small. It gives students a stable
baseline before an optional LLM adapter is added, and every finding must map to
an added line in the submitted diff.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from pydantic import ValidationError

from src.course_services.contracts import ReviewFinding, ReviewReport


HUNK_HEADER = re.compile(
    r"^@@\s+-(?P<old_start>\d+)(?:,(?P<old_len>\d+))?\s+"
    r"\+(?P<new_start>\d+)(?:,(?P<new_len>\d+))?\s+@@"
)


@dataclass(frozen=True)
class AddedLine:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class ParsedDiff:
    changed_paths: tuple[str, ...]
    added_lines: tuple[AddedLine, ...]


def _normalize_diff_path(raw_path: str) -> str | None:
    value = raw_path.strip().split("\t", 1)[0]
    if value == "/dev/null":
        return None
    if value.startswith("b/"):
        value = value[2:]
    if value.startswith("/") or ".." in value.split("/"):
        raise ValueError("DIFF_PATH_BLOCKED")
    return value


def parse_unified_diff(diff_text: str) -> ParsedDiff:
    """Parse new-file line numbers without reading arbitrary repository files."""

    if not diff_text.strip():
        raise ValueError("EMPTY_DIFF")

    changed_paths: list[str] = []
    added_lines: list[AddedLine] = []
    current_path: str | None = None
    old_line: int | None = None
    new_line: int | None = None
    saw_hunk = False

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            current_path = _normalize_diff_path(raw_line[4:])
            if current_path and current_path not in changed_paths:
                changed_paths.append(current_path)
            old_line = None
            new_line = None
            continue

        match = HUNK_HEADER.match(raw_line)
        if match:
            if not current_path:
                raise ValueError("HUNK_WITHOUT_TARGET_PATH")
            old_line = int(match.group("old_start"))
            new_line = int(match.group("new_start"))
            saw_hunk = True
            continue

        if old_line is None or new_line is None or current_path is None:
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            added_lines.append(AddedLine(current_path, new_line, raw_line[1:]))
            new_line += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            old_line += 1
        elif raw_line.startswith(" "):
            old_line += 1
            new_line += 1
        elif raw_line.startswith("\\ No newline"):
            continue

    if not saw_hunk:
        raise ValueError("UNIFIED_DIFF_HUNK_REQUIRED")
    return ParsedDiff(tuple(changed_paths), tuple(added_lines))


def _finding(
    line: AddedLine,
    *,
    severity: str,
    title: str,
    body: str,
    suggestion: str,
    confidence: float,
    rule_id: str,
) -> ReviewFinding:
    return ReviewFinding(
        path=line.path,
        line=line.line,
        severity=severity,
        title=title,
        body=body,
        evidence=line.text.strip()[:180] or "빈 추가 라인",
        suggestion=suggestion,
        confidence=confidence,
        rule_id=rule_id,
    )


def deterministic_findings(lines: Iterable[AddedLine]) -> list[ReviewFinding]:
    """Create a reproducible review baseline focused on consequential risks."""

    findings: list[ReviewFinding] = []
    for line in lines:
        code = line.text
        if re.search(r"\b(eval|exec)\s*\(", code):
            findings.append(
                _finding(
                    line,
                    severity="P0",
                    title="검증되지 않은 문자열이 코드로 실행될 수 있음",
                    body="입력 경로에 따라 임의 코드 실행으로 이어질 수 있습니다.",
                    suggestion="허용된 명령이나 파서만 호출하는 명시적 registry로 교체하세요.",
                    confidence=0.99,
                    rule_id="unsafe-dynamic-execution",
                )
            )
        if re.search(r"\bsubprocess\.(run|Popen)\(.*shell\s*=\s*True", code):
            findings.append(
                _finding(
                    line,
                    severity="P0",
                    title="shell=True가 명령 주입 경계를 우회함",
                    body="외부 입력이 포함되면 shell 확장으로 예상하지 못한 명령이 실행될 수 있습니다.",
                    suggestion="인자 배열과 allowlist를 사용하고 shell 실행을 제거하세요.",
                    confidence=0.98,
                    rule_id="shell-command-injection",
                )
            )
        if re.search(r"^\s*except\s+(Exception\s*)?:\s*$", code) or re.search(
            r"^\s*except\s*:\s*$", code
        ):
            findings.append(
                _finding(
                    line,
                    severity="P2",
                    title="넓은 예외 처리가 실패 계약을 지움",
                    body="인증 오류와 입력 오류가 같은 경로로 숨겨져 복구 결정을 내릴 수 없습니다.",
                    suggestion="복구 가능한 예외만 잡고 구조화된 error_code를 반환하세요.",
                    confidence=0.94,
                    rule_id="broad-exception-boundary",
                )
            )
        if re.search(r"\brequests\.(post|put|patch|delete)\(", code) and not re.search(
            r"dry_run|human_approved|approval", code, flags=re.IGNORECASE
        ):
            findings.append(
                _finding(
                    line,
                    severity="P1",
                    title="외부 쓰기 전에 사람 승인 경계가 보이지 않음",
                    body="재시도나 잘못된 대상 선택이 실제 게시·수정으로 이어질 수 있습니다.",
                    suggestion="dry-run payload, 대상 확인, human_approved 조건을 쓰기 호출 앞에 두세요.",
                    confidence=0.91,
                    rule_id="external-write-without-approval",
                )
            )
    return findings


def build_context_pack(parsed: ParsedDiff) -> dict[str, object]:
    """Return the minimal context a Codex/LLM reviewer should receive."""

    test_candidates = sorted(
        {
            f"tests/test_{path.rsplit('/', 1)[-1]}"
            for path in parsed.changed_paths
            if path.endswith(".py") and not path.startswith("tests/")
        }
    )
    return {
        "changed_paths": list(parsed.changed_paths),
        "added_line_count": len(parsed.added_lines),
        "test_candidates": test_candidates,
        "review_focus": ["correctness", "security", "data_loss", "contract_break"],
        "excluded_focus": ["style_only", "unrelated_files", "invented_runtime_result"],
    }


def run_review_service(diff_text: str) -> dict[str, object]:
    """Run the deterministic baseline and preserve structured expected failures."""

    try:
        parsed = parse_unified_diff(diff_text)
        findings = deterministic_findings(parsed.added_lines)
        report = ReviewReport(
            status="SUCCESS",
            findings=findings,
            changed_paths=list(parsed.changed_paths),
            checks={
                "line_mapping_valid": all(f.path in parsed.changed_paths for f in findings),
                "finding_count": len(findings),
                "context_pack": build_context_pack(parsed),
            },
            automatic_publish=False,
        )
    except (ValueError, ValidationError) as exc:
        report = ReviewReport(
            status="EXPECTED_FAILURE",
            findings=[],
            changed_paths=[],
            checks={"line_mapping_valid": False, "finding_count": 0},
            error_code=str(exc).splitlines()[0],
            automatic_publish=False,
        )
    return report.model_dump(mode="json")
