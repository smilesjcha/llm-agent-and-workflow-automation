"""Static and execution-contract checks for the canonical Day 3 notebook."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_day3_notebook import build_notebook


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "materials/day3/day3_review_intelligence_lab.ipynb"
EXECUTED = ROOT / "materials/day3/day3_review_intelligence_lab.executed.ipynb"


def _source(notebook: dict) -> str:
    return "\n".join("".join(cell["source"]) for cell in notebook["cells"])


def test_day3_notebook_has_eight_periods_and_compilable_code() -> None:
    notebook = build_notebook()
    source = _source(notebook)

    for number, title in (
        (1, "Review Contract"),
        (2, "Unified Diff"),
        (3, "Context Pack"),
        (4, "Provider Adapter"),
        (5, "Hybrid Review"),
        (6, "Human Review · LangGraph"),
        (7, "Golden Evaluation"),
        (8, "Local Service · GitHub PR"),
    ):
        assert f"# {number}차시 · {title}" in source

    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"day3-cell-{index}", "exec")

    assert notebook["metadata"]["period_count"] == 8
    assert len(notebook["cells"]) >= 40


def test_day3_notebook_uses_canonical_service_and_output_contract() -> None:
    source = _source(build_notebook())
    expected_outputs = [
        "01_review_contract.json",
        "02_parsed_diff.json",
        "03_context_pack.json",
        "04_candidate_review.json",
        "05_hybrid_review.json",
        "06_human_review.json",
        "07_evaluation.json",
        "08_release_evidence.json",
        "review_report.md",
        "run_manifest.json",
    ]

    assert "labs.day3.review_copilot" in source
    assert 'REFERENCE_OUT = ROOT / "output/course-labs/day3-v2"' in source
    assert 'OUT = REFERENCE_OUT / "student-run"' in source
    assert all(name in source for name in expected_outputs)
    assert "src.course_services.review_service" not in source
    assert "output/course-labs/day3\"" not in source


def test_day3_run_all_keeps_live_and_external_actions_opt_in() -> None:
    source = _source(build_notebook())

    assert "RUN_OPTIONAL_LIVE_PROVIDER = False" in source
    assert "RUN_LOCALHOST_SMOKE = False" in source
    assert 'os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1"' in source
    assert 'os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1"' in source
    assert '"credential_value_recorded": False' in source
    assert '"external_write": False' in source
    assert '"automatic_pr_comment": False' in source
    assert '"automatic_merge": False' in source
    assert 'release["github_dry_run"]["commands_executed"] == []' in source
    assert "git push -u origin HEAD" in source
    assert "사람 실행 구간" in source


def test_day3_notebook_contains_normal_and_boundary_evidence() -> None:
    source = _source(build_notebook())

    for error_code in (
        "FINDING_SEVERITY_INVALID",
        "DIFF_PATH_BLOCKED",
        "WORKSPACE_PATH_BLOCKED",
        "OPENAI_NOT_CONFIGURED",
        "LIVE_PROVIDER_OPT_IN_REQUIRED",
    ):
        assert error_code in source
    assert "invented_line_removed" in source
    assert 'evaluation["case_count"] == 8' in source
    assert 'evaluation["false_positive"] == 0' in source
    assert 'evaluation["false_negative"] == 0' in source


def test_day3_notebook_includes_direct_coding_and_decision_propagation() -> None:
    source = _source(build_notebook())

    for learner_function in (
        "def learner_added_line_map",
        "def learner_public_context",
        "def learner_grounded_candidates",
        "def learner_review_metrics",
    ):
        assert learner_function in source
    assert 'decision=None' in source
    assert "decision=REVIEW_DECISION" in source
    assert "edited_findings=REVIEW_EDITED_FINDINGS" in source
    assert '"human_review_decision": REVIEW_DECISION' in source
    assert 'else "HOLD"' in source


def test_day3_langgraph_interrupt_precedes_learner_resume() -> None:
    source = _source(build_notebook())

    start = source.index("graph_start = review_graph.invoke")
    decision = source.index('REVIEW_DECISION = "approve"')
    resume = source.index("Command(resume=resume_payload)")
    assert start < decision < resume
    assert 'REVIEW_THREAD_ID = "day3-learner-review-001"' in source
    assert '"external_write": False' in source


def test_checked_in_notebooks_match_builder_and_executed_run() -> None:
    generated = build_notebook()
    checked_in = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    executed = json.loads(EXECUTED.read_text(encoding="utf-8"))

    assert checked_in == generated
    assert len(executed["cells"]) == len(checked_in["cells"])
    code_cells = [cell for cell in executed["cells"] if cell["cell_type"] == "code"]
    assert all(cell["execution_count"] is not None for cell in code_cells)
    assert all(
        output.get("output_type") != "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    )
