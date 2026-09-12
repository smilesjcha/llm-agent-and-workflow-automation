// Student-facing selection material. Catalog entries are proposals, not 36 built services.
const table=(title,headers,rows,note,phase='theory')=>({type:'table',title,headers,rows,note,phase});
const points=(title,points,note,phase='theory')=>({type:'points',title,points,note,phase});
const prompt=(title,prompt,check,note,phase='demo')=>({type:'prompt',title,prompt,check,note,phase});
const code=(title,code,explain,note,phase='lab')=>({type:'code',title,code,explain,note,phase});

export const PROJECT_CATEGORIES=[
  {name:'PM · 프로젝트 관리',rows:[
    ['PM01 일정·지연 점검','업무 JSON → WBS Excel','기본 코드 준비'],
    ['PM02 주간 보고서','같은 WBS → 보고 PPT','기본 코드 준비'],
    ['PM03 변경 요청 대장','요청 CSV → 변경 목록','새 로직 구현'],
    ['PM04 위험 점검표','위험 CSV → 검토 HTML','새 로직 구현'],
  ]},
  {name:'고객지원 · 운영',rows:[
    ['CS01 문의 분류','익명 문의 → 분류 CSV','새 로직 구현'],
    ['CS02 FAQ 답변 초안','질문·FAQ → 근거 있는 MD','새 로직 구현'],
    ['CS03 상담 인계','상담 기록 → 인계 DOCX','새 로직 구현'],
    ['CS04 VOC 집계','문의 목록 → 유형별 표','새 로직 구현'],
  ]},
  {name:'영업 · 제안',rows:[
    ['SA01 후속 연락 점검','활동 CSV → 예정 목록','새 로직 구현'],
    ['SA02 견적 초안','승인 단가 → 견적 DOCX','새 로직 구현'],
    ['SA03 미팅 후속 초안','합의 사항 → 메일 MD','새 로직 구현'],
    ['SA04 제안 조건 비교','조건 CSV → 비교 Excel','새 로직 구현'],
  ]},
  {name:'콘텐츠 · 마케팅',rows:[
    ['MK01 콘텐츠 일정','게시 계획 → 일정 Excel','기본 코드 응용'],
    ['MK02 캠페인 URL 검사','링크 CSV → 오류 목록','새 로직 구현'],
    ['MK03 광고 문구 검토','문구·근거 → 확인 목록','새 로직 구현'],
    ['MK04 성과 보고','지표 CSV → 요약 PPT','출력 코드 응용'],
  ]},
  {name:'HR · 개인 경력',rows:[
    ['HR01 경력 문서','경력 사실 → 이력서 Word','기본 코드 준비'],
    ['HR02 포트폴리오 목록','프로젝트 CSV → 소개 HTML','새 로직 구현'],
    ['HR03 온보딩 안내','업무 목록 → 체크리스트','기본 코드 응용'],
    ['HR04 학습 계획','자가 점검 → 학습 목록','새 로직 구현'],
  ]},
  {name:'교육 · 학습 운영',rows:[
    ['ED01 객관식 채점','합성 답안 → 채점 Excel','기본 코드 준비'],
    ['ED02 문항 형식 검사','문항 JSON → 오류 목록','새 로직 구현'],
    ['ED03 학습 피드백','교사 확인 항목 → Word','출력 코드 응용'],
    ['ED04 출결 집계','합성 출결 → 집계 Excel','새 로직 구현'],
  ]},
  {name:'경영지원 · 문서',rows:[
    ['AD01 지출 자료 점검','지출 CSV → 누락 목록','새 로직 구현'],
    ['AD02 업무 인수인계','담당 업무 → 인계 Word','출력 코드 응용'],
    ['AD03 문서 갱신 점검','기한 CSV → 예정 목록','새 로직 구현'],
    ['AD04 구매 조건 비교','제품 조건 → 비교 Excel','새 로직 구현'],
  ]},
  {name:'개발 · 운영',rows:[
    ['DV01 PR 리뷰 작업대','합성 diff → 리뷰 HTML','기본 코드 준비'],
    ['DV02 테스트 실패 분류','pytest 로그 → 오류 MD','새 로직 구현'],
    ['DV03 릴리스 점검','상태 JSON → 점검 HTML','새 로직 구현'],
    ['DV04 실행 이력 보고','로그 CSV → 실패 집계','새 로직 구현'],
  ]},
  {name:'지식 · 회의',rows:[
    ['KN01 회의 할 일','회의 TXT → 할 일 목록','2주차 코드 응용'],
    ['KN02 결정 변경 비교','신·구 기록 → 차이 MD','새 로직 구현'],
    ['KN03 자료 찾아보기','허용 MD → 검색 HTML','새 로직 구현'],
    ['KN04 회의 사전 브리프','지정 자료 → 근거 목록','새 로직 구현'],
  ]},
];

