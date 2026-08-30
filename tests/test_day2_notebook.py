"""Static behavior checks for the generated Day 2 notebook."""

from __future__ import annotations

from scripts.build_days2_5_notebooks import NOTEBOOKS


def _source_after_heading(heading: str) -> str:
    cells = NOTEBOOKS[2]["cells"]
    for index, cell in enumerate(cells[:-1]):
        source = "".join(cell["source"])
        if cell["cell_type"] == "markdown" and heading in source:
            next_cell = cells[index + 1]
            assert next_cell["cell_type"] == "code"
            return "".join(next_cell["source"])
    raise AssertionError(f"heading not found: {heading}")


def test_day2_has_eight_code_periods_and_all_cells_compile() -> None:
    headings = [
        "1차시 · Meeting Agent Architecture",
        "2차시 · Input Route · STT",
        "3차시 · Domain Context · MCP Policy",
        "4차시 · MeetingRecord Schema",
        "5차시 · Coding Agent Workflow",
        "6차시 · LLM Provider · Cost Guardrail",
        "7차시 · LangGraph · Human Review",
        "8차시 · Localhost App · 선택 Package",
    ]
    for heading in headings:
        compile(_source_after_heading(heading), f"day2-{heading}", "exec")
    assert NOTEBOOKS[2]["metadata"]["period_count"] == 8


def test_day2_run_all_is_network_and_external_write_free() -> None:
    architecture = _source_after_heading("1차시 · Meeting Agent Architecture")
    input_cell = _source_after_heading("2차시 · Input Route · STT")
    provider = _source_after_heading("6차시 · LLM Provider · Cost Guardrail")
    export = _source_after_heading("8차시 · Localhost App · 선택 Package")

    assert '"run_all_network_calls": 0' in architecture
    assert '"external_write": False' in architecture
    assert '"single_llm": route_execution_strategy' in architecture
    assert '"deterministic_workflow": route_execution_strategy' in architecture
    assert '"agent_router": route_execution_strategy' in architecture
    assert "EXTERNAL_ACTION_HUMAN_APPROVAL_REQUIRED" in architecture
    assert "reviewed_fixture_stt" in input_cell
    assert '"reviewed_transcript_fixture"' in input_cell
    assert "matched_audio_transcript_pair" in input_cell
    assert "FASTER_WHISPER_LIVE_OPT_IN" in input_cell
    assert "run_optional_local_stt_smoke" in input_cell
    assert "resolved_public_audio" in input_cell
    assert "load_dotenv(dotenv_path=ROOT / \".env\", override=False)" in provider
    assert 'openai_live_opt_in = os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1"' in provider
    assert 'env=os.environ if openai_live_opt_in else {}' in provider
    assert 'ollama_live_opt_in = os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1"' in provider
    assert "validate_model_record_output" in provider
    assert "OLLAMA_LIVE_OPT_IN_REQUIRED" in provider
    assert "MODEL_NOT_AVAILABLE" in provider
    assert 'item["send"] is False' in export
    assert '"human_review_required": True' in export
    assert '"external_write": False' in export
    assert '"scripts/run_day2_local_app.py"' in export
    assert '"--smoke-and-exit"' in export
    assert '"--port"' in export and '"0"' in export
    assert 'save_json("08_localhost_launch.json", localhost_report)' in export


def test_day2_outputs_use_the_v2_names_and_three_scenarios() -> None:
    all_source = "\n".join("".join(cell["source"]) for cell in NOTEBOOKS[2]["cells"])
    expected = [
        "01_architecture.json",
        "02_inputs.json",
        "03_domain_context.json",
        "04_meeting_record_contract.json",
        "05_workflow_runs.json",
        "06_provider_diagnostics.json",
        "07_human_review.json",
        "08_export_drafts.json",
        "08_localhost_launch.json",
    ]
    assert all(name in all_source for name in expected)
    assert all(
        scenario in all_source
        for scenario in ("google_meet_text", "clovanote_txt", "audio_stt")
    )
    assert 'REFERENCE_OUT = ROOT / "output/course-labs/day2-v2"' in all_source
    assert 'OUT = REFERENCE_OUT / "student-run"' in all_source
    assert 'OUT / "run_manifest.json"' in all_source
    assert '"run_started_at_utc"' in all_source
    assert '"python_version"' in all_source
    assert '"completed_periods"' in all_source
    assert '"result_files"' in all_source
    assert '"tests": RUN_TEST_EVIDENCE' in all_source
    assert '"return_code": result["returncode"]' in all_source
    assert '"status": "PASS" if result["returncode"] == 0 else "FAIL"' in all_source
    assert 'record_test_evidence("day2_focused", focused_test)' in all_source
    assert 'record_test_evidence("localhost_http_smoke", localhost_smoke)' in all_source
    assert '"this_run_network_free"' in all_source
    assert '"live_opt_ins"' in all_source


def test_day2_graph_and_mcp_plan_keep_human_boundary() -> None:
    workflow = _source_after_heading("5차시 · Coding Agent Workflow")
    context = _source_after_heading("3차시 · Domain Context · MCP Policy")
    review = _source_after_heading("7차시 · LangGraph · Human Review")
    record = _source_after_heading("4차시 · MeetingRecord Schema")

    for node in (
        "policy",
        "input_normalize",
        "stt_optional",
        "structure",
        "evidence",
        "human_review",
        "export_draft",
    ):
        assert node in workflow
    assert 'mcp_plan["executed"] is False' in context
    assert 'mcp_plan["external_write"] is False' in context
    assert "build_interruptible_meeting_graph" in review
    assert "start_interruptible_meeting_review" in review
    assert "resume_interruptible_meeting_review" in review
    assert '"pause": "interrupt()"' in review
    assert '"resume": "Command(resume=...)"' in review
    assert '"approve": {}' in review
    assert '"edit": {' in review
    assert '"reject": {}' in review
    assert "s999" in review
    assert "learner_start" in review
    assert "LEARNER_REVIEW_DECISION" in review
    assert "learner_resume" in review
    assert "automated_regression_evidence" in review
    assert review.index("learner_start") < review.index("LEARNER_REVIEW_DECISION")
    assert review.index("LEARNER_REVIEW_DECISION") < review.index("regression_runs")
    assert "unknown_evidence_s999" in record
    assert "owner_due_not_in_source" in record
    assert "TODO_DUE_DATE_INVALID" in record
    assert "MEETING_RECORD_ADDITIONAL_FIELD_FORBIDDEN" in record
