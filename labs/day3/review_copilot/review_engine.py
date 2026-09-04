"""Rule baseline plus optional provider candidates, grounded to diff lines."""

from __future__ import annotations

import re
from typing import Any

from .contracts import AddedLine, ParsedDiff, ReviewDraft, ReviewFinding


def _finding(
    line: AddedLine,
    *,
    severity: str,
    title: str,
    impact: str,
    correction: str,
    rule_id: str,
) -> ReviewFinding:
    return ReviewFinding(
        path=line.path,
        line=line.line,
        severity=severity,  # type: ignore[arg-type]
        title=title,
        impact=impact,
        evidence=line.text.strip()[:200] or "빈 추가 라인",
        correction=correction,
        rule_id=rule_id,
        source="rule",
        confidence=0.99,
    )


def deterministic_review(parsed: ParsedDiff) -> list[ReviewFinding]:
    """Detect consequential defects with deterministic classroom rules."""

    findings: list[ReviewFinding] = []
    for line in parsed.added_lines:
        text = line.text
        if re.search(r"\b(eval|exec)\s*\(", text):
            findings.append(
                _finding(
                    line,
                    severity="P0",
                    title="입력 문자열의 코드 실행",
                    impact="외부 입력이 임의 코드 실행으로 이어질 수 있습니다.",
                    correction="허용 함수 registry와 명시적 argument schema로 교체하세요.",
                    rule_id="unsafe-dynamic-execution",
                )
            )
        if re.search(r"\bsubprocess\.(?:run|Popen)\(.*shell\s*=\s*True", text):
            findings.append(
                _finding(
                    line,
                    severity="P0",
                    title="shell=True 명령 주입 위험",
                    impact="외부 입력이 shell 확장을 거쳐 임의 명령으로 실행될 수 있습니다.",
                    correction="shell을 제거하고 allowlist로 검증한 인자 배열을 전달하세요.",
                    rule_id="shell-command-injection",
                )
            )
        if re.search(r"\b(?:requests|httpx)\.(post|put|patch|delete)\(", text) and not re.search(
            r"dry_run|human_approved|approval", text, flags=re.IGNORECASE
        ):
            findings.append(
                _finding(
                    line,
                    severity="P1",
                    title="사람 승인 없는 외부 서비스 호출",
                    impact="잘못된 대상이나 재시도가 실제 게시·수정으로 이어질 수 있습니다.",
                    correction="dry-run payload와 사람 승인 조건을 외부 서비스 호출 앞에 두세요.",
                    rule_id="external-write-without-approval",
                )
            )
        if re.search(r"^\s*except(?:\s+Exception)?\s*:\s*$", text):
            findings.append(
                _finding(
                    line,
                    severity="P2",
                    title="실패 원인을 지우는 예외 처리",
                    impact="인증·입력·네트워크 오류가 같은 성공 결과로 숨겨집니다.",
                    correction="복구 가능한 예외만 잡고 안정적인 error_code를 반환하세요.",
                    rule_id="broad-exception-boundary",
                )
            )
        if re.search(
            r"\b(?:print|logger\.(?:debug|info|warning|error|exception))\s*\(.*"
            r"(?:token|secret|api[_-]?key|password)",
            text,
            flags=re.IGNORECASE,
        ):
            findings.append(
                _finding(
                    line,
                    severity="P1",
                    title="로그에 인증정보 노출",
                    impact="로그 수집기와 디버그 화면을 통해 credential이 유출될 수 있습니다.",
                    correction="값을 기록하지 말고 provider 상태와 비민감 request ID만 남기세요.",
                    rule_id="secret-in-log",
                )
            )
        if re.search(r"\b(?:requests|httpx)\.(?:get|post|put|patch|delete)\(", text) and not re.search(
            r"\btimeout\s*=", text
        ):
            findings.append(
                _finding(
                    line,
                    severity="P2",
                    title="네트워크 timeout 누락",
                    impact="응답이 없는 외부 서비스 때문에 worker가 무기한 대기할 수 있습니다.",
                    correction="연결·응답 timeout을 명시하고 제한된 재시도만 허용하세요.",
                    rule_id="network-timeout-missing",
                )
            )
        if re.search(r"\b(?:requests|httpx)\.(?:post|put|patch|delete)\(", text) and not re.search(
            r"idempoten", text, flags=re.IGNORECASE
        ):
            findings.append(
                _finding(
                    line,
                    severity="P1",
                    title="외부 서비스 중복 호출 방지 키 누락",
                    impact="재시도 시 같은 댓글·문서·알림이 중복 생성될 수 있습니다.",
                    correction="업무 대상과 payload로 안정적인 idempotency key를 생성하세요.",
                    rule_id="idempotency-key-missing",
                )
            )
    return findings


def _provider_finding(
    candidate: dict[str, Any],
    evidence: AddedLine,
    *,
    provider_used: str,
) -> ReviewFinding:
    return ReviewFinding(
        path=evidence.path,
        line=evidence.line,
        severity=str(candidate["severity"]),  # type: ignore[arg-type]
        title=str(candidate["title"]),
        impact=str(candidate["impact"]),
        evidence=evidence.text.strip()[:200] or "빈 추가 라인",
        correction=str(candidate["correction"]),
        rule_id=str(candidate["rule_id"]),
        source="fixture_llm" if provider_used == "fixture" else "live_llm",
        confidence=float(candidate.get("confidence", 0.7)),
    )


def merge_grounded_candidates(
    parsed: ParsedDiff,
    provider_result: dict[str, Any],
) -> ReviewDraft:
    """Keep only provider findings tied to an actual added line."""

    if provider_result["status"] != "SUCCESS":
        return ReviewDraft(
            status="EXPECTED_FAILURE",
            findings=tuple(),
            provider_requested=str(provider_result["provider_requested"]),
            provider_used="none",
            error_code=str(provider_result["error_code"]),
        )

    known = {(line.path, line.line): line for line in parsed.added_lines}
    findings = deterministic_review(parsed)
    keys = {(finding.path, finding.line, finding.rule_id) for finding in findings}
    for candidate in provider_result.get("candidates", []):
        try:
            path = str(candidate["path"])
            line_number = int(candidate["line"])
            evidence = known[(path, line_number)]
            finding = _provider_finding(
                candidate,
                evidence,
                provider_used=str(provider_result["provider_used"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        key = (finding.path, finding.line, finding.rule_id)
        if key not in keys:
            findings.append(finding)
            keys.add(key)

    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    findings.sort(key=lambda item: (severity_rank[item.severity], item.path, item.line, item.rule_id))
    return ReviewDraft(
        status="DRAFT",
        findings=tuple(findings),
        provider_requested=str(provider_result["provider_requested"]),
        provider_used=str(provider_result["provider_used"]),
        fallback_reason=provider_result.get("fallback_reason"),
        automatic_publish=False,
    )