const referenceNotes={
  'PM · 프로젝트 관리':' 공식 구조 참고: https://developers.google.com/apps-script/samples/automations/generate-pdfs . 입력 데이터와 문서 템플릿 분리를 참고한 강사 제안이며 같은 서비스를 복제하거나 실행했다는 뜻은 아니다.',
  '고객지원 · 운영':' 공식 구조 참고: https://developers.google.com/apps-script/samples/automations/mail-merge . 입력 필드와 문장 템플릿 연결만 참고하며 공식 샘플의 실제 메일 발송은 수업 범위에서 제외한다.',
  '영업 · 제안':' 공식 구조 참고: https://developers.google.com/apps-script/samples/automations/generate-pdfs . 문서 생성과 전달 단계의 분리를 참고한다. 법률·세무 판단이나 실제 청구·메일 발송은 하지 않는다.',
  '개발 · 운영':' 공식 구조 참고: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows . 이벤트와 job/step의 구분을 참고하되 150분 기본 결과는 로컬 검사다.',
  '경영지원 · 문서':' 공식 구현 참고: https://python-docx.readthedocs.io/en/latest/user/quickstart.html . 제목·문단·표 생성 API의 참고이며 문서 내용의 정확성은 사람 검토 대상이다.',
};
const catalogSlides=PROJECT_CATEGORIES.map(category=>({
  ...table(category.name,['프로젝트','입력과 결과','출발 상태'],category.rows,
    '선택 참고 페이지. 4개를 모두 구현하거나 강의 중 실습하지 않는다. 수강생의 업무에 가까운 한 가지를 고른다. 기본 코드 준비도 해당 예제 범위만 검증된 상태이며 확장 기능은 별도 구현이다. 자세한 사용자·최소 기능·오류 두 건·사람 확인은 materials/day5/업무자동화_프로젝트_선택가이드.md의 같은 ID를 참고한다. 카탈로그는 강사가 설계한 제안이며 실제 기업 도입 사례나 구현 완료 목록이 아니다.'+(referenceNotes[category.name]??'')),
  reference:true,
  activityLabel:'Ideation · 선택 참고',
}));

