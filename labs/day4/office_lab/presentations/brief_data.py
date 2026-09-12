"""Derive one slide-content source from the class WBS and review fixtures."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from labs.day4.office_lab.documents.resume_lab import DocumentLabError, workspace_path
from labs.day4.office_lab.sheets.student_excel import calculate_wbs


def prepare_brief(workspace: Path | str, *, as_of: str = "2026-09-25", tasks: list[dict] | None = None) -> dict:
    root = Path(workspace).resolve()
    wbs_source = "labs/day4/office_lab/sheets/wbs_tasks.json"
    review_source = "labs/day4/pr_review_lab/fixtures/findings.json"
    edited_input = tasks is not None
    raw_tasks = tasks if edited_input else json.loads(workspace_path(root, wbs_source).read_text(encoding="utf-8"))
    tasks = calculate_wbs(raw_tasks, as_of)
    if len(tasks) != 14:
        raise DocumentLabError("BRIEF_TASK_COUNT", "This 7-slide template requires 14 tasks")
    if edited_input:
        # Preserve provenance for edited Notebook inputs in the saved brief.
        wbs_source = "Notebook WBS input snapshot"
    reviews = json.loads(workspace_path(root, review_source).read_text(encoding="utf-8"))
    statuses = Counter(task["status"] for task in tasks)
    wbs_rows = [[task["id"] + " " + task["task"], task["start"][5:] + " ~ " + task["end"][5:], task["status"], f"{task['progress']:.0%}"] for task in tasks]
    review_rows = [[item["severity"], item["title"], item["suggestion"]] for item in reviews]
    return {
        "schema_version": 1,
        "project": "PR 리뷰와 문서 자동화 도입",
        "as_of": as_of,
        "synthetic": True,
        "sources": [wbs_source, review_source],
        "wbs_snapshot": raw_tasks,
        "slides": [
            {"title": "PR 리뷰와\n문서 자동화 도입", "subtitle": f"진행 현황 보고  {as_of}", "note": "수업용 합성 프로젝트. 일정과 진행률은 연습 데이터이며 실제 회사 운영 현황이 아닙니다."},
            {"title": "일정 현황", "subtitle": f"전체 {len(tasks)}개 업무  기준일 {as_of}", "table": [["상태", "업무 수", "확인 사항"], ["완료", str(statuses['완료']), "결과 파일과 검증 기록 확인"], ["진행 중", str(statuses['진행 중']), "마감일까지 잔여 작업 확인"], ["지연", str(statuses['지연']), "종료일 경과 및 미완료 업무"], ["예정", str(statuses['예정']), "선행 작업과 착수 조건 확인"]]},
            {"title": "개발 작업 일정", "subtitle": "리뷰 수집부터 승인과 Word 템플릿까지", "table": [["업무", "기간", "상태", "완료율"], *wbs_rows[:7]]},
            {"title": "문서 자동화와 출시 일정", "subtitle": "Excel 및 PPT 제작과 출시 점검", "table": [["업무", "기간", "상태", "완료율"], *wbs_rows[7:]]},
            {"title": "코드 리뷰 확인 사항", "subtitle": "checkout.py 수업용 PR의 재현 가능한 오류", "table": [["등급", "오류", "최소 수정"], *review_rows], "note": "findings.json의 결정적 fixture를 재현한 사례입니다. 이번 보고서에서 새로 모델을 호출하거나 실제 PR에 게시하지 않았습니다."},
            {"title": "산출물 검토 기준", "table": [["산출물", "코드 검사", "사람 확인"], ["리뷰 코멘트", "파일 및 변경 줄 일치", "영향과 수정 제안 타당성"], ["Word 이력서", "새 수치 및 원본 보존", "경력 사실과 표현"], ["Excel WBS", "수식 및 날짜 입력 검증", "일정과 담당 Role"], ["PPT 보고서", "원본 수치와 표 일치", "가독성과 의사결정 맥락"]]},
            {"title": "다음 작업과 승인 사항", "subtitle": "미완료 업무의 일정 조정과 게시 전 검토", "bullets": ["W04 리뷰 초안과 W05 테스트 작업의 지연 원인 확인", "W06 사람 승인 절차와 중복 게시 방지 점검", "W08 Excel 입력을 수정한 뒤 보고서 재생성", "외부 게시와 배포는 담당자 확인 후 별도 진행"]}
        ]
    }


def write_brief(workspace: Path | str, output: str, *, as_of: str = "2026-09-25", tasks: list[dict] | None = None) -> Path:
    path = workspace_path(workspace, output)
    if path.suffix.lower() != ".json":
        raise DocumentLabError("INVALID_OUTPUT_EXTENSION")
    if path.exists():
        raise DocumentLabError("OUTPUT_EXISTS", path.name)
    data = prepare_brief(workspace, as_of=as_of, tasks=tasks)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        json.dump(data, target, ensure_ascii=False, indent=2)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--as-of", default="2026-09-25")
    args = parser.parse_args()
    print(write_brief(Path.cwd(), args.output, as_of=args.as_of))
