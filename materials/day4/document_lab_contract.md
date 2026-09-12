# 4주차 Word와 PPT 자동화 실습

Word 차시에서는 경력 문장을 고친 뒤 실제 `.docx`를 만들고, PPT 차시에서는 앞서 수정한 WBS 입력으로 보고서를 다시 만듭니다. JSON은 중간 데이터입니다. 최종 확인 대상은 Word 문서와 편집 가능한 PowerPoint 파일입니다.

## 예시의 출처

- 이력서는 사용자가 대화에서 제공한 산업별 경력으로 구성한 **수업 예시**입니다. 개인 원본 이력서를 가져오거나 수정한 결과가 아닙니다.
- 이름, 연락처, 근무 기간, 학위, 매출 개선율은 넣지 않았습니다. 제공되지 않은 사실을 문장 다듬기 과정에서 추가하지 않습니다.
- 약 7만명, 3~5일, 10초 내외는 사용자의 진술입니다. 별도 검증 전이므로 개선본에서 수치 확인이 필요함을 표시했습니다.
- PPT는 `PR 리뷰와 문서 자동화 도입`이라는 수업용 프로젝트입니다. WBS와 동일한 14개 업무를 사용하며 일정은 2026년 9월 14일~10월 9일, 상태 계산 기준일은 9월 25일입니다. 실제 회사 프로젝트의 성과 보고가 아닙니다.
- 아래 Codex/Claude 대화는 **학생이 입력할 요청 예시**입니다. 실제 계정에서 수행한 대화나 모델 응답 캡처로 제시하지 않습니다.

## 준비물

| 구분 | 준비 | 확인 방법 |
|---|---|---|
| Python | 기존 수업 가상환경과 python-docx | `python -c "import docx; print(docx.__version__)"` |
| Node.js | Node.js LTS와 npm | `node --version` 및 `npm --version` |
| PPT 생성 | PptxGenJS 4.x | 아래 설치 명령 실행 |
| 문서 열기 | Word/PowerPoint 또는 LibreOffice | 제공된 Before와 PPT 파일 열기 |
| 한글 폰트 | NanumGothic 권장 | 문서 앱의 글꼴 목록 확인<br>미설치 시 사용 가능한 한글 글꼴로 코드의 `NanumGothic` 변경 |
| 대화형 개선 | Codex 또는 Claude에서 실습 폴더 선택 | 없는 경력 생성 금지, 파일 저장 경로 확인 |

```bash
python -m pip install "python-docx>=1.1,<2"
npm install --prefix labs/day4/office_lab/presentations
```

계정이나 유료 API 없이 제공 코드의 생성과 검증을 실행할 수 있습니다. Codex/Claude와 추가로 대화하는 기능은 각 계정의 이용 조건과 한도를 따릅니다.

## 6차시 Word 자동화 50분

| 구간 | 내용 | 학생의 작업 | 파일과 확인 |
|---|---|---|---|
| 0~8분 | 문서 구조와 사실 보존 | 개선 전후 문서에서 동일한 경력 비교 | `Resume_Before.docx`<br>`Resume_After.docx` |
| 8~15분 | Word 스타일 | Title, Heading, List Bullet의 차이 확인 | 글꼴만 바꾸기와 구조 변경 구분 |
| 15~25분 | 원문과 수정안 연결 | fact ID를 고른 뒤 해당 문장만 수정 | `career_facts.json`<br>없는 수치와 근무 기간 추가 금지 |
| 25~37분 | Word 생성 코드 | Notebook에서 `build_resume()` 실행 | 자신의 출력 폴더에 실제 `.docx` 생성 |
| 37~45분 | 잘못된 수정안 검사 | 10초를 1초로 바꾼 문장이 막히는지 확인 | `UNSUPPORTED_NUMERIC_CLAIM` |
| 45~50분 | 사람 검토 | 파일을 열고 내용 및 페이지 수 확인 | 의미의 타당성, 제목 스타일, 줄 잘림 |

### 핵심 코드

프로젝트 루트에서 실행합니다. Notebook은 매 실행마다 새로운 결과 폴더를 사용합니다. 아래 예시 폴더를 다시 사용할 경우 파일명을 바꿉니다.

