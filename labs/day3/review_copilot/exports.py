"""Pure JSON-to-Markdown export for a reviewed local result."""

from __future__ import annotations

from typing import Any


def render_review_markdown(result: dict[str, Any]) -> str:
    if result.get("status") != "SUCCESS":
        return f"# Review Copilot\n\n실행 실패: `{result.get('error_code', 'UNKNOWN')}`\n"
    stages = result["stages"]
    draft = stages["05_hybrid_review"]
    review = stages["06_human_review"]
    evaluation = stages["07_evaluation"]
    rows = [
        "# Review Copilot 결과",
        "",
        f"- Provider: `{draft['provider_requested']}` → `{draft['provider_used']}`",
        f"- Human Review: `{review['status']}` / {review['reviewer']}",
        f"- Golden evaluation: {evaluation['case_passed']}/{evaluation['case_count']} · F1 {evaluation['f1']}",
        "- External write: `false`",
        "",
        "## Findings",
        "",
    ]
    reviewed_findings = review["findings"]
    if not reviewed_findings:
        rows.append("검토할 finding이 없습니다.")
    for finding in reviewed_findings:
        rows.extend(
            [
                f"### {finding['severity']} · {finding['title']}",
                "",
                f"- 위치: `{finding['path']}:{finding['line']}`",
                f"- 영향: {finding['impact']}",
                f"- 근거: `{finding['evidence']}`",
                f"- 최소 교정: {finding['correction']}",
                f"- Rule: `{finding['rule_id']}`",
                "",
            ]
        )
    return "\n".join(rows).rstrip() + "\n"
