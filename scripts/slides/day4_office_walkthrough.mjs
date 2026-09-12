// Additive walkthroughs. Each anchor names one existing lesson title.
const code = (title, source, explain, note) => ({
  type: 'code', title, code: source, explain, note, phase: 'lab',
});
const task = (title, steps, file, check, note) => ({
  type: 'task', title, steps, file, check, note, phase: 'lab',
});
const table = (title, headers, rows, note) => ({
  type: 'table', title, headers, rows, note, phase: 'theory',
});

export const OFFICE_WALKTHROUGH = [
  {
    period: 3, after: '일정 데이터와 간트 차트', slides: [
      task('WBS 연습 파일 열기', [
        '제공 파일을 복사한 뒤 Excel 또는 LibreOffice로 열기',
        '아래쪽 WBS 탭 선택, 왼쪽 위 이름 상자에 F12 입력',
        '같은 행의 A12가 W04인지, F12가 80%인지 확인',
        '계산 결과 I12의 지연 표시와 B4 기준일 확인',
      ], 'outputs/day4-document-automation/WBS_Gantt.xlsx',
      '수정 대상: 복사본의 입력 셀 / 계산 셀은 유지',
      '원본을 OS 파일 관리자의 복사 기능으로 다른 이름에 저장한다. 이름 상자는 수식 입력줄 왼쪽의 셀 주소 칸이다. F12를 찾기 전에 다른 시트가 선택되어 있지 않은지 확인한다. 이 단계는 기준 파일 관찰이며 뒤의 Notebook 저장본과 구분한다.'),
    ],
  },
  {
    period: 3, after: 'WBS 데이터 로딩', slides: [
      code('업무 ID와 Python 행 선택',
`w04_index = next(
    i for i, row in enumerate(tasks) if row["id"] == "W04"
)
w04 = tasks[w04_index]
print(w04["id"], w04["task"])
print(w04["start"], w04["end"], w04["progress"])`,
      ['Notebook 4차시의 데이터 로딩 셀 실행 후',
       'W04: 2026-09-21 ~ 2026-09-23 / 진척률 0.8'],
      'Python 목록은 0부터 세므로 네 번째 업무의 위치는 3이다. 위치 숫자를 외우기보다 id로 찾아서 수정할 업무를 확인한다. next에서 StopIteration이 나면 tasks를 다시 로딩하고 W04가 있는지 확인한다. 해당 업무가 없는데 다른 행을 대신 고치지 않는다.'),
    ],
  },
  {
    period: 3, after: '진척률 변경', slides: [
      code('진척률 수정과 XLSX 저장',
`tasks_my = deepcopy(tasks)
tasks_my[w04_index]["progress"] = 1
destination = RUN / "excel/WBS_walkthrough.xlsx"
wbs_path = write_wbs_copy(
    ROOT, tasks_my, AS_OF,
    str(destination.relative_to(ROOT)),
)
print(wbs_path)`,
      ['Notebook의 ROOT·RUN·AS_OF와 import 셀 선행',
       '같은 이름이 있으면 WBS_walkthrough_v2.xlsx 사용'],
      '앞 장표의 w04_index를 사용한다. deepcopy와 write_wbs_copy는 제공 Notebook의 앞선 import 셀에서 준비한다. 출력 경로를 실제 파일 관리자로 열고 F12=100%, 재계산 후 I12=완료인지 확인한다. OUTPUT_ALREADY_EXISTS는 원본 보호를 위한 중단이며 기존 파일을 지우는 대신 새 파일명을 사용한다.'),
    ],
  },
  {
    period: 3, after: '일정 변경과 차트 확인', slides: [
      task('입력 셀과 수식 입력줄', [
        '내 WBS를 열고 B4 기준일을 2026-09-25로 복구',
        'D12=09/21·E12=09/23 복구, H12의 날짜 참조 확인',
        'F12를 80%로 변경하고 I12의 지연 표시 확인',
        'F12를 100%로 복구하고 완료 표시 확인 후 저장',
      ], '내 실행 폴더 / excel/WBS_walkthrough.xlsx',
      '기본 날짜 유지 시 H12=3 / 진척률에 따라 I12 변경',
      '방금 저장한 WBS_walkthrough.xlsx의 WBS 탭을 연다. 앞 장표에서 바꾼 기준일 B4=2026-09-25, 시작일 D12=2026-09-21, 종료일 E12=2026-09-23을 먼저 복구한다. H12의 실제 식에는 입력 오류를 검사하는 조건도 있다. NETWORKDAYS의 날짜 인수 D12와 E12를 찾아 평일 3일과 비교한다. H12와 I12에 계산 결과를 직접 타이핑하지 않는다.'),
    ],
  },
  {
    period: 3, after: '선행 일정의 오류', slides: [
      code('종료일 오류와 입력 복구',
`broken_tasks = deepcopy(tasks)
broken_tasks[0]["end"] = "2026-09-01"
print(validate_wbs(broken_tasks))
broken_tasks[0]["end"] = tasks[0]["end"]
assert validate_wbs(broken_tasks) == []
print("날짜 복구 완료")`,
      ['종료일이 시작일보다 빠르면 END_BEFORE_START',
       '오류를 고친 뒤 검사 결과가 빈 목록인지 확인'],
      '새 복사본에서 한 값만 바꾼다. 출력에서 id=W01과 code=END_BEFORE_START를 확인한다. 검사를 건너뛰고 계산을 강행하지 않는다. 숫자 0으로 오류를 감추지 않고 원본 종료일을 복구한 뒤 저장을 재시도한다.'),
    ],
  },
  {
    period: 3, after: '수식 결과의 검증', slides: [
      table('저장 후 값이 그대로인 경우',
        ['화면의 상태', '확인과 복구'], [
          ['F12가 아직 80%', '출력 경로 확인\n새 저장본을 다시 열기'],
          ['F12는 100%, I12는 지연', 'Excel 수식 탭\n계산 옵션: 자동 / 지금 계산'],
          ['Python에서 수식 결과가 None', 'openpyxl은 수식 미계산\nExcel·LibreOffice에서 재계산'],
          ['앱에서 계산 후에도 불일치', 'B4·D12·E12와 수식 확인\n원본 템플릿 복사본으로 재현'],
        ],
        'Excel Windows의 수식 탭 기준이며 Mac과 LibreOffice는 메뉴 위치가 다를 수 있다. data_only=True는 저장된 계산 캐시를 읽는 옵션으로 재계산 명령이 아니다. None을 0점 또는 0일로 치환하지 않는다. 출처: https://support.microsoft.com/ko-kr/excel/change-formula-recalculation-iteration-or-precision-in-excel'),
    ],
  },
  {
    period: 4, after: '채점 시트의 위치', slides: [
      task('정답과 답안의 셀 선택', [
        '제공 채점 파일의 복사본에서 채점 탭 선택',
        '이름 상자에 D8 입력: 첫 문항의 정답 1 확인',
        'D10 선택: S001의 첫 문항 답안과 정답 비교',
        'AR10의 총점 20점과 AT10의 처리 상태 확인',
      ], 'outputs/day4-document-automation/Exam_Grading.xlsx',
      '정답 8행 / 답안 10~37행 / 총점 AR열',
      '정답 변경 전의 기본 파일로 진행한다. 응답행의 첫 칸은 D10이다. D8을 답안 칸으로 오해해서 붙여넣지 않는다. 실제 성적이나 원본 온라인 파일을 열지 않고 제공된 합성 데이터만 사용한다.'),
    ],
  },
  {
    period: 4, after: 'Python 기준값', slides: [
      code('문항 번호와 목록 위치',
`print("1번 정답:", exam["key"][0])
student = exam["students"][25]
print("학생:", student["id"])
print("9번 답안:", student["answers"][8])
print(grade_exam(exam)["students"][25])`,
      ['26번째 학생 S026 / 9번 답안 9 / Excel L35',
       '목록 위치는 0부터, 문항 번호는 1부터 시작'],
      'exam은 바로 앞 데이터 로딩 결과다. students[25]는 S026, answers[8]은 9번 문항이다. 보기 9는 정답과 다르다는 의미의 오답이 아니라 입력 범위를 벗어난 값이다. score=None과 status=입력 오류를 함께 확인한다.'),
    ],
  },
  {
    period: 4, after: '입력 오류의 복구', slides: [
      code('보기 번호 수정의 전후',
`exam_my = deepcopy(exam)
exam_my["students"][25]["answers"][8] = 1
before_count = grade_exam(exam)["eligible_count"]
fixed = grade_exam(exam_my)
print(before_count, fixed["eligible_count"])
print(fixed["students"][25]["score"])`,
      ['집계 대상 26명에서 27명 / S026은 24점',
       '수정한 exam_my를 Notebook의 XLSX·CSV 저장 셀에 전달'],
      '실습은 사전에 정한 합성 오류 9를 1로 고친다. 실제 시험에서는 원본 답안 확인 없이 학생 응답을 추정하지 않는다. 원본 exam을 유지하여 전후 비교가 가능하다. grade_exam은 파일을 저장하지 않으므로 뒤의 write_exam_copy와 write_grade_csv 셀까지 실행해야 결과 파일에 반영된다.'),
    ],
  },
  {
    period: 4, after: '예외 입력 테스트', slides: [
      code('정답 누락의 복구 순서',
`missing = deepcopy(exam_my)
missing["key"][0] = None
held = grade_exam(missing)
assert held["students"][0]["score"] is None
print(held["students"][0]["status"])
missing["key"][0] = exam["key"][0]
assert grade_exam(missing)["eligible_count"] == 27`,
      ['D8에 해당하는 정답 누락: 정답 확인 / 점수 보류',
       '정답 복구 후, 입력 오류를 고친 27명 다시 집계'],
      '이전 장표에서 S026을 수정한 exam_my를 기준으로 한다. 숫자 0으로 누락 정답을 채우지 않는다. 누락 상태의 결과를 배포하지 않고 정답 근거를 확인한 다음 재계산한다. Excel 복사본에서도 D8을 비웠다가 1로 복구해 같은 정책을 확인한다.'),
    ],
  },
  {
    period: 4, after: 'Google Sheets 적용', slides: [
      task('내 채점표의 Google Sheets 사본', [
        '개인 Drive의 새로 만들기에서 합성 XLSX 파일 업로드',
        '업로드한 파일 열기, 파일 메뉴의 Google Sheets로 저장',
        '새 Google 파일 이름을 4주차_채점_연습으로 변경',
        '원래 XLSX 보존, 새 파일의 채점 탭에서만 작업',
      ], '내 복사본의 Exam_Grading.xlsx / 개인 Google 계정',
      '선택 확장 / 온라인 계산·서식은 계정에서 직접 확인 필요',
      '원본 성적표 URL은 사용하지 않는다. 이미 네이티브 Google Sheets인 자신의 문서는 파일 메뉴의 사본 만들기를 사용한다. XLSX 편집 화면에서 바로 값을 고치면 Excel 원본 형식에 저장될 수 있으므로 먼저 변환한다. 제공 코드의 원격 실행·권한 화면·수식 렌더는 미검증이다. 계정이 없으면 앞의 로컬 XLSX·CSV 경로로 진행한다. 출처: https://support.google.com/docs/answer/9331167?hl=ko'),
      task('조건부서식 메뉴와 시험 입력', [
        '채점 탭에서 응답 범위 D10:AQ37 선택',
        '서식 메뉴의 조건부서식 열기, 맞춤 수식 규칙 선택',
        '정답 규칙의 적용 범위와 D$8·D$45 참조 확인',
        'L35를 9에서 1로 변경, B5=27과 AR35=24 확인',
      ], '새 Google 파일 / 채점 탭 / 서식 > 조건부서식',
      '원격 실행 미검증 / 계산과 색을 함께 확인 후 사용',
      '기본 합성 XLSX를 변환한 새 문서에서 진행한다. 기존 정답 규칙이 있으면 중복 규칙을 추가하지 않는다. 없다면 앞의 정답 색의 조건 장표에 있는 전체 수식을 맞춤 수식에 넣는다. 색만 보고 통과시키지 않고 점수·처리 상태를 확인한다. 변환 오류가 지속되면 로컬 파일로 돌아가거나 별도의 빈 Google 문서에서 google_sheets/README.md의 새 시트 생성 절차를 사용한다. 출처: https://support.google.com/docs/answer/78413?hl=ko'),
    ],
  },
  {
    period: 5, after: 'Fact map', slides: [
      task('경력 원문 JSON 열기', [
        'VS Code 탐색기에서 documents 폴더의 JSON 열기',
        '파일 안에서 medical-polyp 검색',
        'text의 원문과 rewrite의 수정 문장 비교',
        '원본 저장 없이 Notebook의 my_rewrites에서 수정',
      ], 'labs/day4/office_lab/documents/career_facts.json',
      'id는 근거 연결 / text는 원문 / rewrite는 수정 초안',
      'JSON은 최종 이력서가 아니라 문장을 근거와 연결하는 입력이다. 이 파일은 사용자가 제공한 경력의 수업 예시이며 별도로 검증한 실제 원본 이력서가 아니다. 연락처·고객 정보나 새로운 재직 기간을 추가하지 않는다.'),
      code('Fact ID의 원문 조회',
`known = {
    fact["id"]: fact
    for role in facts["roles"] for fact in role["facts"]
}
source_fact = known["medical-polyp"]
print(source_fact["text"])
print(source_fact["rewrite"])`,
      ['Notebook 6차시의 read_fact_map 셀 실행 후',
       '문장 위치가 바뀌어도 같은 ID로 원문 조회'],
      'facts는 FACT_SOURCE를 read_fact_map으로 읽은 결과다. 파일 이름과 변수 이름을 구분한다. 잘못된 ID의 KeyError가 나면 원문 JSON에서 정확한 id를 확인하며 비슷한 경력을 임의로 대체하지 않는다.'),
    ],
  },
  {
    period: 5, after: '경력 문장 한 개 개선', slides: [
      code('문장 수정안의 자동 검사',
`my_rewrites = {
    "medical-polyp":
    "대장내시경 영상 기반 용종 탐지·진단 서비스 총괄 개발과 운영"
}
report = audit_rewrite(facts, my_rewrites)
print(report["numeric_guard"])
print(report["semantic_claims_verified"])`,
      ['새 숫자 검사 PASS / 의미 검증 False',
       '자동 검사 후에도 Role과 업무 범위는 원문 대조'],
      '화면에 표시되는 PASS는 수치 규칙의 통과다. semantic_claims_verified=False를 함께 읽는다. 문장을 짧게 줄이면서 총괄 역할이나 핵심 업무를 빼지 않았는지도 사람이 판단한다. 필요한 경우 my_rewrites 문장만 수정하고 다시 검사한다.'),
    ],
  },
  {
    period: 5, after: '의도한 과장 검사', slides: [
      code('숫자 없는 과장의 검사 한계',
`bad_proposal = {
    "medical-polyp": "전 세계 모든 병원의 진단 서비스를 총괄"
}
limit = audit_rewrite(facts, bad_proposal)
print(limit["numeric_guard"])
print(limit["semantic_claims_verified"])`,
      ['검사 한계용 허위 문장 / DOCX 저장 금지',
       '숫자가 없어 PASS여도, 원문에 없는 주장'],
      '의도적으로 잘못된 문장을 별도 bad_proposal 변수에 넣는다. my_rewrites는 바꾸지 않는다. 전 세계 모든 병원이라는 범위는 원문에 없지만 현재 숫자 규칙은 이를 찾지 못한다. AI나 정규식 검사의 통과가 사실 인증을 뜻하지 않는 사례다. 다음 저장에는 정상 my_rewrites만 사용한다.'),
    ],
  },
  {
    period: 5, after: 'Word 스타일 수정', slides: [
      code('DOCX의 새 버전 생성',
`word_path = RUN / "word/Resume_walkthrough.docx"
result = build_resume(
    ROOT, FACT_SOURCE, word_path,
    variant="after", proposals=my_rewrites,
)
print(result["path"])
print(result["status"])`,
      ['실제 파일 생성 / 상태는 REQUIRES_HUMAN_REVIEW',
       'OUTPUT_EXISTS 발생 시 파일명에 _v2 추가'],
      'Notebook 6차시의 정상 수정안 my_rewrites를 전달한다. 숫자 없는 과장 실험의 bad_proposal은 전달하지 않는다. build_resume는 원본과 기존 출력 파일을 덮지 않는다. 파일이 만들어졌다는 출력과 사람 검토가 끝났다는 상태를 혼동하지 않는다.'),
    ],
  },
  {
    period: 5, after: '구조와 서식', slides: [
      task('Word 문장과 원문 대조', [
        '출력한 Resume_walkthrough.docx를 Word에서 열기',
        '의료 경력 문장을 찾아 원문의 서비스 범위와 비교',
        '직함·총괄 여부·빠진 사실을 확인하고 수정안 기록',
        '홈의 스타일에서 제목·본문 확인, 모든 페이지 점검',
      ], '내 DOCX + career_facts.json의 medical-polyp',
      '숫자 일치 외에 Role·범위·누락 확인',
      '생성 결과에서 해당 문장을 찾지 못하면 다른 버전의 파일을 열었는지 확인한다. 문장 수정은 Notebook의 my_rewrites에 반영하고 새 버전 DOCX를 만든다. Word 화면에서만 고친 내용은 다음 코드 실행 때 유지되지 않는다는 점을 설명한다. PDF 인쇄본도 만들면 줄바꿈과 페이지 나눔을 비교할 수 있다.'),
    ],
  },
  {
    period: 6, after: '자동화 방식의 차이', slides: [
      code('Node.js와 PPT 패키지 확인',
`node --version
npm --version
npm list --prefix labs/day4/office_lab/presentations pptxgenjs
# 패키지가 없을 때만 실행
npm install --prefix labs/day4/office_lab/presentations`,
      ['저장소 루트의 터미널 / Python 셀이 아님',
       'node가 없으면 설치 후 터미널·Notebook 커널 재시작'],
      '이미 Node와 pptxgenjs가 있으면 재설치하지 않는다. node 명령을 못 찾으면 Node.js 공식 설치 안내에서 운영체제에 맞는 LTS를 준비한다. npm install에는 인터넷이 필요하다. 설치 후 Notebook의 Node.js 준비 셀을 다시 실행하여 새 PATH를 확인한다. 개인 계정 로그인이나 API 키는 이 코드 생성에 필요하지 않다. 설치 안내: https://nodejs.org/en/download'),
    ],
  },
  {
    period: 6, after: '프로젝트 데이터 준비', slides: [
      code('수정 WBS의 보고서 입력 저장',
`from labs.day4.office_lab.presentations.brief_data import (
    write_brief,
)
brief_path = write_brief(
    ROOT, str((RUN / "ppt/walkthrough.json").relative_to(ROOT)),
    tasks=tasks_my, as_of=AS_OF,
)
print(brief_path)`,
      ['4차시의 tasks_my와 고정 기준일 AS_OF 재사용',
       '같은 출력 이름이 있으면 walkthrough_v2.json 사용'],
      'Notebook 앞선 셀에서 준비한 ROOT와 RUN을 사용한다. 이 경로는 수정한 WBS를 다시 계산하여 새로운 JSON을 저장한다. 원래 Notebook의 보고서 부제를 직접 바꾼 경로와 구분한다. 표시된 brief_path를 다음 PPT 실행에 전달하며 예전 brief.json을 잘못 선택하지 않는다.'),
    ],
  },
  {
    period: 6, after: '학생용 PPT 생성', slides: [
      task('Notebook의 PPT 생성 순서', [
        'Node.js 준비 셀 실행, 두 준비 상태 모두 확인',
        'JSON 저장 셀 아래에 추가 코드 셀로 walkthrough.json 저장',
        '생성 셀의 파일명을 Project_Brief_walkthrough.pptx로 변경',
        'PPT 생성 셀 실행 후 출력 링크로 실제 파일 열기',
      ], 'Notebook 7차시 / student_ppt.mjs / 내 brief_path',
      'PPT 생성 완료 메시지와 실제 7장 파일 확인',
      'RUN/ppt 아래의 새 이름을 사용한다. 새 JSON을 저장한 뒤 기존 JSON 준비 셀을 다시 실행하면 brief_path가 기존 경로로 바뀐다. 추가 셀 이후 Node 준비·PPT 생성·구조 검사만 실행한다. 생성 미실행은 완료가 아니다. 파일이 이미 있으면 새 이름을 사용한다. 코드 실행의 cwd는 ROOT이며 JSON과 출력 모두 저장소 내부 경로다.'),
    ],
  },
  {
    period: 6, after: '보고서 재생성', slides: [
      code('완료·지연 수치의 입력 대조',
`data = json.loads(brief_path.read_text(encoding="utf-8"))
rows = calculate_wbs(tasks_my, AS_OF)
counts = {r[0]: int(r[1]) for r in data["slides"][1]["table"][1:]}
for status in ("완료", "지연"):
    expected = sum(r["status"] == status for r in rows)
    assert counts[status] == expected
assert data["wbs_snapshot"] == tasks_my
print(counts)`,
      ['W04만 완료 처리한 입력: 완료 5개 / 지연 1개',
       '서로 다른 기준일·입력 파일이면 비교 중단'],
      '저장한 JSON을 실제로 다시 읽어 계산 결과와 비교한다. Excel 파일의 수식을 읽은 결과가 아니라 같은 WBS 입력을 각 출력에 전달한 비교다. assert 실패 시 tasks_my를 JSON 저장 뒤에 다시 바꾸었는지, AS_OF가 동일한지 확인하고 JSON과 PPT를 함께 새 버전으로 생성한다.'),
    ],
  },
  {
    period: 6, after: '편집 가능한 표 확인', slides: [
      task('지연 업무와 보고 문장 비교', [
        '새 PPT 2장의 일정 현황에서 지연 업무 1개 확인',
        '3장의 W04는 완료, W05는 지연인지 비교',
        '7장의 후속 작업에서 W05의 지연 원인 확인 문장 검토',
        '표와 문장이 다르면 입력·생성 코드 확인 후 재생성',
      ], '내 PPT 2·3·7장 / W04 완료 입력 기준',
      '업무 수가 같아도 후속 작업 문장은 별도 확인',
      'W04만 완료로 바꾼 수업 입력을 기준으로 한다. 표가 맞는데 마지막 장에 예전 지연 업무가 남아 있으면 보고서가 잘못된 후속 작업을 유도할 수 있다. 해당 문장이 현재 상태에서 파생되는지 확인한다. 단순 숫자 일치 검사를 통과했다고 모든 설명이 맞는 것은 아니다.'),
    ],
  },
  {
    period: 6, after: 'Codex의 레이아웃 수정', slides: [
      task('긴 업무명과 표 너비 조정', [
        '같은 폴더에 student_ppt_my.mjs라는 코드 복사본 생성',
        'Codex에 긴 업무명 행의 colW·rowH 조정 요청',
        'Notebook 실행 파일명을 복사본으로 바꾸고 새 PPT 생성',
        '모든 7장에서 14개 업무의 누락·줄 잘림 확인',
      ], 'labs/day4/office_lab/presentations/student_ppt_my.mjs',
      '표 편집 유지 / 글씨 축소보다 열 너비·행 높이 조정',
      'student_ppt_my.mjs는 학생이 새로 만드는 파일이다. 같은 presentations 폴더에 두어 이미 설치된 pptxgenjs를 사용할 수 있게 한다. 긴 업무명을 별도 tasks_long 복사본에서 하나만 늘려 재현하고 prepare_brief 또는 write_brief에 그 입력을 전달한다. Codex 요청에 총 14개 업무, 7장, 표 수치 유지 조건을 명시한다. 마지막에는 PDF 인쇄본에서도 각 장표를 확인한다.'),
    ],
  },
];
