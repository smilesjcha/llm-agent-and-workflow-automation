"""End-to-end Review Copilot workflow used by the Day 3 notebook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .context_builder import build_context_pack
from .contracts import ReviewPolicy
from .diff_parser import parse_unified_diff
from .evaluation import evaluate_case_set
from .errors import stable_error_code
from .github_plan import build_github_dry_run
from .human_review import apply_human_review
from .providers import FixtureReviewProvider, ReviewProvider, run_provider
from .review_engine import merge_grounded_candidates
from .safety import is_sensitive_path, redact_secret_like_text
from .test_evidence import not_run_evidence
from .workspace import read_workspace_json, read_workspace_text


def run_review_workflow(
    *,
    workspace_root: str | Path,
    diff_path: str | Path,
    project_context_path: str | Path,
    fixture_path: str | Path,
    provider: ReviewProvider | None = None,
    allow_fallback: bool = True,
    decision: str | None = None,
    reviewer: str = "수강생",
    rationale: str = "근거 라인과 최소 교정을 확인했습니다.",
    repository: str = "smilesjcha/llm-agent-and-workflow-automation",
    base: str = "main",
    branch: str = "codex/day3-review-copilot",
    evaluation_manifest_path: str | Path = "labs/day3/review_copilot/fixtures/cases.json",
    golden_path: str | Path = "labs/day3/review_copilot/fixtures/golden_findings.json",
    edited_findings: list[dict[str, Any]] | None = None,
    context_max_bytes: int = 20_000,
    test_evidence: dict[str, Any] | None = None,
    provider_case_id: str | None = None,
    candidate_evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load workspace-scoped fixtures, then run the in-memory workflow."""

    try:
        diff_text = read_workspace_text(diff_path, workspace_root=workspace_root)
        project_context = read_workspace_json(
            project_context_path, workspace_root=workspace_root
        )
        fixture_payload = read_workspace_json(fixture_path, workspace_root=workspace_root)
    except (OSError, ValueError, TypeError) as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "completed_stage": 0,
            "external_write": False,
        }

    return run_review_text_workflow(
        workspace_root=workspace_root,
        diff_text=diff_text,
        project_context=project_context,
        fixture_payload=fixture_payload,
        provider=provider,
        allow_fallback=allow_fallback,
        decision=decision,
        reviewer=reviewer,
        rationale=rationale,
        repository=repository,
        base=base,
        branch=branch,
        evaluation_manifest_path=evaluation_manifest_path,
        golden_path=golden_path,
        edited_findings=edited_findings,
        context_max_bytes=context_max_bytes,
        test_evidence=test_evidence,
        provider_case_id=provider_case_id,
        candidate_evaluation=candidate_evaluation,
    )