export const PROJECT_ENRICHMENT=[
  {period:7,after:'개인 프로젝트 선택',slides:catalogSlides},
  {period:7,after:'개인 과제의 범위',slides:[
    points('사용자 한 명의 반복 업무',[
      'PM 민지: 매주 WBS에서 지연 업무 확인',
      '입력: 업무 14개와 이번 기준일',
      '첫 결과: 확인이 필요한 업무의 로컬 목록',
    ],'가상 사용자다. 실제 인물이나 절감 시간을 주장하지 않는다. 전체 프로젝트 관리 솔루션 대신 매주 반복되는 조회 하나를 선택한다. 지연 판단은 입력 날짜와 진척률로 계산하며 사람은 실제 사유를 확인한다. 짧게 사례를 설명하고 각자 비슷한 작업을 떠올릴 시간을 준다.'),
    {...table('첫 버전과 이후 확장',['구분','첫 버전','나중의 개선'],[
      ['입력','지정한 파일 한 개','여러 시스템 수집'],
      ['판단','날짜·상태의 명시적 규칙','AI의 원인 설명'],
      ['결과','새 로컬 CSV 한 개','메일·Slack 전달'],
      ['확인','정상 1건·실패 2건','다중 사용자·운영 로그'],
    ],'150분은 모든 행의 오른쪽 기능까지 만드는 시간이 아니다. 왼쪽 경로를 실제로 실행하고 검증한다. 외부 시스템 수집은 읽기 권한과 범위부터 설계해야 하고 원격 전송은 내용·수신자·계정의 별도 사람 승인을 받아야 한다.'),activityLabel:'Ideation · 범위 선택'},
    {...table('입력 파일의 세 가지 상태',['파일','준비 내용','확인할 차이'],[
      ['sample_normal.json','형식이 맞는 업무 목록','기본 결과 생성'],
      ['sample_bad_date.json','끝 날짜가 시작보다 빠름','날짜 오류 거절'],
      ['sample_bad_id.json','존재하지 않는 선행 ID','관계 오류 거절'],
    ],'이 세 파일명은 학생이 새로 준비할 파일명이다. 이미 배포한 파일이라고 표현하지 않는다. 출발점은 labs/day4/office_lab/sheets/wbs_tasks.json. 원본을 복사하고 한 값씩만 바꿔 오류 원인을 명확히 한다. 여기서는 입력 사례를 설계하며 실제 생성·실행은 다음 코드 단계다.'),activityLabel:'Ideation · 입력 설계'},
    prompt('첫 제작 요청','wbs_tasks.json과 student_excel.py를 읽어 줘. PM이 이번 기준일의 지연 업무만 보는 로컬 목록이 필요해. 입력 파일은 보존하고, calculate_wbs의 결과를 필터링하는 작은 함수를 제안해 줘. 파일 생성과 실행 전에 변경 위치·정상 사례·실패 사례 두 가지를 먼저 보여 줘. 외부 연결과 게시 기능은 제외해 줘.','사용자 · 입력 경로 · 최소 함수 · 금지 행동','학생이 입력할 대화 예시이며 실제 실행 기록이 아니다. Codex 로컬 작업은 본인의 프로젝트 폴더를 선택하고, 첨부형 대화에서는 해당 두 파일을 첨부한다. 계획만 받았으면 구현 완료로 표시하지 않는다.'),
  ]},
  {period:7,after:'개선 기능의 첫 구현',slides:[
    code('기존 계산의 재사용',
      'from labs.day4.office_lab.sheets.student_excel import (\n    load_sample, calculate_wbs\n)\ndef delayed_tasks(tasks, as_of):\n    rows = calculate_wbs(tasks, as_of)\n    return [row for row in rows if row["status"] == "지연"]\nitems = delayed_tasks(load_sample("wbs_tasks.json"),\n                      "2026-09-25")\nprint([row["id"] for row in items])',
      ['기본 입력: 지연 업무 2개','새 함수는 계산을 다시 만들지 않고 결과를 선택'],
      '저장소 루트 또는 ROOT가 잡힌 Notebook에서 실행한다. 제공 calculate_wbs의 결과를 재사용한 새 함수 예시다. 입력 검사에서 문제가 나면 예외를 정상 빈 목록으로 바꾸지 않는다. 이 셀은 필터 계산까지만 수행하며 CSV 저장은 다음 구현 요청의 범위다.'),
    {...table('직접 확인할 세 가지 결과',['입력','기대 결과','확인 방법'],[
      ['제공 업무·09/25','W04·W05 선택','ID와 원본 행 비교'],
      ['종료일 역전','입력 오류로 중단','오류 코드와 위치 확인'],
      ['없는 선행 ID','입력 오류로 중단','해당 ID 복구 후 재실행'],
    ],'정상 결과 2건을 실제로 출력하고 ID를 확인한다. 실패 두 건은 deepcopy로 원본을 보존한 입력에 하나씩 주입한다. 이 지연 필터는 사람의 지연 사유 판단이나 담당자 평가를 자동화하지 않는다. 입력이 올바른데 지연이 없는 경우는 빈 목록이라는 정상 결과다.','lab'),activityLabel:'코드·파일 작업'},
    prompt('파일 저장과 재실행 요청','확인한 delayed_tasks 결과를 새 CSV로 저장해 줘. 입력 파일의 작업 폴더 밖 접근과 기존 출력 파일 덮어쓰기는 막아 줘. 정상 입력, 날짜 오류, 없는 선행 ID를 테스트하고 실제 명령과 결과를 남겨 줘. README에는 설치·입력·실행·결과 경로만 먼저 적어 줘. 내가 CSV를 열어 확인한 뒤 다음 기능을 정할게.','실제 CSV · 테스트 출력 · 새 폴더 재실행','실제 코드 제작으로 이어지는 요청 예시다. CSV 저장기와 해당 테스트는 새 구현이 필요하며 이미 제공되어 있다고 말하지 않는다. 150분 내 이 단계가 막히면 원인을 기록하고 기존 XLSX 경로를 이용한다. 원격 API·메일 전송은 기본 범위 밖이다.','lab'),
  ]},
];
