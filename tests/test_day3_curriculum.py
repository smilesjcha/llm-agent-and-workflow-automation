"""Cross-artifact contracts for the Codex CLI Day 3 redesign."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "materials/day3/day3_redesign_curriculum.json"
MAP = ROOT / "design-system/ppt/cha-sungjae-lecture/content-harness/DAY3_MESSAGE_MAP.json"

def curriculum() -> dict:
    return json.loads(CURRICULUM.read_text(encoding="utf-8"))

def test_day3_schedule_has_eight_full_periods_and_end_of_block_breaks() -> None:
    data = curriculum()
    assert [p["time"] for p in data["periods"]] == [
        "09:00-09:50", "09:50-10:40", "10:40-11:30", "13:00-13:50",
        "13:50-14:40", "15:00-15:50", "15:50-16:40", "16:40-17:30",
    ]
    assert all(sum(part["minutes"] for part in p["agenda"]) == 50 for p in data["periods"])
    assert [b["time"] for b in data["breaks"]] == ["11:30-13:00", "14:40-15:00", "17:30-18:00"]

def test_original_40h_and_future_individual_project_remain_visible() -> None:
    data = curriculum()
    assert sum(m["hours"] for m in data["original_modules"]) == 40
    assert len(data["roadmap"]) == 5
    assert len(data["week4"]) == len(data["week5"]) == 8
    assert "150분" in data["mini_project"]["minutes"]
    assert "30분" in data["mini_project"]["minutes"]
    assert "발표 강제 없음" in data["mini_project"]["sharing"]

def test_each_period_has_real_coding_steps_not_only_json_or_web_browsing() -> None:
    data = curriculum()
    assert data["primary_provider"] == "codex_cli"
    for p in data["periods"]:
        assert len(p["lab_steps"]) >= 5
        assert len(p["theory"]) >= 4
        assert p["codex_task"] and p["completion"] and p["files"]
        assert any(word in " ".join(p["lab_steps"]) for word in ("실행", "Test", "구현", "작성", "검증"))
    assert "JSON" in data["opening"]["json_role"]

def test_student_docs_use_canonical_notebook_and_explicit_live_mode() -> None:
    text = (ROOT / "materials/day3/2026_Day3_수강생_실습가이드.md").read_text(encoding="utf-8")
    assert "day3_review_intelligence_lab.ipynb" in text
    assert "RUN_CODEX_LIVE" in text and "codex login status" in text
    assert "fixture" in text.lower() or "예제" in text
    assert "checkout.py" in text and "checkout_checks.py" in text
    assert "LangGraph" in text and "Codex" in text

def test_deck_message_map_has_full_coverage_and_exact_time_budget() -> None:
    if not MAP.exists():
        pytest.skip("슬라이드 검증 자료는 code-only ZIP에 포함하지 않음")
    data = json.loads(MAP.read_text(encoding="utf-8"))
    count = data["deck"]["slideCount"]
    covered = [n for b in data["blocks"] for n in range(b["range"][0], b["range"][1] + 1)]
    assert covered == list(range(1, count + 1))
    assert [p["page"] for p in data["slides"]] == covered
    assert sum(p["minutes"] for p in data["slides"]) == 430
    assert data["timing"]["teachingMinutes"] == 400
    assert data["deck"]["finalSynthesisSlides"] == [count]
    assert "CODEX_CLI" in data["deck"]["path"]
    assert data["design"]["bodyPoint"] >= 20
    assert data["design"]["tablePoint"] >= 19
    assert len(data["requiredNativeTables"]) >= 15
    for period in range(1, 9):
        pages = [p for p in data["slides"] if p["period"] == period]
        assert any(p["lab"] for p in pages)
        assert any(p["type"] == "conversation" for p in pages)

def test_architecture_distinguishes_reviewer_adapter_from_coding_agent() -> None:
    source = (ROOT / "assets/components/day3/master-code-review-agent.mmd").read_text(encoding="utf-8")
    assert source.startswith("flowchart LR")
    assert "Codex CLI" in source and "LangGraph" in source
    assert "대화형 Codex" in source and "제공된 Context" in source
    assert "4주차" in source and "5주차" in source
    assert "사람 확인 후 게시" in source
