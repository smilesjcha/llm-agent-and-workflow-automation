"""Day 4 slide ordering and the 400-minute teaching contract; no rendering."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "scripts/slides/day4_plan.mjs"
CONTENT = ROOT / "scripts/slides/day4_document_content.mjs"
CATALOG = ROOT / "scripts/slides/day4_project_catalog.mjs"

SYNTHETIC_INPUT = """
function input() {
  const opening = Array.from({length: 7}, (_, i) => ({
    type: 'points', title: `Opening ${i}`, phase: 'theory'
  }));
  const periods = Array.from({length: 8}, (_, i) => ({
    title: `Period ${i + 1}`, theory: 12, demo: 8, lab: 25, check: 5
  }));
  const lessons = periods.map((_, i) => [
    {type: 'points', title: `Theory ${i}`, phase: 'theory'},
    {type: 'code', title: `Demo ${i}`, phase: 'demo'},
    {type: 'task', title: `Lab ${i}`, phase: 'lab'},
    {type: 'table', title: `Check ${i}`, phase: 'check'},
  ]);
  return {opening, periods, lessons};
}
function messageFrom(action) {
  try { action(); return null; }
  catch (error) { return error.message; }
}
function describe(result) {
  return {
    total: result.total,
    count: result.plan.length,
    periods: Array.from({length: 8}, (_, p) => result.plan
      .filter(item => (item.p ?? 0) === p)
      .reduce((sum, item) => sum + item.minutes, 0)),
    openingMinutes: result.plan.filter(item => item.p === null)
      .reduce((sum, item) => sum + item.minutes, 0),
    halfMinuteSteps: result.plan.every(item =>
      item.minutes >= 0 && Number.isInteger(item.minutes * 2)),
    ranges: result.ranges,
  };
}
"""


@pytest.fixture(scope="module")
def node_executable():
    executable = shutil.which("node")
    assert executable, "Day 4 curriculum checks require Node.js on PATH."
    return executable


def run_node(node_executable: str, body: str) -> dict | list | str | None:
    """Import only pure curriculum modules, never the PPT authoring runtime."""
    source = (
        "import {insertLessonAdditions, buildDay4Plan} from "
        + json.dumps(PLAN.as_uri())
        + ";\n"
        + SYNTHETIC_INPUT
        + body
    )
    process = subprocess.run(
        [node_executable, "--input-type=module", "-e", source],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
    )
    assert process.returncode == 0, process.stderr[-2000:]
    return json.loads(process.stdout)


def test_insert_preserves_anchor_order_and_marks_additions(node_executable):
    result = run_node(node_executable, """
const {lessons} = input();
const original = lessons[0][0];
const addition = {type: 'code', title: 'Walkthrough', phase: 'lab'};
insertLessonAdditions(lessons, [{period: 0, after: 'Theory 0', slides: [
  addition, {type: 'task', title: 'Recovery', phase: 'lab'}
]}]);
console.log(JSON.stringify({
  titles: lessons[0].map(slide => slide.title),
  added: lessons[0].filter(slide => slide.expanded).map(slide => slide.title),
  originalPreserved: lessons[0][0] === original,
  additionUnchanged: addition.expanded === undefined,
  otherPeriodCount: lessons[1].length,
}));
""")
    assert result == {
        "titles": ["Theory 0", "Walkthrough", "Recovery", "Demo 0", "Lab 0", "Check 0"],
        "added": ["Walkthrough", "Recovery"],
        "originalPreserved": True,
        "additionUnchanged": True,
        "otherPeriodCount": 4,
    }


def test_missing_anchor_rejected_before_insertion(node_executable):
    result = run_node(node_executable, """
