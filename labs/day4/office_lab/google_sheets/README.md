# Google Sheets 자동 채점 선택 실습

제공한 합성 데이터로 **새 연습 시트 2개**를 만드는 Apps Script입니다. 사용자가 공유한 원본 성적표 URL에 접근하지 않으며, 실제 원본 문서를 수정하지 않았습니다. Google 계정에서 스크립트를 실행하거나 배포한 상태가 아닙니다.

기본 실습은 로컬 Excel 파일입니다. Google Sheets를 사용할 수 있는 학생만 이 확장을 선택합니다.

## 생성 범위

| 구분 | 내용 |
|---|---|
| 새 시트 | `Day4_채점_실습`, `Day4_채점내역_실습` |
| 예제 | 로컬 `exam_sample.json`과 같은 합성 28명·40문항 |
| 입력 | 정답 `D8:AQ8`, 응시 상태 `C10:C37`, 답안 `D10:AQ37` |
| 결과 | 총점 `AR`, 등수 `AS`, 처리 상태 `AT`, 미응답·오류·오답·정답 `AU:AX` |
| 문항 분석 | 정답자 수 41행, 집계 인원 42행, 정답률 43행 |
| 권한 | 현재 문서와 확인창. 파일목록 탐색·외부URL·이메일·트리거 없음 |
| 기존 시트 | 읽거나 고치지 않음. 생성할 이름이 이미 있으면 중단 |

## 실행 순서

1. 개인 연습용 **새 Google 스프레드시트**를 만듭니다. 실제 성적표와 업무용 문서는 닫아 둡니다.
2. 파일 이름을 `4주차 합성 채점 연습`처럼 지정합니다. 업로드한 `.xlsx` 편집 화면이 아니라 Google 스프레드시트 형식인지 확인합니다.
3. 해당 문서에서 **확장 프로그램 → Apps Script**를 엽니다. 독립 프로젝트가 아닌 이 문서에 연결된 프로젝트여야 합니다.
4. 기본 `Code.gs` 내용을 제공한 [Code.gs](Code.gs) 내용으로 바꾸고 저장합니다. 기존 업무용 Apps Script 프로젝트에 붙여넣지 않습니다.
5. 프로젝트 설정에서 **에디터에 appsscript.json 매니페스트 파일 표시**를 켭니다. 새 연습 프로젝트에 제공한 [appsscript.json](appsscript.json)을 넣고 저장합니다.
6. 실행할 함수로 `createDay4GradingPractice`를 선택하고 실행합니다. 처음 요청되는 권한은 현재 문서와 UI에 한정되어야 합니다. 이메일·전체 Drive 등 예상과 다른 권한이면 승인하지 않습니다. 조직 정책으로 차단되면 로컬 실습으로 돌아갑니다.
7. 스프레드시트 탭의 확인창에서 **빈 연습 문서가 맞는지** 확인한 뒤 동의합니다. 취소하면 아무 시트도 만들지 않습니다.
8. 새로 생긴 두 시트에서 정답·응답·총점·처리 상태를 확인합니다. 기존 `시트1`은 지우지 않습니다.
9. 아래 입력 변경 실습을 수행합니다. 수식을 직접 지우지 말고 지정한 입력 셀만 바꿉니다.
10. 재실행 시 `PRACTICE_SHEET_ALREADY_EXISTS`면 정상적인 덮어쓰기 차단입니다. 다른 새 연습 문서를 만들어 실행합니다. 생성 중 오류가 나면 이미 생긴 연습 시트를 자동 삭제하지 않습니다.

## 변경 실습

| 순서 | 바꿀 입력 | 확인할 결과 |
|---|---|---|
| 1 | 처음 생성된 값 유지 | 채점 가능 26명, S026 입력 오류, S028 결시 |
| 2 | `L35`: 9 → 1 | S026 채점 완료·24점, 채점 가능 27명 |
| 3 | `D8`: 1 → 2 | S001 20→19점, 등수·문항 정답률 재계산 |
| 4 | `D8` 지우기 | 응시자 전체 채점 보류, 정답률 집계 보류 |
| 5 | `D8` 복구 후 `D10`에 글자 입력 | S001 입력 오류·점수 보류. 0점으로 숨기지 않음 |
| 6 | 변경한 입력 복구 | 총점·등수·집계 대상 재확인 |

