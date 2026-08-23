"""Offline evaluation helpers used by the Day 3 and Day 5 labs."""

from __future__ import annotations

from typing import Any


def finding_key(item: dict[str, Any]) -> tuple[str, int, str]:
    return (str(item["path"]), int(item["line"]), str(item.get("rule_id", item["title"])))


def evaluate_review_findings(
    predicted: list[dict[str, Any]], expected: list[dict[str, Any]]
) -> dict[str, Any]:
    """Calculate exact-key precision/recall without an LLM judge."""

    predicted_keys = {finding_key(item) for item in predicted}
    expected_keys = {finding_key(item) for item in expected}
    true_positive = len(predicted_keys & expected_keys)
    precision = true_positive / len(predicted_keys) if predicted_keys else 1.0
    recall = true_positive / len(expected_keys) if expected_keys else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "true_positive": true_positive,
        "false_positive": len(predicted_keys - expected_keys),
        "false_negative": len(expected_keys - predicted_keys),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


def release_gate(
    *,
    review_metrics: dict[str, Any],
    safety_passed: bool,
    latency_seconds: float,
    max_latency_seconds: float = 30.0,
) -> dict[str, Any]:
    reasons: list[str] = []
    if review_metrics.get("recall", 0.0) < 0.8:
        reasons.append("RECALL_BELOW_0_8")
    if review_metrics.get("precision", 0.0) < 0.8:
        reasons.append("PRECISION_BELOW_0_8")
    if not safety_passed:
        reasons.append("SAFETY_CHECK_FAILED")
    if latency_seconds > max_latency_seconds:
        reasons.append("LATENCY_BUDGET_EXCEEDED")
    return {
        "decision": "READY" if not reasons else "HOLD",
        "reasons": reasons,
        "human_release_required": True,
    }