const {lessons} = input();
const error = messageFrom(() => insertLessonAdditions(lessons, [{
  period: 0, after: 'Missing title',
  slides: [{type: 'code', title: 'New slide', phase: 'lab'}]
}]));
console.log(JSON.stringify({error, length: lessons[0].length}));
""")
    assert result["error"].startswith("DAY4_ANCHOR_MISSING:")
    assert result["length"] == 4


@pytest.mark.parametrize("titles", [["Theory 0"], ["Theory 7"], ["New title", "New title"]])
def test_duplicate_titles_rejected_within_or_across_periods(node_executable, titles):
    result = run_node(node_executable, """
const {lessons} = input();
const titles = """ + json.dumps(titles) + """;
const error = messageFrom(() => insertLessonAdditions(lessons, [{
  period: 0, after: 'Theory 0',
  slides: titles.map(title => ({type: 'code', title, phase: 'lab'}))
}]));
console.log(JSON.stringify({error, length: lessons[0].length}));
""")
    assert result["error"].startswith("DAY4_DUPLICATE_TITLE:")
    assert result["length"] == 4


@pytest.mark.parametrize("group", [
    {"period": 8, "after": "Theory 0", "slides": [{"title": "Outside"}]},
    {"period": 0, "after": "Theory 0", "slides": []},
])
def test_invalid_addition_rejected(node_executable, group):
    result = run_node(node_executable, """
