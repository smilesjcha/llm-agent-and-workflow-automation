"""Cross-artifact contract checks for the Day 3 classroom release."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "materials/day3/2026_Day3_수강생_실습가이드.md"
INSTRUCTOR = ROOT / "materials/day3/2026_Day3_강사용_상세교안.md"
CHECKLIST = ROOT / "materials/day3/2026_Day3_강의직전_체크리스트.md"
MAP = (
    ROOT
    / "design-system/ppt/cha-sungjae-lecture/content-harness/DAY3_MESSAGE_MAP.json"
)


def _course_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (GUIDE, INSTRUCTOR, CHECKLIST)
    )


def test_day3_docs_use_one_canonical_notebook_and_output_root() -> None:
    text = _course_text()

    assert "materials/day3/day3_review_intelligence_lab.ipynb" in text
    assert "materials/day3/day3_review_intelligence_lab.executed.ipynb" in text
    assert "output/course-labs/day3-v2/student-run/" in text
    for stale in (
        "day3_service_lab.ipynb",
        "data/day3_review_cases/",
        "lab/day3-<",
        "review_copilot/AGENTS.md",
    ):
        assert stale not in text


def test_day3_schedule_matches_the_shared_day2_to_day5_policy() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    rows = (
        "| 09:00-09:50 | 1차시 |",
        "| 09:50-10:40 | 2차시 |",
        "| 10:40-11:30 | 3차시 |",
        "| 11:30-13:00 | - | 쉬는 시간·점심시간 |",
        "| 13:00-13:50 | 4차시 |",
        "| 13:50-14:40 | 5차시 |",
        "| 14:40-15:00 | - | 쉬는 시간 |",
        "| 15:00-15:50 | 6차시 |",
        "| 15:50-16:40 | 7차시 |",
        "| 16:40-17:30 | 8차시 |",
        "| 17:30-18:00 | - | 쉬는 시간·Q&A·실습 복구 |",
    )
    assert all(row in text for row in rows)
    assert "14:00-15:00 | - | 점심" not in text


def test_day3_docs_keep_live_provider_and_github_writes_optional() -> None:
    text = _course_text()

    assert "RUN_OPTIONAL_LIVE_PROVIDER=True" in text
    assert "Draft PR" in text
    assert "자동 Merge" in text or "자동 merge" in text
    assert "external_write=false" in text
    assert "@codex review" in text
    assert "사람" in text


def test_day3_message_map_covers_every_slide_once() -> None:
    payload = json.loads(MAP.read_text(encoding="utf-8"))
    ranges = [block["range"] for block in payload["blocks"]]
    covered = [number for start, end in ranges for number in range(start, end + 1)]

    assert payload["deck"]["slideCount"] == 176
    assert covered == list(range(1, 177))
    assert payload["deck"]["finalSynthesisSlides"] == [172, 173, 174, 175, 176]


def test_day3_reference_outputs_have_eight_ordered_stages() -> None:
    output = ROOT / "output/course-labs/day3-v2"
    expected = [
        "01_review_contract.json",
        "02_parsed_diff.json",
        "03_context_pack.json",
        "04_candidate_review.json",
        "05_hybrid_review.json",
        "06_human_review.json",
        "07_evaluation.json",
        "08_release_evidence.json",
    ]

    assert all((output / name).is_file() for name in expected)
    release = json.loads((output / expected[-1]).read_text(encoding="utf-8"))
    assert release["decision"] == "READY_FOR_MANUAL_GITHUB_STEP"
    assert release["github_dry_run"]["commands_executed"] == []
    assert release["external_write"] is False
