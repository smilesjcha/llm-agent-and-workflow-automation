"""Offline evidence for the Day 3 controlled experiments and repair stages."""

from copy import deepcopy
import difflib
from pathlib import Path
import shutil

import pytest

from labs.day3.review_copilot.deep_dive import (
    MAX_CONTEXT_BYTES, build_context_payload, build_stage_source,
    checkout_ground_truth, run_context_review, score_review_findings,
)
from labs.day3.review_copilot.exercise import prepare_exercise, run_exercise_demo, run_exercise_tests
from labs.day3.review_copilot.providers import FixtureReviewProvider, UnavailableReviewProvider


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path("labs/day3/review_copilot/fixtures/checkout")


def new_file_diff(source, path="checkout.py"):
    return "".join(difflib.unified_diff(
        [], source.splitlines(keepends=True), fromfile="/dev/null", tofile=f"b/{path}",
    ))


def context_inputs():
    source = build_stage_source()
    return {
        "source": source, "diff": new_file_diff(source),
        "business_rules": "쿠폰 할인액은 상품 금액 이하. 할인 후 50,000원부터 무료 배송.",
        "test_evidence": {"status": "FAILED", "test_count": 9, "cases": [{"name": "coupon", "status": "FAIL"}]},
    }


class RecordingProvider:
    name = "test-recorder"
    model = "no-network-test-double"

    def __init__(self):
        self.calls = []

    def review(self, prompt):
        self.calls.append(deepcopy(prompt))
        return []


def test_context_modes_change_the_exact_provider_payload_without_hidden_fields():
    inputs = context_inputs()
    before = deepcopy(inputs)
    recorder = RecordingProvider()
    payloads = [build_context_payload(**inputs, mode=mode)
                for mode in ("code_only", "policy", "policy_and_tests")]
    for payload in payloads:
        result = run_context_review(payload, provider=recorder, allow_live=True)
        assert result["provider_called"] is True
        assert result["provider_used"] == "test-recorder"
        assert result["sent_fields"] == sorted(payload)
    common = {"case_id", "mode", "source", "diff", "added_lines"}
    assert [set(payload) for payload in recorder.calls] == [
        common, common | {"business_rules"}, common | {"business_rules", "test_evidence"},
    ]
    assert len({payload["source"] for payload in recorder.calls}) == 1
    assert len({payload["diff"] for payload in recorder.calls}) == 1
    assert inputs == before
    payloads[-1]["test_evidence"]["cases"][0]["status"] = "MUTATED"
    assert inputs == before


def test_context_never_reads_unselected_arguments():
    inputs = context_inputs()
    inputs["business_rules"] = object()
    inputs["test_evidence"] = object()
    payload = build_context_payload(**inputs, mode="code_only")
    assert "business_rules" not in payload and "test_evidence" not in payload


def test_context_provider_mutation_cannot_change_the_callers_payload():
    class MutatingProvider(RecordingProvider):
        def review(self, prompt):
            prompt["test_evidence"]["cases"].clear()
            return []

    payload = build_context_payload(**context_inputs(), mode="policy_and_tests")
    before = deepcopy(payload)
    run_context_review(payload, provider=MutatingProvider(), allow_live=True)
    assert payload == before


def test_context_default_never_invokes_a_nonfixture_provider():
    provider = RecordingProvider()
    result = run_context_review(build_context_payload(**context_inputs()), provider=provider)
    assert result["error_code"] == "CONTEXT_LIVE_OPT_IN_REQUIRED"
    assert result["provider_called"] is False and provider.calls == []
    assert result["provider_used"] is None
    assert result["sent_fields"] == []


def test_context_fixture_is_explicit_and_fallback_is_never_silent():
    payload = build_context_payload(**context_inputs())
    fixture = FixtureReviewProvider({"checkout-context": []})
    offline = run_context_review(payload, provider=fixture)
    assert offline["provider_used"] == "fixture" and offline["fallback_reason"] is None
    unavailable = UnavailableReviewProvider("codex_cli", "CODEX_LOGIN_REQUIRED")
    failure = run_context_review(payload, provider=unavailable, allow_live=True)
    assert failure["status"] == "EXPECTED_FAILURE"
    assert failure["error_code"] == "CODEX_LOGIN_REQUIRED" and failure["provider_used"] is None
    recovery = run_context_review(
        payload, provider=unavailable, allow_live=True, allow_fallback=True, fallback=fixture,
    )
    assert recovery["provider_used"] == "fixture"
    assert recovery["fallback_reason"] == "CODEX_LOGIN_REQUIRED"


@pytest.mark.parametrize("path", ["../checkout.py", "/etc/passwd", "C:/secret.py", r"..\secret.py", ".env", "config/credentials.json"])
def test_context_blocks_unsafe_and_sensitive_diff_path_labels(path):
    inputs = context_inputs()
    inputs["diff"] = new_file_diff(inputs["source"], path)
    with pytest.raises(ValueError, match="CONTEXT_PATH_BLOCKED"):
        build_context_payload(**inputs)