const {lessons} = input();
console.log(JSON.stringify(messageFrom(() =>
  insertLessonAdditions(lessons, [""" + json.dumps(group) + "]))))")
    assert result == "INVALID_DAY4_ADDITION"


def test_plan_allocates_50_minutes_per_period_including_opening(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
console.log(JSON.stringify(describe(buildDay4Plan(opening, lessons, periods))));
""")
    assert result["total"] == 400
    assert result["periods"] == [50] * 8
    assert result["openingMinutes"] == 5
    assert result["halfMinuteSteps"] is True
    assert len(result["ranges"]) == 8


def test_reference_slides_take_no_teaching_minutes(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
lessons[7].push(...Array.from({length: 50}, (_, i) => ({
  type: 'table', title: `Optional ${i}`, reference: true,
  activityLabel: 'Ideation · 선택 참고', phase: 'theory'
})));
const result = buildDay4Plan(opening, lessons, periods);
console.log(JSON.stringify({
  ...describe(result),
  optional: result.plan.filter(item => item.d.reference).map(item => item.minutes)
}));
""")
    assert result["total"] == 400
    assert result["periods"] == [50] * 8
    assert result["optional"] == [0] * 50


def test_phase_over_budget_rejected_instead_of_zero_minute_teaching(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
lessons[0].push(...Array.from({length: 20}, (_, i) => ({
  type: 'points', title: `Too much theory ${i}`, phase: 'theory'
})));
console.log(JSON.stringify(messageFrom(() =>
  buildDay4Plan(opening, lessons, periods))));
""")
    assert result == "TOO_MANY_SLIDES_FOR_TIMING: theory"


def test_budget_without_matching_phase_is_rejected(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
lessons[3] = lessons[3].filter(slide => slide.phase !== 'lab');
console.log(JSON.stringify(messageFrom(() =>
  buildDay4Plan(opening, lessons, periods))));
""")
    assert result == "MISSING_TIMING_PHASE: lab"


@pytest.mark.parametrize("shorten", ["opening", "lessons", "periods"])
def test_changed_course_structure_is_rejected(node_executable, shorten):
    result = run_node(node_executable, """
const args = input();
args[""" + json.dumps(shorten) + """].pop();
console.log(JSON.stringify(messageFrom(() =>
  buildDay4Plan(args.opening, args.lessons, args.periods))));
""")
    assert result == "DAY4_STRUCTURE_CHANGED"


def test_non_400_total_is_rejected(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
periods[2].lab += 1;
console.log(JSON.stringify(messageFrom(() =>
  buildDay4Plan(opening, lessons, periods))));
""")
    assert result == "TIMING_NOT_400: 401"


def test_equal_total_does_not_hide_unbalanced_periods(node_executable):
    result = run_node(node_executable, """
const {opening, lessons, periods} = input();
periods[0].lab += 1;
periods[1].lab -= 1;
console.log(JSON.stringify(messageFrom(() =>
  buildDay4Plan(opening, lessons, periods))));
""")
    assert result == "PERIOD_NOT_50: 1"


@pytest.fixture(scope="module")
def integrated_curriculum(node_executable):
    return run_node(node_executable, """
const {OPENING, LESSONS, PERIODS} = await import(""" + json.dumps(CONTENT.as_uri()) + """);
const {PROJECT_CATEGORIES} = await import(""" + json.dumps(CATALOG.as_uri()) + """);
const result = buildDay4Plan(OPENING, LESSONS, PERIODS);
const names = new Set(PROJECT_CATEGORIES.map(category => category.name));
console.log(JSON.stringify({
  ...describe(result),
  expanded: LESSONS.map(items => items.filter(slide => slide.expanded).length),
  referenceCount: result.plan.filter(item => item.d.reference).length,
  titles: LESSONS.flat().map(slide => slide.title),
  catalog: result.plan.filter(item => names.has(item.d.title)).map(item => ({
    title: item.d.title, reference: item.d.reference,
    activityLabel: item.d.activityLabel, phase: item.d.phase,
    minutes: item.minutes, rows: item.d.rows.length,
  })),
  categoryCount: PROJECT_CATEGORIES.length,
  breaks: result.plan.filter(item => item.d.type === 'break').map(item => ({
    time: item.d.time, minutes: item.minutes
  })),
  sections: result.ranges.map(([start, end], p) => ({
    start, end, period: p, firstType: result.plan[start - 1].d.type,
    lastPeriod: result.plan[end - 1].p,
  })),
  requiredSlideMinutes: result.plan.filter(item =>
    item.p !== null && !item.d.reference && item.d.type !== 'break'
  ).map(item => item.minutes),
}));
""")


def test_integrated_deck_has_200_slides_and_55_additions(integrated_curriculum):
    result = integrated_curriculum
    assert result["count"] == 200
    assert result["expanded"] == [5, 5, 5, 6, 6, 6, 6, 16]
    assert sum(result["expanded"]) == 55
    assert result["referenceCount"] == 27
    assert len(result["titles"]) == len(set(result["titles"]))


def test_integrated_eight_periods_remain_50_minutes(integrated_curriculum):
    result = integrated_curriculum
    assert result["total"] == 400
    assert result["periods"] == [50] * 8
    assert result["openingMinutes"] == 5
    assert result["halfMinuteSteps"] is True
    assert all(minutes >= 0.5 for minutes in result["requiredSlideMinutes"])


def test_integrated_project_catalog_is_optional_ideation(integrated_curriculum):
    result = integrated_curriculum
    assert result["categoryCount"] == 9
    assert len(result["catalog"]) == 9
    assert len({slide["title"] for slide in result["catalog"]}) == 9
    for slide in result["catalog"]:
        assert slide["reference"] is True
        assert slide["activityLabel"].startswith("Ideation")
        assert slide["phase"] != "lab"
        assert slide["minutes"] == 0
        assert slide["rows"] == 4


def test_integrated_breaks_and_ranges_preserve_course_schedule(integrated_curriculum):
    result = integrated_curriculum
    assert result["ranges"] == [
        [8, 28], [29, 52], [53, 74], [76, 98],
        [99, 121], [123, 144], [145, 166], [167, 199],
    ]
    assert result["breaks"] == [
        {"time": "11:30–13:00", "minutes": 0},
        {"time": "14:40–15:00", "minutes": 0},
        {"time": "17:30–18:00", "minutes": 0},
    ]
    assert len(result["sections"]) == 8
    previous_end = 7
    for section in result["sections"]:
        assert section["start"] > previous_end
        assert section["end"] >= section["start"]
        assert section["firstType"] == "section"
        assert section["lastPeriod"] == section["period"]
        previous_end = section["end"]
