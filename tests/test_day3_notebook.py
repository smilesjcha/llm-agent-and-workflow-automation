"""The notebook must teach working code, actual failure/repair, and explicit live execution."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re

import pytest

from scripts.build_day3_notebook import build_notebook

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "materials/day3/day3_review_intelligence_lab.ipynb"
EXECUTED = ROOT / "materials/day3/day3_review_intelligence_lab.executed.ipynb"


def _source(notebook=None):
    return "\n".join("".join(cell["source"]) for cell in (notebook or build_notebook())["cells"])


def _learner_function(name, extra_scope=None):
    scope = {"Path": Path, "re": re, "json": json}
    scope.update(extra_scope or {})
    for cell in build_notebook()["cells"]:
        if cell["cell_type"] == "code":
            tree = ast.parse("".join(cell["source"]))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    exec(compile(ast.Module(body=[node], type_ignores=[]), "learner-function", "exec"), scope)
                    return scope[name]
    raise AssertionError(f"Missing learner implementation: {name}")


def test_notebook_has_eight_periods_and_compilable_code():
    notebook = build_notebook()
    source = _source(notebook)
    for number in range(1, 9):
        assert f"# {number}차시 ·" in source
    assert notebook["metadata"]["period_count"] == 8
    assert notebook["metadata"]["primary_provider"] == "codex_cli"
    assert len(notebook["cells"]) >= 40
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"cell-{index}", "exec")


def test_primary_codex_cli_is_explicit_and_replay_does_not_claim_live():
    source = _source()
    assert "RUN_CODEX_LIVE = False" in source
    assert "CodexCLIReviewProvider(live_opt_in=True" in source
    assert "checkout_fixture_provider" in source
    assert "allow_fallback=False" in source
    assert "제공된 예제 리뷰" in source
    assert "codex login status" in source
    assert '"-m", "pip", "install", "-r"' in source
    assert "OllamaReviewProvider" not in source
    assert "OPENAI_API_KEY" not in source


def test_notebook_executes_failure_repairs_real_file_and_retests_same_target():
    source = _source()
    assert 'before_tests["status"] == "FAILED"' in source
    assert 'after_tests["status"] == "PASSED"' in source
    assert 'student_file.write_text(REPAIRED_SOURCE' in source
    assert 'before_receipt["result"]["payable_won"] == -2_000' in source
    assert 'after_receipt["result"]["payable_won"] == 3_000' in source
    assert "checkout.py repair" in source
    assert source.index("before_tests = run_exercise_tests") < source.index("student_file.write_text")
    assert source.index("student_file.write_text") < source.index("after_tests = run_exercise_tests")


def test_learner_diff_parser_handles_separate_hunks_and_blocks_parent_path():
    parse = _learner_function("learner_added_line_map")
    diff = "\n".join(["+++ b/a.py", "@@ -2,2 +2,2 @@", " keep", "-old", "+new",
                      "@@ -20,1 +20,2 @@", " keep", "+new2"])
    assert [(row["line"], row["text"]) for row in parse(diff)] == [(3, "new"), (21, "new2")]
    with pytest.raises(ValueError, match="DIFF_PATH_BLOCKED"):
        parse("+++ b/../../outside.py")


def test_context_prompt_and_grounding_keep_relevant_evidence():
    select = _learner_function("learner_public_context")
    context = select({"business_rules": "rule", "changed_lines": [], "unrelated_note": "exclude"})
    assert context == {"business_rules": "rule", "changed_lines": []}
    prompt = _learner_function("learner_review_prompt")
    assert "business_rules" in prompt(context)
    assert "business_rules" not in prompt(context, refined=False)
    grounding = _learner_function("learner_grounded_candidates")
    real, invented = {"path": "a.py", "line": 5}, {"path": "a.py", "line": 999}
    assert grounding([real, invented], [real]) == ([real], [invented])


def test_metrics_distinguish_wrong_findings_and_missed_bugs():
    metrics = _learner_function("learner_review_metrics")
    result = metrics(["bug1", "style"], ["bug1", "bug2"])
    assert result == {"tp": 1, "fp": 1, "fn": 1, "precision": .5, "recall": .5, "f1": .5}
    assert metrics([], ["bug1"])["fn"] == 1
    assert metrics([], [])["f1"] == 0


def test_decision_input_rejects_unrecognized_action_and_requires_reason():
    decide = _learner_function("learner_review_decision")
    assert decide("edit", "learner", "verified")["decision"] == "edit"
    with pytest.raises(ValueError, match="REVIEW_DECISION_INVALID"):
        decide("publish", "learner", "verified")
    with pytest.raises(ValueError, match="REVIEW_REASON_REQUIRED"):
        decide("approve", "learner", " ")


def test_graph_waits_before_resume_and_carries_actual_review_to_report():
    source = _source()
    assert source.index("graph_start = review_graph.invoke") < source.index('REVIEW_DECISION = "edit"')
    assert source.index('REVIEW_DECISION = "edit"') < source.index("Command(resume=resume_payload)")
    assert 'reviewed_findings = graph_final["review"]["findings"]' in source
    assert 'rejected["findings"] == []' in source
    assert 'else "HOLD"' in source
    assert '"commands_executed": []' in source
    assert "--exercise-dir" in source
    assert "150분" in source and "Q&A 30분" in source


def test_controlled_context_has_absent_fields_and_detects_missing_policy():
    check = _learner_function("learner_check_context_mode", {
        "CONTEXT_MODES": ("code_only", "policy", "policy_and_tests")})
    assert check({"source": "code"}, "code_only")
    assert check({"source": "code", "business_rules": "rule"}, "policy")
    assert check({"source": "code", "business_rules": "rule", "test_evidence": {}}, "policy_and_tests")
    with pytest.raises(AssertionError):
        check({"source": "code"}, "policy")
    with pytest.raises(AssertionError):
        check({"source": "code", "test_evidence": {}}, "code_only")
    source = _source()
    assert "RUN_CONTEXT_COMPARE = False" in source
    assert "RUN_CLEAN_CODE_REVIEW = False" in source
    assert "run_context_review(context_payloads[mode]" in source


def test_live_comparison_budget_counts_requests_before_provider_calls():
    reserve = _learner_function("learner_check_call_budget")
    assert reserve(0, 2, 3) == 2
    assert reserve(2, 1, 3) == 3
    with pytest.raises(RuntimeError, match="CONTEXT_CALL_BUDGET_EXCEEDED"):
        reserve(3, 1, 3)
    with pytest.raises(ValueError, match="CONTEXT_CALL_COUNT_INVALID"):
        reserve(-1, 1, 3)
    with pytest.raises(ValueError, match="CONTEXT_CALL_COUNT_INVALID"):
        reserve(True, 1, 3)


def test_staged_repairs_parse_actual_unittest_evidence():
    count = _learner_function("learner_failed_tests")
    assert count({"status": "FAILED", "stderr": "FAILED (failures=5, errors=2)"}) == 7
    assert count({"status": "PASSED", "stderr": "OK"}) == 0
    with pytest.raises(ValueError, match="TEST_FAILURE_COUNT_MISSING"):
        count({"status": "FAILED", "stderr": "process did not finish"})
    source = _source()
    assert 'build_stage_source("coupon_cap")' in source
    assert 'build_stage_source("shipping")' in source
    assert 'build_stage_source("validated")' in source
    assert '[item["failed"] for item in stage_history] == [7, 5, 4, 0]' in source


def _direct_graph_namespace():
    from typing import TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import interrupt
    from labs.day3.review_copilot.contracts import ReviewDraft
    from labs.day3.review_copilot.human_review import apply_human_review

    namespace = dict(TypedDict=TypedDict, StateGraph=StateGraph, START=START, END=END,
                     InMemorySaver=InMemorySaver, interrupt=interrupt, ReviewDraft=ReviewDraft,
                     apply_human_review=apply_human_review)
    names = {"LearnerReviewState", "learner_prepare_review", "learner_human_review",
             "learner_review_route", "learner_finish_review", "learner_block_review",
             "build_learner_review_graph"}
    for cell in build_notebook()["cells"]:
        if cell["cell_type"] == "code":
            for node in ast.parse("".join(cell["source"])).body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
                    exec(compile(ast.Module(body=[node], type_ignores=[]), "learner-graph", "exec"), namespace)
    return namespace


@pytest.mark.parametrize("bad_edit", [False, True])
def test_notebook_defined_stategraph_interrupt_edit_and_boundary(bad_edit):
    from langgraph.types import Command
    from labs.day3.review_copilot.contracts import ReviewDraft, ReviewFinding

    finding = ReviewFinding(path="checkout.py", line=5, severity="P1", title="쿠폰 상한 누락",
        impact="쿠폰 초과 시 음수", evidence="return total_won - coupon_won",
        correction="쿠폰 상한 적용", rule_id="coupon-cap").to_dict()
    draft = ReviewDraft(status="DRAFT", findings=(ReviewFinding.model_validate(finding),)).to_dict()
    graph = _direct_graph_namespace()["build_learner_review_graph"]()
    config = {"configurable": {"thread_id": "learner-test"}}
    first = graph.invoke({"draft": draft, "audit": []}, config=config)
    assert "__interrupt__" in first and graph.get_state(config).next == ("human",)
    edited = {**finding, "title": "검토한 쿠폰 상한"}
    if bad_edit:
        edited["line"] = 999
    final = graph.invoke(Command(resume={"decision": "edit", "reviewer": "learner",
        "rationale": "Test 재현 확인", "edited_findings": [edited]}), config=config)
    assert final["external_write"] is False
    if bad_edit:
        assert final["status"] == "BLOCKED"
        assert final["review"]["error_code"] == "EDIT_FINDING_NOT_GROUNDED"
        assert final["findings"] == []
    else:
        assert final["status"] == "DRY_RUN_READY"
        assert final["findings"][0]["title"] == "검토한 쿠폰 상한"


def test_human_scoring_keeps_real_results_unjudged_until_explicit_mapping():
    source = _source()
    assert 'len(ground_truth["bugs"]) == 4' in source
    assert "LIVE_JUDGMENTS = []" in source
    assert 'pending_score["precision"] is None' in source
    assert 'additional_score["fp"] == 0' in source
    assert 'score_review_findings(actual_findings, LIVE_JUDGMENTS)' in source
    assert "expected_ids=[]" in source


def test_checked_in_notebooks_match_builder_and_executed_run():
    generated = build_notebook()
    checked_in = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    assert checked_in == generated
    if (ROOT / "BUNDLE_MANIFEST.json").is_file() and not EXECUTED.is_file():
        pytest.skip("학생 코드 번들은 실행 출력 Notebook을 포함하지 않음")
    executed = json.loads(EXECUTED.read_text(encoding="utf-8"))
    assert len(executed["cells"]) == len(generated["cells"])
    assert _source(executed) == _source(generated)
    for cell in executed["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is not None
            assert all(output.get("output_type") != "error" for output in cell.get("outputs", []))