실제 시험에서는 오류 입력을 추측해서 수정하지 않습니다. 원본 답안 확인 후 수정하는 절차를 합성 값 `9→1`로 연습합니다.

## 수식과 조건부서식

숫자와 수식으로 먼저 판정하고 색은 보조 표시로 사용합니다. 맞춤 조건부서식은 Google Sheets의 제약을 고려해 **같은 시트의 셀**만 참조합니다. 다른 시트의 문항별 판정은 일반 셀 수식으로 가져옵니다.

```excel
=AND($C10="응시",D$45="등록",ISNUMBER(D10),D10=D$8,D10>=1,D10<=4)
```

- `$C10`: 응시 상태 열만 고정.
- `D$8`: 정답 행만 고정.
- `D$45`: 정답이 숫자 정수1~4로 등록되었는지 확인. 잘못된 정답과 답안이 우연히 같아도 정답 색을 칠하지 않음.
- `D10:AQ37`: 적용할 응답 범위.
- 미응답은 해당 문항 0점이며 전체 분모에 포함합니다.
- 결시·입력 오류는 점수 미확정이며 분모에서 제외합니다.
- 정답 하나라도 비어 있거나 잘못되면 전체 채점을 보류합니다.
- 같은 점수는 같은 등수, 다음 등수는 동점 인원만큼 건너뜁니다.

숫자 범위 입력 제한은 1~4로 안내하지만 실수·문자·붙여넣기도 수식으로 다시 확인합니다. 입력 검증 UI만 믿고 채점하지 않습니다.

## Google 계정이 없는 경우

Notebook 5차시를 실행하거나 다음 명령으로 로컬 XLSX·CSV를 만듭니다.

```bash
python -m pip install -r labs/day4/office_lab/sheets/requirements.txt
python -m labs.day4.office_lab.sheets.student_excel --workspace . --output-dir outputs/day4-student/sheets-alternative-01
```

`WBS_my_project.xlsx`, `Exam_my_class.xlsx`, `grading_report.csv`가 새 폴더에 저장됩니다. Excel 또는 LibreOffice로 `.xlsx`를 열어 재계산합니다. `openpyxl`은 수식을 계산하지 않습니다. Google 계정 없이도 `grade_exam`의 계산·테스트·파일 저장까지 필수 실습을 완료할 수 있습니다.

## 코드 검증과 미검증 범위

```bash
node --test labs/day4/office_lab/google_sheets/test_code.mjs
```

Node 모의 API 테스트 9개: 합성 데이터 일치, 두 새 시트만 생성, 쓰기 배열 크기, 취소, 중복 이름 중단, 동시 실행 차단, 오류 발생 시 잠금 해제, 같은 시트 조건부서식 참조, 수식 구조·권한 제한을 확인했습니다.

**Google 서버의 수식 계산·권한 화면·실제 조건부서식 렌더는 미검증입니다.** Node 테스트는 이를 대신하지 않습니다. 수강생 본인 계정에서 위 대표 입력 변경을 확인한 후 자신의 연습 결과로 사용하세요. 이 예제는 코드 배포 자료이며, 이미 생성된 온라인 스프레드시트 링크를 제공하는 방식이 아닙니다.

## 공식 참고

- [현재 문서로 권한 제한](https://developers.google.com/apps-script/guides/services/authorization)
- [프로젝트 매니페스트 표시](https://developers.google.com/apps-script/concepts/manifests)
- [조건부서식 Builder](https://developers.google.com/apps-script/reference/spreadsheet/conditional-format-rule-builder)
- [확인창과 버튼](https://developers.google.com/apps-script/reference/base/ui)
- [문서 단위 잠금](https://developers.google.com/apps-script/reference/lock/lock-service)

확인일: 2026-09-12.