def run_review_text_workflow(
    *,
    workspace_root: str | Path,
    diff_text: str,
    project_context: dict[str, Any],
    fixture_payload: dict[str, Any],
    provider: ReviewProvider | None = None,
    allow_fallback: bool = True,
    decision: str | None = None,
    reviewer: str = "수강생",
    rationale: str = "근거 라인과 최소 교정을 확인했습니다.",
    repository: str = "smilesjcha/llm-agent-and-workflow-automation",
    base: str = "main",
    branch: str = "codex/day3-review-copilot",
    evaluation_manifest_path: str | Path = "labs/day3/review_copilot/fixtures/cases.json",
    golden_path: str | Path = "labs/day3/review_copilot/fixtures/golden_findings.json",
    edited_findings: list[dict[str, Any]] | None = None,
    context_max_bytes: int = 20_000,
    test_evidence: dict[str, Any] | None = None,
    provider_case_id: str | None = None,
    candidate_evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run all stages on an in-memory diff; suitable for the localhost UI."""

    policy = ReviewPolicy()
    try:
        responses = fixture_payload.get("responses")
        if not isinstance(responses, dict):
            raise ValueError("FIXTURE_RESPONSES_REQUIRED")
        fixture = FixtureReviewProvider(responses)
        requested = provider or fixture
        parsed = parse_unified_diff(diff_text)
        context = build_context_pack(
            parsed,
            policy=policy,
            project_context=project_context,
            max_bytes=context_max_bytes,
            workspace_root=workspace_root,
        )
        prompt_lines = []
        prompt_redaction_count = 0
        for line in parsed.added_lines:
            if is_sensitive_path(line.path):
                continue
            safe_text, redaction_count = redact_secret_like_text(line.text)
            prompt_redaction_count += redaction_count
            prompt_lines.append({**line.to_dict(), "text": safe_text})
        prompt = {
            "case_id": provider_case_id
            or str(fixture_payload.get("case_id", "default")),
            "contract": "ReviewFinding",
            "context": context,
            "added_lines": prompt_lines,
            "redaction_count": context.get("redaction_count", 0)
            + prompt_redaction_count,
        }
        provider_result = run_provider(
            requested=requested,
            fallback=fixture,
            prompt=prompt,
            allow_fallback=allow_fallback,
        )
        draft = merge_grounded_candidates(parsed, provider_result)
        human_review = apply_human_review(
            draft,
            decision=decision,
            reviewer=reviewer,
            rationale=rationale,
            edited_findings=edited_findings,
        )
        evidence = dict(test_evidence) if test_evidence is not None else not_run_evidence()
        github = build_github_dry_run(
            repository=repository,
            base=base,
            branch=branch,
            title="Day 3 Review Copilot 실습",
            review=human_review,
            changed_paths=list(parsed.changed_paths),
            test_evidence=evidence,
        )
        evaluation = evaluate_case_set(
            workspace_root=workspace_root,
            manifest_path=evaluation_manifest_path,
            golden_path=golden_path,
        )
    except (OSError, ValueError, TypeError) as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "completed_stage": 0,
            "external_write": False,
        }

    hybrid_review = {**draft.to_dict(), "test_evidence": evidence}
    live_provider_used = provider_result.get("provider_used") not in {None, "fixture"}
    if not live_provider_used:
        candidate_gate = {
            "status": "NOT_REQUIRED",
            "reason": "FIXTURE_OR_RULE_BASELINE_USED",
        }
    elif candidate_evaluation and candidate_evaluation.get("release_decision") == "READY":
        candidate_gate = {"status": "PASSED", "evidence": candidate_evaluation}
    else:
        candidate_gate = {
            "status": "HOLD",
            "error_code": "LIVE_PROVIDER_CANDIDATE_EVALUATION_REQUIRED",
        }
    stages = {
        "01_review_contract": policy.to_dict(),
        "02_parsed_diff": parsed.to_dict(),
        "03_context_pack": context,
        "04_candidate_review": provider_result,
        "05_hybrid_review": hybrid_review,
        "06_human_review": {
            **human_review.to_dict(),
            "langgraph": _optional_langgraph_review(
                draft.to_dict(),
                decision=decision,
                reviewer=reviewer,
                rationale=rationale,
                edited_findings=edited_findings,
            ),
        },
        "07_evaluation": evaluation,
        "08_release_evidence": {
            "finding_count": len(draft.findings),
            "changed_path_count": len(parsed.changed_paths),
            "provider_provenance_visible": True,
            "human_review_required": True,
            "external_write": False,
            "rule_baseline_gate": evaluation,
            "provider_candidate_gate": candidate_gate,
            "github_dry_run": github,
            "decision": "READY_FOR_MANUAL_GITHUB_STEP"
            if github["status"] == "DRY_RUN_READY"
            and evaluation["release_decision"] == "READY"
            and evidence.get("status") == "PASSED"
            and candidate_gate["status"] in {"NOT_REQUIRED", "PASSED"}
            else "HOLD",
        },
    }
    return {
        "status": "SUCCESS",
        "completed_stage": 8,
        "stages": stages,
        "external_write": False,
    }


def _optional_langgraph_review(
    draft: dict[str, Any],
    *,
    decision: str | None,
    reviewer: str | None,
    rationale: str | None,
    edited_findings: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Use LangGraph when installed and keep a stable optional-dependency result."""

    try:
        from .langgraph_review import run_langgraph_human_review

        return run_langgraph_human_review(
            draft,
            decision=decision,
            reviewer=reviewer,
            rationale=rationale,
            edited_findings=edited_findings,
            thread_id="day3-workflow-human-review",
        )
    except RuntimeError as exc:
        if str(exc) != "LANGGRAPH_NOT_INSTALLED":
            raise
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "LANGGRAPH_NOT_INSTALLED",
            "interrupted": False,
            "external_write": False,
        }
