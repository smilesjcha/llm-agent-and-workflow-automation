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
        "1차시 · 회의 Agent 전체 지도",
        "2차시 · 세 가지 입력과 STT 선택",
        "3차시 · 도메인 맥락과 MCP 정책",
        "4차시 · MeetingRecord 결과 계약",
        "5차시 · Codex·Claude 시나리오 설계",
        "6차시 · LLM Provider와 비용 경계",
        "7차시 · LangGraph 사람 검증",
        "8차시 · Desktop 선물 패키지",
    ]
    for heading in headings:
        compile(_source_after_heading(heading), f"day2-{heading}", "exec")
    assert NOTEBOOKS[2]["metadata"]["period_count"] == 8


def test_day2_run_all_is_network_and_external_write_free() -> None:
    architecture = _source_after_heading("1차시 · 회의 Agent 전체 지도")
    input_cell = _source_after_heading("2차시 · 세 가지 입력과 STT 선택")
    provider = _source_after_heading("6차시 · LLM Provider와 비용 경계")
    export = _source_after_heading("8차시 · Desktop 선물 패키지")

    assert '"run_all_network_calls": 0' in architecture
    assert '"external_write": False' in architecture
    assert "reviewed_fixture_stt" in input_cell
    assert "matched_audio_transcript_pair" in input_cell
    assert "RUN_OPENAI_LIVE = False" in provider
    assert 'env=os.environ if RUN_OPENAI_LIVE else {}' in provider
    assert "MODEL_NOT_AVAILABLE" in provider
    assert 'item["send"] is False' in export
    assert '"human_review_required": True' in export
    assert '"external_write": False' in export


def test_day2_outputs_use_the_v2_names_and_three_scenarios() -> None:
    all_source = "\n".join("".join(cell["source"]) for cell in NOTEBOOKS[2]["cells"])
    expected = [
        "01_architecture.json",
        "02_inputs.json",
        "03_domain_context.json",
        "04_strategy_compare.json",
        "05_workflow_runs.json",
        "06_provider_diagnostics.json",
        "07_human_review.json",
        "08_export_drafts.json",
    ]
    assert all(name in all_source for name in expected)
    assert all(
        scenario in all_source
        for scenario in ("google_meet_text", "clovanote_txt", "audio_stt")
    )
    assert 'OUT = ROOT / "output/course-labs/day2-v2"' in all_source


def test_day2_graph_and_mcp_plan_keep_human_boundary() -> None:
    workflow = _source_after_heading("5차시 · Codex·Claude 시나리오 설계")
    context = _source_after_heading("3차시 · 도메인 맥락과 MCP 정책")
    review = _source_after_heading("7차시 · LangGraph 사람 검증")

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
    assert 'review_decision="approve"' in review
    assert 'review_decision="edit"' in review
    assert 'review_decision="reject"' in review
    assert "s999" in review
