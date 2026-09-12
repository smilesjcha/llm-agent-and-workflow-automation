# 4주차 Excel 실습 운영 명세

## 실습의 범위

완성 파일을 구경하는 시간이 아니다. 입력 데이터 변경 → 수식 확인 → 잘못된 입력 재현 → 코드 수정 → 새 파일 저장 → 독립 계산과 대조까지 진행한다. 최종 Excel 파일은 실제 수식·조건부서식·입력 제한·틀 고정을 포함한다. 원본 성적이나 개인 이력은 사용하지 않는다.

| 차시 | 주제 | 이론 10분 | 강사 시연 10분 | 코드 실습 25분 | 확인 5분 |
|---|---|---|---|---|---|
| 4차시 | WBS·Gantt 자동화 | 업무 분해, 날짜 데이터, 절대·상대 참조, NETWORKDAYS | 업무14개·4주 간트와 상태 변화 | 작업목록 읽기 → 진척률 수정 → 날짜 오류 재현 → 새 Excel 저장 → 수식 재계산 | 지연2→1, 수식/CF 보존 |
| 5차시 | 시험 자동 채점 | 정답률 분모, 결시/미응답/오류, 동점 순위 | 28명·40문항 채점, 오류 행과 미응답 행 비교 | 9 입력 복구 → 정답 변경 → 재채점 → CSV·Excel 저장 | 채점26→27명, 총점·순위·정답률 일치 |

4·5차시 배치는 전체 교안과 통합할 때 조정할 수 있다. 두 실습은 독립 실행 가능하며, WBS 데이터는 후반부 자동 생성 PPT의 일정 표에 재사용한다.

## 설치와 시작

저장소 루트, Python 3.12 가상환경에서 실행한다. Excel 유료 구독이 없어도 LibreOffice에서 수식과 조건부서식을 확인할 수 있다. 실제로 GUI 앱을 열지 않아도 Python CSV 채점 결과와 pytest는 실행된다.

```bash
python -m pip install -r labs/day4/office_lab/sheets/requirements.txt
python -m labs.day4.office_lab.sheets.student_excel --workspace . --output-dir outputs/day4-student/run-01
python -m pytest -q tests/test_day4_excel_lab.py
```

Notebook 상단 설치 셀:

```python
%pip install "openpyxl>=3.1.5,<4"
```

최종 템플릿 저작은 artifact-tool로 진행했다. 학생 실행 경로에는 내부 패키지가 필요 없다. 공개 라이브러리 openpyxl은 템플릿의 입력을 바꾸고 저장한다. **openpyxl은 수식 계산 엔진이 아니다.** 저장한 파일을 Excel/LibreOffice에서 열어 재계산하고, Python 독립 계산 결과와 비교한다. 저장 직후 `data_only=True`로 읽은 빈 캐시는 0점이 아니다.

## 제공 파일

| 용도 | 경로 | 내용 |
|---|---|---|
| WBS 템플릿 | `outputs/day4-document-automation/WBS_Gantt.xlsx` | 업무14개, 28일 간트, 기준일 입력, 평일 업무일수 |
| 채점 템플릿 | `outputs/day4-document-automation/Exam_Grading.xlsx` | 합성28명·40문항, 채점·채점내역2시트 |
| 프로젝트 입력 | `labs/day4/office_lab/sheets/wbs_tasks.json` | `id, task, role, start, end, progress, predecessor` |
| 시험 입력 | `labs/day4/office_lab/sheets/exam_sample.json` | `key[40]`, `students[{id,attendance,answers[40]}]` |
| 학생 구현 코드 | `labs/day4/office_lab/sheets/student_excel.py` | 검증·독립 계산·Excel 입력 수정·CSV 저장 |
| 단위 테스트 | `tests/test_day4_excel_lab.py` | 날짜 역전·미응답·결시·잘못된 입력·경로 이탈 등 |
| 실제 앱 재계산 검증 | `labs/day4/office_lab/sheets/verify_native.py` | Excel/LibreOffice 재계산본과 Python 결과 비교 |

## WBS 실습 순서

```python
from pathlib import Path
from labs.day4.office_lab.sheets.student_excel import (
    load_sample, validate_wbs, calculate_wbs, write_wbs_copy,
)
ROOT = Path.cwd()  # 저장소 루트인지 README.md로 확인
tasks = load_sample("wbs_tasks.json")
assert validate_wbs(tasks) == []
before = calculate_wbs(tasks, "2026-09-25")
assert sum(row["status"] == "지연" for row in before) == 2

tasks[3]["progress"] = 1  # W04 Codex 리뷰 초안 완료
after = calculate_wbs(tasks, "2026-09-25")
assert sum(row["status"] == "지연" for row in after) == 1
result = write_wbs_copy(ROOT, tasks, "2026-09-25",
                        "outputs/day4-student/run-02/WBS_my_project.xlsx")
print(result)
```

Excel에서 `F12=100%`, `I12=완료`, 지연 요약1건과 간트 색 변화를 확인한다. `H12` 수식은 `NETWORKDAYS`를 유지한다. 기준일 `B4`를 2026-10-01로 바꾸면 일정 상태가 다시 계산된다.

