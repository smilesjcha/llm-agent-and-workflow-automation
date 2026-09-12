from copy import deepcopy
from pathlib import Path
import shutil
import pytest

from labs.day4.office_lab.sheets.student_excel import (
    _safe_path, calculate_wbs, grade_exam, load_sample, validate_wbs,
    write_exam_copy, write_grade_csv, write_wbs_copy,
)

ROOT = Path(__file__).resolve().parents[1]


def test_wbs_status_and_weekday_count():
    tasks = load_sample("wbs_tasks.json")
    assert validate_wbs(tasks) == []
    result = calculate_wbs(tasks, "2026-09-25")
    assert result[3]["status"] == "지연"
    assert result[5]["working_days"] == 3
    tasks[3]["progress"] = 1
    assert calculate_wbs(tasks, "2026-09-25")[3]["status"] == "완료"


@pytest.mark.parametrize(("field", "value", "code"), [
    ("end", "2026-09-01", "END_BEFORE_START"),
    ("progress", None, "INVALID_PROGRESS"),
    ("progress", True, "INVALID_PROGRESS"),
    ("progress", 1.1, "INVALID_PROGRESS"),
    ("predecessor", "W99", "INVALID_PREDECESSOR"),
    ("role", "", "REQUIRED_INPUT_MISSING"),
])
def test_wbs_input_failures(field, value, code):
    tasks = load_sample("wbs_tasks.json")
    tasks[0][field] = value
    assert code in [item["code"] for item in validate_wbs(tasks)]
    with pytest.raises(ValueError, match="WBS_INPUT_INVALID"):
        calculate_wbs(tasks, "2026-09-25")


def test_dependency_cycle_and_duplicate_id():
    tasks = load_sample("wbs_tasks.json")
    tasks[0]["predecessor"] = "W02"
    assert "DEPENDENCY_CYCLE" in [x["code"] for x in validate_wbs(tasks)]
    tasks[0]["id"] = "W02"
    assert "DUPLICATE_TASK_ID" in [x["code"] for x in validate_wbs(tasks)]


def test_exam_normal_missing_invalid_absent_and_tied_rank():
    result = grade_exam(load_sample("exam_sample.json"))
    rows = result["students"]
    assert result["eligible_count"] == 26
    assert rows[0]["score"] == 20
    assert rows[24]["status"] == "미응답 포함"
    assert rows[24]["blank_count"] == 2
    assert rows[25]["score"] is None and rows[25]["status"] == "입력 오류"
    assert rows[27]["score"] is None and rows[27]["status"] == "결시"
    assert rows[0]["rank"] == rows[26]["rank"]
    assert result["questions"][0]["denominator"] == 26


def test_exam_key_change_repair_and_missing_key():
    sample = load_sample("exam_sample.json")
    before = grade_exam(sample)
    sample["key"][0] = 2
    changed = grade_exam(sample)
    assert changed["students"][0]["score"] == before["students"][0]["score"] - 1
    assert changed["questions"][0]["rate"] != before["questions"][0]["rate"]
    sample["students"][25]["answers"][8] = 1
    assert grade_exam(sample)["eligible_count"] == 27
    sample["key"][0] = None
    result = grade_exam(sample)
    assert result["eligible_count"] == 0
    assert result["mean"] is None and result["questions"][0]["rate"] is None
    assert result["students"][0]["status"] == "정답 확인"


@pytest.mark.parametrize("value", [0, 5, 1.5, "1", True, "잘못된 값"])
def test_invalid_answer_is_not_a_valid_zero_score(value):
    sample = load_sample("exam_sample.json")
    sample["students"][0]["answers"][0] = value
    assert grade_exam(sample)["students"][0]["score"] is None


def test_zero_score_is_valid_and_duplicate_id_is_blocked():
    sample = load_sample("exam_sample.json")
    sample["students"][0]["answers"] = [value % 4 + 1 for value in sample["key"]]
    assert grade_exam(sample)["students"][0]["score"] == 0
    sample["students"][0]["id"] = sample["students"][1]["id"]
    assert grade_exam(sample)["students"][0]["status"] == "ID 확인"


def test_safe_path_including_symlink_escape(tmp_path):
    with pytest.raises(ValueError, match="PATH_OUTSIDE_WORKSPACE"):
        _safe_path(tmp_path, "../outside.xlsx")
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError, match="PATH_OUTSIDE_WORKSPACE"):
        _safe_path(tmp_path, "escape/outside.xlsx")


def _templates(tmp_path):
    target = tmp_path / "outputs/day4-document-automation"
    target.mkdir(parents=True)
    for filename in ["WBS_Gantt.xlsx", "Exam_Grading.xlsx"]:
        shutil.copy2(ROOT / "outputs/day4-document-automation" / filename, target / filename)


def test_student_copies_keep_formulas_and_conditional_formats(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    _templates(tmp_path)
    tasks = load_sample("wbs_tasks.json")
    tasks[3]["progress"] = 1
    result = write_wbs_copy(tmp_path, tasks, "2026-09-25")
    sheet = openpyxl.load_workbook(result)["WBS"]
    assert sheet["F12"].value == 1
    assert "NETWORKDAYS" in sheet["H12"].value
    assert len(sheet.conditional_formatting) >= 3
    with pytest.raises(FileExistsError, match="OUTPUT_ALREADY_EXISTS"):
        write_wbs_copy(tmp_path, tasks, "2026-09-25")
    exam = load_sample("exam_sample.json")
    exam["students"][25]["answers"][8] = 1
    output = write_exam_copy(tmp_path, exam)
    book = openpyxl.load_workbook(output)
    assert book["채점"]["L35"].value == 1
    assert book["채점"]["AR10"].value.startswith("=IF(")
    assert book.calculation.fullCalcOnLoad
    assert len(book["채점"].conditional_formatting) >= 4
    formulas = [rule.formula[0] for group in book["채점"].conditional_formatting
                for rule in book["채점"].conditional_formatting[group] if rule.formula]
    assert any('D$45="등록"' in formula for formula in formulas)


def test_report_contains_human_readable_status_and_no_overwrite(tmp_path):
    output = write_grade_csv(tmp_path, load_sample("exam_sample.json"))
    assert "입력 오류" in output.read_text(encoding="utf-8-sig")
    assert "S028,결시" in output.read_text(encoding="utf-8-sig")
    with pytest.raises(FileExistsError):
        write_grade_csv(tmp_path, load_sample("exam_sample.json"))


def test_spreadsheet_formula_injection_stays_literal(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    _templates(tmp_path)
    tasks = load_sample("wbs_tasks.json")
    tasks[0]["task"] = '=HYPERLINK("https://example.invalid","unexpected")'
    path = write_wbs_copy(tmp_path, tasks, "2026-09-25")
    cell = openpyxl.load_workbook(path)["WBS"]["B9"]
    assert cell.data_type == "s"
    exam = load_sample("exam_sample.json")
    exam["students"][0]["id"] = "=1+1"
    report = write_grade_csv(tmp_path, exam)
    assert "'=1+1" in report.read_text(encoding="utf-8-sig")