```python
from pathlib import Path
from labs.day4.office_lab.documents.resume_lab import (
    read_fact_map, audit_rewrite, build_resume, DocumentLabError,
)

ROOT = Path.cwd()
source = "labs/day4/office_lab/documents/career_facts.json"
facts = read_fact_map(ROOT, source)
my_revision = {
    "medical-polyp": "대장내시경 영상 기반 용종 탐지 및 진단 서비스 개발과 운영"
}
audit = audit_rewrite(facts, my_revision)
result = build_resume(
    ROOT, source, "outputs/my-day4/Resume_After.docx",
    proposals=my_revision,
)
print(result["path"])
```

`audit_rewrite()`는 새 수치와 잘못된 fact ID를 검사합니다. 문장의 의미가 사실인지, 기존의 역할을 부풀렸는지까지 증명하지 않습니다. 반환 상태가 `REQUIRES_HUMAN_REVIEW`인 이유입니다.

```python
try:
    audit_rewrite(facts, {"education-latency": "평가 시간을 1초로 단축"})
except DocumentLabError as error:
    assert error.code == "UNSUPPORTED_NUMERIC_CLAIM"
    print("원문에 없는 수치 차단 확인")
```

### Codex와의 대화 예시

1. **읽기**: “`career_facts.json`과 `Resume_Before.docx`를 비교해줘. 현재 자료에 있는 경력만 표로 정리하고, 확인이 필요한 수치와 빠진 정보를 구분해줘. 문서는 아직 바꾸지 마.”
2. **수정안**: “지원 분야는 Agent 제품 PM이야. 현재 Role과 산업별 문제 해결 경험을 앞에 배치해줘. 각 bullet마다 근거 fact ID를 남기고, 새 수치나 재직 기간은 만들지 마.”
3. **코드 구현**: “수정안의 사실을 내가 확인했어. `build_resume()`의 proposals 인자로 전달하고 새 파일로 저장해줘. 원본 덮어쓰기는 금지하고, 없는 수치를 넣는 테스트도 추가해줘.”
4. **결과 확인**: “출력 문서를 열어서 2페이지 이내인지, 제목과 본문이 잘리지 않는지 확인해줘. 구조 검사 결과와 사람이 확인해야 할 내용을 나눠서 알려줘.”

Claude에서도 같은 요청을 사용할 수 있습니다. 파일 작업 도구를 쓸 수 없는 환경이라면 코드와 수정안을 받은 뒤 Notebook에서 직접 실행합니다. 파일 첨부와 실제 로컬 파일 쓰기 권한은 같은 기능이 아닙니다.

## 7차시 PPT 자동화 50분

| 구간 | 내용 | 학생의 작업 | 파일과 확인 |
|---|---|---|---|
| 0~8분 | 보고서 입력과 구조 | WBS와 리뷰가 보고서 어디에 들어가는지 확인 | 7장 PPT 미리 보기 |
| 8~16분 | 상태 계산 | 완료율과 기준일을 바꿔 표 변화 확인 | `prepare_brief()`<br>합계가 14개인지 확인 |
| 16~28분 | PPT 코드 생성 | Node.js로 편집 가능한 PPT 생성 | `student_ppt.mjs`<br>실제 `.pptx` 열기 |
| 28~38분 | 입력 변경과 재생성 | 자신이 수정한 WBS를 새 보고서에 반영 | `tasks=tasks_my`<br>원본 템플릿은 보존 |
| 38~45분 | 시각 검사 | 각 장표를 열어 문장과 표의 잘림 확인 | 7장 모두 확인<br>PDF로 인쇄 후 다시 확인 |
| 45~50분 | 개선 요청 | 열 너비 또는 보고 대상에 맞춰 수정 요청 | Codex/Claude에 구체적인 파일과 수정 기준 전달 |

### 데이터 변경과 생성

```python
import copy
from pathlib import Path
from labs.day4.office_lab.presentations.brief_data import prepare_brief, write_brief

ROOT = Path.cwd()
initial = prepare_brief(ROOT)
tasks_my = copy.deepcopy(initial["wbs_snapshot"])
tasks_my[3]["progress"] = 1.0  # W04 리뷰 초안 완료 가정
brief_path = write_brief(
    ROOT, "outputs/my-day4/project_brief.json",
    tasks=tasks_my, as_of="2026-09-25",
)
```

```bash
node labs/day4/office_lab/presentations/student_ppt.mjs outputs/my-day4/project_brief.json outputs/my-day4/Project_Brief.pptx
```