### 입력 셀과 수식

| 위치 | 역할 | 학생 확인 |
|---|---|---|
| `WBS!B4` | 기준일(수업용 고정값 2026-09-25) | TODAY가 아닌 재현 가능한 입력 |
| `WBS!B5` | 프로젝트 시작일 | 간트 날짜의 기준 |
| `A9:G22` | ID, 업무, Role, 시작일, 종료일, 진척률, 선행ID | 입력 변경 영역 |
| `H9:H22` | 평일 업무일수 | 토·일 제외, 공휴일 미반영 |
| `I9:I22` | 완료·지연·예정·진행 중 | 지연 = 종료일 < 기준일 AND 진척률 < 100% |
| `J9:J22` | 날짜·ID·진척률·선행 일정 확인 | 오류를 임의 일정으로 대체하지 않음 |
| `K9:K22` | 선행업무 종료일 조회 | 정확한 ID 매칭 |
| `L8:AM8` | 28일 날짜 헤더 | `=$B$5+0`부터 +27까지 |
| `L9:AM22` | 간트 조건부서식 | `$D9`, `$E9`, `L$8`의 고정 방향 |

대표 수식:

```excel
=IF(J9<>"입력 완료","계산 보류",NETWORKDAYS(D9,E9))
=IF(J9<>"입력 완료","입력 확인",IF(F9=1,"완료",IF(E9<$B$4,"지연",IF(D9>$B$4,"예정","진행 중"))))
```

의도 실패: `tasks[0]["end"]="2026-09-01"` → `END_BEFORE_START`. `progress=None` → `INVALID_PROGRESS`. ID 중복, 존재하지 않는 선행 ID, 순환 의존도 별도 오류 코드로 확인한다. `progress=0`은 정상이다.

### Codex 작업 요청

> `student_excel.py`와 테스트를 읽어줘. WBS에 공휴일 목록을 입력받는 선택 인수를 추가하고, 업무일 계산에서 토·일과 공휴일을 제외해줘. 날짜를 임의로 추정하지 말고 내가 제공하는 목록만 사용해. 공휴일 없음·평일 공휴일·주말과 중복 공휴일을 테스트해줘. Excel NETWORKDAYS의 세 번째 인수에 연결하는 수정은 먼저 diff로 보여줘. 원본 템플릿을 덮어쓰지 말고 새 결과 파일로 저장해줘.

이 요청은 학생이 실제 계산 로직과 테스트를 수정하는 확장 과제다. 최종 제공 템플릿에는 공휴일 기능을 구현한 것처럼 표시하지 않는다.

## 시험 채점 실습 순서

```python
from labs.day4.office_lab.sheets.student_excel import (
    load_sample, grade_exam, write_exam_copy, write_grade_csv,
)
exam = load_sample("exam_sample.json")
initial = grade_exam(exam)
assert initial["eligible_count"] == 26
assert initial["students"][25]["status"] == "입력 오류"
assert initial["students"][25]["score"] is None

exam["students"][25]["answers"][8] = 1  # S026, 9번 문항의 입력 9 복구
repaired = grade_exam(exam)
assert repaired["eligible_count"] == 27

exam["key"][0] = 2  # 1번 정답 변경; 성적 발표 전 정답표 검토 사례
regraded = grade_exam(exam)
assert regraded["students"][0]["score"] == 19
print(write_exam_copy(ROOT, exam, "outputs/day4-student/run-03/Exam_my_class.xlsx"))
print(write_grade_csv(ROOT, exam, "outputs/day4-student/run-03/grading_report.csv"))
```

변경 전 원본은 S001=20점, S025=미응답2개/19점, S026=입력오류/채점보류, S027=S001과 동점, S028=결시다. 이론 설명 다음에는 학생이 실제 코드를 실행하고 Excel에서 입력을 고쳐본다.

### 좌표와 채점 기준

| 위치 | 의미 | 기준 |
|---|---|---|
| `채점!D8:AQ8` | 40문항 정답 | 숫자1~4만 가능. 비어 있거나 잘못되면 모든 응시자 성적 보류 |
| `A10:A37` | 합성 ID | S001~S028. 중복 ID는 채점 보류 |
| `C10:C37` | 응시 상태 | 응시 / 결시 |
| `D10:AQ37` | 답안 | 미응답은 0점으로 계산하되 미응답 개수 표시 |
| `AR10:AR37` | 총점 | 문항별1점, 40점 만점. 입력 오류/결시/정답 미등록은 숫자0이 아닌 채점보류 |
| `AS10:AS37` | 등수 | `1+COUNTIFS(총점범위,">"&본인점수)`. 공동1등2명이면 다음3등 |
| `AT10:AX37` | 상태·미응답·오류·오답·정답 | 숫자에 숨기지 않는 처리 결과 |
| `채점내역!D8:AQ35` | 문항별 판정 | 정답 / 오답 / 미응답 / 잘못된 입력 / 정답 미등록 / 결시 |
| `채점!D41:AQ41` | 정답자 수 | 채점 가능한 응시자 중 해당 문항 정답자 |
| `D42:AQ42` | 분모 | 입력 오류가 없는 응시자. 결시 제외, 미응답 포함 |
| `D43:AQ43` | 문항 정답률 | 정답자수÷집계대상. 분모0이면 집계보류 |