def test_context_blocks_unsafe_old_path_too():
    inputs = context_inputs()
    inputs["diff"] = inputs["diff"].replace("--- /dev/null", "--- a/../private.py")
    with pytest.raises(ValueError, match="CONTEXT_PATH_BLOCKED"):
        build_context_payload(**inputs)


@pytest.mark.parametrize("field,value,mode,error", [
    ("source", "", "code_only", "CONTEXT_SOURCE_REQUIRED"),
    ("diff", "", "code_only", "CONTEXT_DIFF_REQUIRED"),
    ("business_rules", "", "policy", "CONTEXT_RULES_REQUIRED"),
    ("test_evidence", {}, "policy_and_tests", "CONTEXT_TEST_EVIDENCE_REQUIRED"),
    ("test_evidence", {"invalid": object()}, "policy_and_tests", "CONTEXT_JSON_INVALID"),
    ("test_evidence", {"invalid": float("nan")}, "policy_and_tests", "CONTEXT_JSON_INVALID"),
    ("source", "x" * (MAX_CONTEXT_BYTES + 1), "code_only", "CONTEXT_TOO_LARGE"),
    ("source", "\ud800", "code_only", "CONTEXT_ENCODING_INVALID"),
    ("test_evidence", {"invalid": "\ud800"}, "policy_and_tests", "CONTEXT_ENCODING_INVALID"),
])
def test_context_expected_input_failures_have_named_codes(field, value, mode, error):
    inputs = context_inputs()
    inputs[field] = value
    with pytest.raises(ValueError, match=error):
        build_context_payload(**inputs, mode=mode)


def test_context_rejects_invalid_mode_and_modified_experimental_payload():
    with pytest.raises(ValueError, match="CONTEXT_MODE_INVALID"):
        build_context_payload(**context_inputs(), mode="all")
    payload = build_context_payload(**context_inputs())
    payload["business_rules"] = "Hidden policy must not be sent in code_only."
    with pytest.raises(ValueError, match="CONTEXT_PAYLOAD_MISMATCH"):
        run_context_review(payload, provider=FixtureReviewProvider({}))


def test_context_redacts_only_synthetic_secret_shaped_text_and_preserves_input():
    inputs = context_inputs()
    inputs["test_evidence"]["stderr"] = "password=public-synthetic-example"
    before = deepcopy(inputs)
    payload = build_context_payload(**inputs, mode="policy_and_tests")
    assert payload["test_evidence"]["stderr"] == "password=[REDACTED]"
    assert inputs == before


@pytest.fixture
def checkout_workspace(tmp_path):
    shutil.copytree(ROOT / TEMPLATE, tmp_path / TEMPLATE)
    prepare_exercise(workspace_root=tmp_path)
    return tmp_path


def test_all_repair_stages_execute_the_same_unchanged_nine_tests(checkout_workspace):
    directory = checkout_workspace / "output/day3-redesign/student-service"
    checks = directory / "starter/checkout_checks.py"
    original_checks = checks.read_bytes()
    original_template = (ROOT / TEMPLATE / "starter/checkout.py").read_bytes()
    failure_counts = []
    for stage in ("starter", "coupon_cap", "shipping", "validated"):
        (directory / "starter/checkout.py").write_text(build_stage_source(stage), encoding="utf-8")
        result = run_exercise_tests(workspace_root=checkout_workspace)
        assert result["test_count"] == len(result["cases"]) == 9
        failure_counts.append(sum(case["status"] != "PASSED" for case in result["cases"]))
        assert checks.read_bytes() == original_checks
    assert failure_counts == [7, 5, 4, 0]
    assert (ROOT / TEMPLATE / "starter/checkout.py").read_bytes() == original_template
    assert run_exercise_demo(workspace_root=checkout_workspace)["result"]["payable_won"] == 3_000
    assert run_exercise_demo(workspace_root=checkout_workspace, total_won=-1)["error_code"] == "MONEY_NON_NEGATIVE_REQUIRED"


def test_stage_builder_does_not_overwrite_student_edits(checkout_workspace):
    path = checkout_workspace / "output/day3-redesign/student-service/starter/checkout.py"
    original = path.read_text(encoding="utf-8") + "\n# Student's own work\n"
    path.write_text(original, encoding="utf-8")
    assert "min(total_won, coupon_won)" in build_stage_source("coupon_cap")
    assert path.read_text(encoding="utf-8") == original
    assert build_stage_source("validated") == (ROOT / TEMPLATE / "solution/checkout.py").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="CHECKOUT_STAGE_INVALID"):
        build_stage_source("unknown")


def test_stage_detects_template_drift_instead_of_silently_omitting_a_fix(monkeypatch):
    monkeypatch.setattr("labs.day3.review_copilot.deep_dive._template_source", lambda version: "# changed template\n")
    with pytest.raises(ValueError, match="CHECKOUT_TEMPLATE_CHANGED"):
        build_stage_source("coupon_cap")