이 템플릿은 14개 업무를 2장에 나누는 7장 보고서입니다. 업무 수가 다르면 `BRIEF_TASK_COUNT`로 멈춥니다. 더 많은 업무가 필요하면 코드를 고쳐 표 분할과 슬라이드 수를 함께 변경합니다. 남은 행을 조용히 버리지 않습니다.

`project_brief.json`에 수정한 WBS의 `wbs_snapshot`이 함께 들어갑니다. Excel 파일의 계산 결과를 읽은 척하지 않으며, Excel과 PPT가 **같은 입력 데이터**를 사용하게 만드는 방식입니다. 학생용 `PptxGenJS` 결과와 강사용 참고 PPT는 같은 내용 원본을 사용하지만 레이아웃 엔진이 달라 외형은 조금 다릅니다.

### Codex와의 대화 예시

1. **보고 대상**: “`outputs/my-day4/project_brief.json`으로 PM에게 보여줄 7장 진행 보고서가 필요해. 완료 업무 나열보다 지연 업무와 검토할 결정을 쉽게 찾는 구조를 먼저 제안해줘.”
2. **입력 확인**: “총 업무 수와 완료·진행·지연·예정 수를 코드로 검산해줘. W04를 완료로 바꾼 입력이 3장 표에 반영되는지 확인하고, 원본 WBS를 덮어쓰지 마.”
3. **파일 생성**: “`student_ppt.mjs`로 실제 PowerPoint 파일을 생성해줘. 표는 편집 가능해야 해. 흑백과 한글 폰트를 사용하고, 제목은 명사형으로 짧게 유지해줘.”
4. **화면 개선**: “생성된 PPT의 모든 장표를 확인해줘. 글자가 작은 표는 열 너비나 행 수를 조정하고, 오른쪽 열을 별도 색으로 강조하지 마. 계산 결과와 데이터 출처는 유지해줘.”

## API와 오류 계약

| 함수 및 실행 파일 | 입력 | 결과 | 주요 실패 |
|---|---|---|---|
| `read_fact_map(workspace, source)` | 허용 폴더 아래 JSON | 경력 fact map | `FACT_SCHEMA_INVALID`<br>`FACT_SOURCE_INVALID` |
| `audit_rewrite(facts, proposals)` | fact ID별 새 문장 | 검사 보고서<br>사람 검토 필요 | `UNKNOWN_FACT_REFERENCE`<br>`UNSUPPORTED_NUMERIC_CLAIM` |
| `build_resume(workspace, source, output, variant='after', proposals=None)` | 원본, 새 경로, 수정안 | 실제 DOCX와 경로 | `OUTPUT_EXISTS`<br>`PATH_OUTSIDE_WORKSPACE` |
| `prepare_brief(workspace, as_of='2026-09-25', tasks=None)` | 기준일, 선택 WBS 입력 | 7장 보고서 원본 | `BRIEF_TASK_COUNT`<br>`WBS_INPUT_INVALID` |
| `write_brief(workspace, output, as_of=..., tasks=None)` | 새 JSON 경로 | 저장한 Path | `OUTPUT_EXISTS`<br>`PATH_OUTSIDE_WORKSPACE` |
| `student_ppt.mjs input.json output.pptx` | 보고서 원본 | 편집 가능한 7장 PPT | `BRIEF_SCHEMA_INVALID`<br>`PATH_OUTSIDE_WORKSPACE`<br>`OUTPUT_EXISTS` |

## 강사용 참고 파일

| 파일 | 용도 |
|---|---|
| `outputs/day4-document-automation/Resume_Before.docx` | 장황한 문장과 중복의 비교 대상 |
| `outputs/day4-document-automation/Resume_After.docx` | Role과 산업별 경력 중심 개선본 |
| `outputs/day4-document-automation/Project_Brief.pptx` | 참고 보고서 정본 |
| `outputs/day4-document-automation/Project_Brief.pdf` | 인쇄 결과 확인 |
| `labs/day4/office_lab/presentations/project_brief.json` | 보고서 내용 원본 |
| `tests/test_day4_document_lab.py` | 사실 보존, 출력 보존, 폴더 범위, WBS 연결 검사 |

Word 참고 파일의 본문과 제목은 native Word 스타일이며, PPT 참고 파일의 표는 native PowerPoint 표입니다. PNG는 화면 설명과 시각 검수에 사용하며 편집 가능한 원본을 대신하지 않습니다.