색만으로 점수를 계산하지 않는다. 숫자와 수식으로 먼저 계산하고 조건부서식은 판정을 시각화한다. 정답행 참조는 `D$8`, 응시상태 참조는 `$C10`으로 고정 방향이 다르다. 붙여넣기는 Excel 입력 제한을 우회할 수 있어 수식·Python 검증을 함께 둔다.

### Codex 작업 요청

> `grade_exam`에서 문항별 배점이 다른 시험을 지원해줘. 현재는 40문항×1점이야. 새 `weights` 배열은 40개 양수이고, 입력 오류나 정답 누락은 여전히 채점보류여야 해. 결시를 0점으로 넣거나 정답률 분모를 바꾸지 마. 동일 배점·가중치 변경·잘못된 배점·동점 순위 테스트를 먼저 작성해줘. 학생 성적은 합성 데이터만 사용하고 실제 구글시트에는 접근하지 마.

## 재실행과 제한

- 템플릿은 업무14개·응시자28명·문항40개다. 행을 추가할 때 수식·조건부서식·집계 범위를 함께 확장해야 한다. 현재 코드는 잘못된 개수로 덮어쓰지 않고 명시적 오류를 반환한다.
- 입력·출력 파일 경로는 지정 workspace 내부로 제한한다. 경로 이탈과 symlink 이탈 모두 거부한다.
- 외부에서 온 업무명·ID가 `=`로 시작해도 Excel 수식으로 실행하지 않고 텍스트로 저장한다. CSV에서도 수식처럼 해석될 수 있는 문자열을 구분한다.
- 같은 출력 파일을 다시 쓰면 `OUTPUT_ALREADY_EXISTS`. 새 `run-02` 폴더 등으로 실행 이력을 보존한다.
- 학생 Excel의 입력 변경은 Google Sheets 원본에 반영되지 않는다. 클라우드 업로드·성적 공개는 이 실습에서 실행하지 않는다.
- `.xlsx`의 셀 수식·틀고정·조건부서식은 artifact-tool과 LibreOffice 재계산본으로 교차 확인한다. 모든 Excel 버전·Google Sheets 변환에서 동일함을 보증하는 것은 아니므로 사용 앱에서 대표 입력을 재확인한다.

## 검증 근거

최종 템플릿의 artifact-tool 재계산: 수식 오류0. WBS 진척률 변경 시 지연→완료. 정답 변경 시 S001점수20→19. 오류 답안9복구 시 채점인원26→27. 정답누락·문자정답·문자답안은 성적보류. 모든 임시 입력은 원래 합성 예제로 복구 후 저장했다.

LibreOffice에서 별도 복사본을 열고 저장한 결과: 업무14개 업무일수·상태, 학생28명 총점·동점등수·처리상태, 문항40개 정답률을 독립 Python 계산과 대조해 일치 확인. Excel 수식 오류0, 간트/채점 조건부서식 및 틀고정 유지. PNG는 실제 생성 workbook의 렌더이며 특정 서비스 UI 캡처로 표기하지 않는다.

학생 CLI가 수정해 저장한 사본도 LibreOffice에서 재계산했다. W04 진척률100% → 완료/지연1건, S026 입력복구 → 24점/집계27명을 확인했다. 검증 기록: `outputs/day4-document-automation/excel_native_validation.json`. Excel 실습21개와 Day1 전체35개 테스트를 함께 실행해 **56 passed**.

## 공식 레퍼런스

확인일: 2026-09-12. 아래는 함수·도구 동작의 출처이며, 학생이 사이트를 읽는 것만으로 실습을 대체하지 않는다.

| 출처 | 수업에 연결할 내용 |
|---|---|
| [Microsoft NETWORKDAYS](https://support.microsoft.com/en-us/excel/functions/networkdays-function) | 날짜의 숫자 저장, 주말 제외, 휴일 목록 선택 인수 |
| [Microsoft COUNTIFS](https://support.microsoft.com/en-gb/office/countifs-function-dda3dc6e-f74e-4aee-88bc-aa8c2a866842) | 여러 범위를 동일한 행 단위로 세는 조건부 집계 |
| [Microsoft 조건부서식](https://support.microsoft.com/en-us/excel/use-conditional-formatting-to-highlight-information-in-excel) | 수식 기반 규칙, 상대/절대 참조, 복사 이후 적용 범위 확인 |
| [Microsoft RANK.EQ](https://support.microsoft.com/en-us/excel/functions/rank-eq-function) | 동일 점수 동일 순위, 동점 이후 순위 건너뛰기. 본 예제는 1+COUNTIFS로 같은 정의 구현 |
| [openpyxl 수식 처리](https://openpyxl.readthedocs.io/en/3.1.2/simple_formulae.html) | 수식 저장과 수식 계산의 차이. openpyxl은 계산하지 않음 |
