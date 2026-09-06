"""Controlled Context experiments, incremental repairs, and human review scoring.

These helpers read only the bundled public checkout templates. Provider calls
are a separate, explicit boundary; none of the builders executes student code,
overwrites a file, or publishes a review.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from .codex_cli import CodexCLIReviewProvider
from .diff_parser import parse_unified_diff
from .providers import FixtureReviewProvider, ReviewProvider, run_provider
from .safety import is_sensitive_path, redact_payload


CONTEXT_MODES = ("code_only", "policy", "policy_and_tests")
REPAIR_STAGES = ("starter", "coupon_cap", "shipping", "validated")
MAX_CONTEXT_BYTES = 240_000
_MODULE_ROOT = Path(__file__).resolve().parent
_TEMPLATES = _MODULE_ROOT / "fixtures" / "checkout"
_EXPECTED_IDS = (
    "coupon-cap", "shipping-after-discount", "input-validation", "receipt-applied-discount",
)


def _text(value: Any, error: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ValueError("CONTEXT_ENCODING_INVALID") from exc
    if size > MAX_CONTEXT_BYTES:
        raise ValueError("CONTEXT_TOO_LARGE")
    return value


def _safe_context_path(value: str) -> None:
    """Context paths are labels, not read requests; block unsafe labels as well."""
    path = value.strip().split("\t", 1)[0]
    if path == "/dev/null":
        return
    if path.startswith(("a/", "b/")):
        path = path[2:]
    if (
        not path or "\\" in path or PurePosixPath(path).is_absolute()
        or PureWindowsPath(path).drive or ".." in PurePosixPath(path).parts
        or is_sensitive_path(path)
    ):
        raise ValueError("CONTEXT_PATH_BLOCKED")


def _copy_json(value: Any) -> Any:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("CONTEXT_JSON_INVALID") from exc
    try:
        size = len(encoded.encode("utf-8"))
    except UnicodeError as exc:
        raise ValueError("CONTEXT_ENCODING_INVALID") from exc
    if size > MAX_CONTEXT_BYTES:
        raise ValueError("CONTEXT_TOO_LARGE")
    return json.loads(encoded)


def build_context_payload(
    source: str,
    diff: str,
    business_rules: str,
    test_evidence: dict[str, Any],
    mode: str = "code_only",
) -> dict[str, Any]:
    """Build the *actual* provider payload with absent, not blank, control fields.

    ``source`` and ``diff`` are file contents, never filesystem paths. All modes
    send the same source/diff/added lines. ``policy`` additionally sends business
    rules; ``policy_and_tests`` additionally sends actual test evidence. No
    ground truth, model answer, or hidden policy is appended by this helper.
    Unselected arguments are not read, serialized, or sent.
    """
    if mode not in CONTEXT_MODES:
        raise ValueError("CONTEXT_MODE_INVALID")
    _text(source, "CONTEXT_SOURCE_REQUIRED")
    _text(diff, "CONTEXT_DIFF_REQUIRED")
    for line in diff.splitlines():
        if line.startswith(("--- ", "+++ ")):
            _safe_context_path(line[4:])
    parsed = parse_unified_diff(diff)
    for path in parsed.changed_paths:
        _safe_context_path(path)
    if not parsed.added_lines:
        raise ValueError("CONTEXT_ADDED_LINES_REQUIRED")
    payload: dict[str, Any] = {
        "case_id": "checkout-context", "mode": mode,
        "source": source, "diff": diff,
        "added_lines": [line.to_dict() for line in parsed.added_lines],
    }
    if mode in {"policy", "policy_and_tests"}:
        payload["business_rules"] = _text(business_rules, "CONTEXT_RULES_REQUIRED")
    if mode == "policy_and_tests":
        if not isinstance(test_evidence, dict) or not test_evidence:
            raise ValueError("CONTEXT_TEST_EVIDENCE_REQUIRED")
        payload["test_evidence"] = _copy_json(test_evidence)
    safe_payload, _ = redact_payload(_copy_json(payload))
    return safe_payload


def run_context_review(
    payload: dict[str, Any], *, provider: ReviewProvider | None = None,
    allow_live: bool = False, allow_fallback: bool = False,
    fallback: FixtureReviewProvider | None = None,
) -> dict[str, Any]:
    """Call run_provider directly, without review_exercise's automatic Context.

    A custom/non-fixture provider requires ``allow_live=True``. Codex additionally
    requires its own ``live_opt_in=True``. Fallback is always separately selected
    and labelled; an omitted fixture is an empty offline response, not live data.
    """
    if not isinstance(payload, dict):
        raise ValueError("CONTEXT_PAYLOAD_INVALID")
    mode = payload.get("mode")
    rebuilt = build_context_payload(
        payload.get("source"), payload.get("diff"), payload.get("business_rules"),
        payload.get("test_evidence"), mode=mode,
    )
    if payload != rebuilt:
        raise ValueError("CONTEXT_PAYLOAD_MISMATCH")
    requested = provider if provider is not None else CodexCLIReviewProvider()
    metadata = {"context_mode": mode, "sent_fields": sorted(rebuilt), "external_write": False}
    if not isinstance(requested, FixtureReviewProvider) and not allow_live:
        return {
            "status": "EXPECTED_FAILURE", "error_code": "CONTEXT_LIVE_OPT_IN_REQUIRED",
            "provider_requested": requested.name, "provider_used": None,
            "requested_model": requested.model, "model": None, "schema_valid": False,
            "fallback_reason": None, "candidates": [], "provider_called": False, **metadata,
            "sent_fields": [],
        }
    result = run_provider(
        requested=requested,
        fallback=fallback if fallback is not None else FixtureReviewProvider({}),
        prompt=rebuilt, allow_fallback=allow_fallback,
    )
    return {**result, "provider_called": True, **metadata}


def _template_source(version: str) -> str:
    template = (_TEMPLATES / version / "checkout.py").resolve()
    if not template.is_relative_to(_MODULE_ROOT) or not template.is_file():
        raise ValueError("CHECKOUT_TEMPLATE_UNAVAILABLE")
    return template.read_text(encoding="utf-8")


def _replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("CHECKOUT_TEMPLATE_CHANGED")
    return source.replace(before, after, 1)


def build_stage_source(stage: str = "starter") -> str:
    """Return a source string, preserving the templates and all student files.

    The unchanged nine checks produce 7 → 5 → 4 → 0 failures. The coupon stage
    fixes both the calculation and receipt; shipping changes only its threshold;
    validated adds the input checks from the existing reference implementation.
    """
    if stage not in REPAIR_STAGES:
        raise ValueError("CHECKOUT_STAGE_INVALID")
    if stage == "validated":
        return _template_source("solution")
    source = _template_source("starter")
    if stage in {"coupon_cap", "shipping"}:
        source = _replace_once(
            source, "return total_won - coupon_won", "return total_won - min(total_won, coupon_won)",
        )
        source = _replace_once(
            source, '"coupon_applied_won": coupon_won,',
            '"coupon_applied_won": min(total_won, coupon_won),',
        )
    if stage == "shipping":
        source = _replace_once(
            source, "shipping = 0 if total_won >= 50_000 else 3_000",
            "shipping = 0 if payment >= 50_000 else 3_000",
        )
    return source


def checkout_ground_truth() -> dict[str, Any]:
    """Human-only scoring reference; never automatically sent to a provider."""
    return {
        "case_id": "checkout-starter", "source_stage": "starter",
        "expected_ids": list(_EXPECTED_IDS),
        "bugs": [
            {"id": "coupon-cap", "title": "쿠폰 상한 누락",
             "reproduction": "payable(10_000, 15_000)", "expected": 0, "starter_actual": -5_000,
             "test_names": ["test_coupon_larger_than_total_is_capped"]},
            {"id": "shipping-after-discount", "title": "할인 전 무료 배송 판정",
             "reproduction": 'calculate_checkout(50_000, 10_000)["shipping_won"]',
             "expected": 3_000, "starter_actual": 0,
             "test_names": ["test_shipping_uses_discounted_amount"]},
            {"id": "input-validation", "title": "금액 입력 검사 누락",
             "reproduction": "payable(-100, 0); payable(10_000, -100); payable(10_000.5, 100); payable(True, 0)",
             "expected": "음수는 MONEY_NON_NEGATIVE_REQUIRED, 소수·bool은 MONEY_INTEGER_REQUIRED",
             "test_names": ["test_negative_total_is_rejected", "test_negative_coupon_is_rejected",
                            "test_fractional_won_is_rejected", "test_bool_is_not_money"]},
            {"id": "receipt-applied-discount", "title": "실제 할인액과 다른 영수증",
             "reproduction": 'calculate_checkout(10_000, 15_000)["coupon_applied_won"]',
             "expected": 10_000, "starter_actual": 15_000,
             "test_names": ["test_receipt_records_applied_discount"]},
        ],
        "normal_cases": [
            {"id": "normal-coupon", "reproduction": "payable(30_000, 5_000)",
             "expected": 25_000, "test_name": "test_normal_coupon"},
            {"id": "free-shipping-threshold", "reproduction": 'calculate_checkout(55_000, 5_000)["shipping_won"]',
             "expected": 0, "test_name": "test_free_shipping_at_threshold"},
        ],
        "clean_case": {"case_id": "checkout-validated", "source_stage": "validated", "expected_ids": []},
        "scoring_note": "4개 결함 범주와 9개 테스트는 다릅니다. 정상 코드에 대한 지적도 사람이 확인합니다.",
    }


def score_review_findings(
    findings: list[dict[str, Any]], judgments: list[dict[str, Any]], *,
    expected_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Score explicit human mappings, without guessing from rule_id or wording.

    Each judgment has finding_index and verdict. ``expected_bug`` also needs a
    known expected_id. ``valid_additional`` remains unjudged against this rubric,
    not FP. Duplicate findings cannot increase TP or recall. Missing judgments
    remain unjudged. Final precision is withheld until all findings are mapped;
    judged_precision/recall_so_far are explicitly provisional observations.
    """
    if not isinstance(findings, list) or not all(isinstance(item, dict) for item in findings):
        raise ValueError("REVIEW_FINDINGS_INVALID")
    if not isinstance(judgments, list) or not all(isinstance(item, dict) for item in judgments):
        raise ValueError("REVIEW_JUDGMENTS_INVALID")
    if expected_ids is not None and not isinstance(expected_ids, (list, tuple)):
        raise ValueError("REVIEW_EXPECTED_IDS_INVALID")
    expected = list(_EXPECTED_IDS if expected_ids is None else expected_ids)
    if (
        not all(isinstance(item, str) and item.strip() for item in expected)
        or len(expected) != len(set(expected))
    ):
        raise ValueError("REVIEW_EXPECTED_IDS_INVALID")
    mapped: dict[int, dict[str, Any]] = {}
    verdicts = {"expected_bug", "false_positive", "valid_additional", "unjudged"}
    for judgment in judgments:
        index, verdict = judgment.get("finding_index"), judgment.get("verdict")
        if type(index) is not int or not 0 <= index < len(findings):
            raise ValueError("REVIEW_FINDING_INDEX_INVALID")
        if index in mapped:
            raise ValueError("REVIEW_DUPLICATE_JUDGMENT")
        if not isinstance(verdict, str) or verdict not in verdicts:
            raise ValueError("REVIEW_VERDICT_INVALID")
        expected_id = judgment.get("expected_id")
        if verdict == "expected_bug":
            if not isinstance(expected_id, str) or expected_id not in expected:
                raise ValueError("REVIEW_EXPECTED_ID_UNKNOWN")
        elif expected_id is not None:
            raise ValueError("REVIEW_UNEXPECTED_EXPECTED_ID")
        mapped[index] = {"finding_index": index, "verdict": verdict, "expected_id": expected_id}
    rows = [mapped.get(index, {"finding_index": index, "verdict": "unjudged", "expected_id": None})
            for index in range(len(findings))]
    matches = [row["expected_id"] for row in rows if row["verdict"] == "expected_bug"]
    matched = set(matches)
    tp = len(matched)
    fp = sum(row["verdict"] == "false_positive" for row in rows)
    unjudged = sum(row["verdict"] in {"unjudged", "valid_additional"} for row in rows)
    judged_precision = tp / (tp + fp) if tp + fp else None
    recall = tp / len(expected) if expected else None
    return {
        "tp": tp, "fp": fp, "fn": len(expected) - tp, "unjudged": unjudged,
        "precision": judged_precision if unjudged == 0 else None,
        "recall": recall, "judged_precision": judged_precision, "recall_so_far": recall,
        "metrics_complete": unjudged == 0,
        "judged_coverage": (len(findings) - unjudged) / len(findings) if findings else 1.0,
        "duplicate_finding_count": len(matches) - tp,
        "valid_additional_count": sum(row["verdict"] == "valid_additional" for row in rows),
        "finding_count": len(findings), "expected_bug_count": len(expected),
        "matched_expected_ids": sorted(matched),
        "unmatched_expected_ids": [item for item in expected if item not in matched],
        "judgments": rows, "automatic_approval": False,
        "metric_scope": "사람이 매핑한 고유 결함 범주; unjudged가 있으면 잠정 평가",
    }