def test_stage_template_cannot_read_through_an_external_symlink(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "checkout.py").write_text("# Public test-only outside file\n", encoding="utf-8")
    templates = tmp_path / "fixtures"
    templates.mkdir()
    (templates / "starter").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr("labs.day3.review_copilot.deep_dive._TEMPLATES", templates)
    with pytest.raises(ValueError, match="CHECKOUT_TEMPLATE_UNAVAILABLE"):
        build_stage_source()


def test_ground_truth_has_four_distinct_bugs_and_normal_negative_controls():
    truth = checkout_ground_truth()
    assert len(truth["bugs"]) == len(set(truth["expected_ids"])) == 4
    assert {bug["id"] for bug in truth["bugs"]} == set(truth["expected_ids"])
    assert len(truth["normal_cases"]) >= 1
    assert truth["clean_case"] == {"case_id": "checkout-validated", "source_stage": "validated", "expected_ids": []}
    truth["bugs"][0]["title"] = "MUTATED"
    assert checkout_ground_truth()["bugs"][0]["title"] != "MUTATED"


def test_human_scoring_matches_unique_bugs_not_rule_ids_or_duplicate_findings():
    findings = [{"rule_id": "arbitrary"}] * 4
    judgments = [
        {"finding_index": 0, "verdict": "expected_bug", "expected_id": "coupon-cap"},
        {"finding_index": 1, "verdict": "expected_bug", "expected_id": "coupon-cap"},
        {"finding_index": 2, "verdict": "expected_bug", "expected_id": "shipping-after-discount"},
        {"finding_index": 3, "verdict": "false_positive"},
    ]
    before = deepcopy(judgments)
    score = score_review_findings(findings, judgments)
    assert (score["tp"], score["fp"], score["fn"], score["unjudged"]) == (2, 1, 2, 0)
    assert score["recall"] == 0.5 and score["precision"] == pytest.approx(2 / 3)
    assert score["duplicate_finding_count"] == 1
    assert score["metrics_complete"] is True and score["automatic_approval"] is False
    assert judgments == before


def test_valid_additional_and_missing_human_labels_are_not_false_positives():
    score = score_review_findings(
        [{"rule_id": "coupon-cap"}, {"rule_id": "new-valid-rule"}, {"rule_id": "unreviewed"}],
        [{"finding_index": 0, "verdict": "expected_bug", "expected_id": "coupon-cap"},
         {"finding_index": 1, "verdict": "valid_additional"}],
    )
    assert score["tp"] == 1 and score["fp"] == 0 and score["unjudged"] == 2
    assert score["valid_additional_count"] == 1
    assert score["precision"] is None and score["judged_precision"] == 1.0
    assert score["metrics_complete"] is False and score["judged_coverage"] == pytest.approx(1 / 3)
    assert score["recall_so_far"] == 0.25


def test_empty_findings_and_clean_source_never_get_invented_accuracy():
    missing = score_review_findings([], [])
    assert missing["fn"] == 4 and missing["recall"] == 0.0 and missing["precision"] is None
    clean = score_review_findings([], [], expected_ids=[])
    assert clean["tp"] == clean["fp"] == clean["fn"] == 0
    assert clean["precision"] is None and clean["recall"] is None
    actual_fp = score_review_findings([{}], [{"finding_index": 0, "verdict": "false_positive"}], expected_ids=[])
    assert actual_fp["fp"] == 1 and actual_fp["precision"] == 0.0


@pytest.mark.parametrize("judgments,error", [
    ([{"finding_index": True, "verdict": "unjudged"}], "REVIEW_FINDING_INDEX_INVALID"),
    ([{"finding_index": 2, "verdict": "unjudged"}], "REVIEW_FINDING_INDEX_INVALID"),
    ([{"finding_index": 0, "verdict": "automatic"}], "REVIEW_VERDICT_INVALID"),
    ([{"finding_index": 0, "verdict": "expected_bug", "expected_id": "unknown"}], "REVIEW_EXPECTED_ID_UNKNOWN"),
    ([{"finding_index": 0, "verdict": "valid_additional", "expected_id": "coupon-cap"}], "REVIEW_UNEXPECTED_EXPECTED_ID"),
    ([{"finding_index": 0, "verdict": "unjudged"}] * 2, "REVIEW_DUPLICATE_JUDGMENT"),
])
def test_invalid_human_judgments_fail_with_explicit_codes(judgments, error):
    with pytest.raises(ValueError, match=error):
        score_review_findings([{}], judgments)


def test_ground_truth_ids_cannot_be_duplicated_to_distort_recall():
    with pytest.raises(ValueError, match="REVIEW_EXPECTED_IDS_INVALID"):
        score_review_findings([], [], expected_ids=["same", "same"])
    with pytest.raises(ValueError, match="REVIEW_EXPECTED_IDS_INVALID"):
        score_review_findings([], [], expected_ids="abcd")
