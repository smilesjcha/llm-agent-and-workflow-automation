import { COURSE_DAYS, DAY_TIMES } from "./days2_5_content.mjs";

const BASE = COURSE_DAYS[2].periods;

const DETAILS = [
  {
    shortTitle: "Meeting Agent Architecture",
    label: "Request Router",
    subtitle: "LLM · Workflow · Agent · Human Review",
    focusTitle: "LLM·Workflow·Agent 역할",
    conceptTitle: "판단량과 실행 방식",
    processTitle: "회의 기록 서비스 구조",
    decisionTitle: "요청 유형별 선택 기준",
    filesTitle: "Router 파일 구조",
    demoTitle: "요청 분류 Demo",
    resultTitle: "Architecture 결과",
    codexTitle: "Codex Task · 최소 실행 구조",
    labATitle: "Router 규칙 실행",
    labBTitle: "승인 없는 발송 차단",
    completionTitle: "1차시 완료 기준",
    phaseTimes: ["0-13분", "13-21분", "21-43분", "43-50분"],
    focus: "한 번의 생성, 고정 절차, 상황별 판단을 구분하는 제품 구조",
    setup: [
      "Python 3.12 · VS Code · Jupyter Kernel",
      "Repository clone · workspace root 확인",
      "materials/day2/day2_service_lab.ipynb 실행 준비",
    ],
    optional: ["Codex login", "Claude Code login", "API Key 불필요"],
    fileRoles: [
      ["읽기", "materials/day2/일반인을_위한_회의기록_Agent_설계.md"],
      ["실행", "materials/day2/day2_service_lab.ipynb · 1차시"],
      ["구현", "src/course_services/day2_meeting_workflow.py"],
      ["검증", "python -m pytest -q tests/test_day2_meeting_workflow.py -k rule_router"],
    ],
    terms: [
      ["LLM", "주어진 맥락으로 한 번의 결과를 생성"],
      ["Workflow", "순서·검증·오류 처리를 코드로 고정"],
      ["Agent", "상황에 따라 Route·Tool·다음 행동 선택"],
      ["Human Review", "외부 저장·발송 전 Approve·Edit·Reject"],
    ],
    conceptFiles: [
      "route_execution_strategy()",
      "run_meeting_workflow()",
      "compare_execution_strategies()",
      "start_*() · resume_*()",
    ],
    decisions: [
      ["한 번의 요약·변환", "LLM", "도구 선택 없음"],
      ["항상 같은 처리 순서", "Workflow", "단계·오류 규칙 고정"],
      ["자료·도구·다음 행동 선택", "Agent", "정책·비용 상한 필요"],
    ],
    demo: [
      "세 요청을 Router에 입력",
      "선택된 실행 방식과 이유 확인",
      "외부 저장·발송 요청의 승인 대기 확인",
    ],
    resultChecks: [
      "layer_count · fixed_graph",
      "agent_views",
      "human_review_required",
      "external_write=false",
    ],
    mapCheck: "6개 Layer · 7단계 Graph\n발송 요청 승인 대기",
    labA: [
      "Notebook 1차시 Cell 실행",
      "fixed_meeting_record·context_retrieval·one_off 비교",
      "01_architecture.json 저장 확인",
    ],
    labB: [
      "자동 이메일 요청을 Blocked case로 추가",
      "external_write=false 확인",
      "Focused Test 재실행",
    ],
    codexPrompt: [
      "목표: 세 요청 유형 Router의 최소 구조",
      "허용: day2_meeting_workflow.py와 해당 Test만 수정",
      "필수: Happy Path와 승인 없는 발송 차단 Test",
      "금지: .env·외부 API·자동 게시 변경",
    ],
    notebookSnippet: `route_cases = {
    "single_llm": route_execution_strategy(
        requested_actions=["rewrite_as_podcast_script"]),
    "workflow": route_execution_strategy(
        requested_actions=["normalize", "summarize", "todos"]),
    "agent": route_execution_strategy(
        requested_actions=["summarize", "todos"],
        external_context_sources=["notion", "slack"]),
}
gate = external_action_approval_gate(
    "send_meeting_email", human_approved=False)
architecture["three_route_cases"] = route_cases
architecture["external_action_approval_gate"] = gate
assert gate["error_code"] == \
       "EXTERNAL_ACTION_HUMAN_APPROVAL_REQUIRED"`,
    success: "요청 유형·선택 방식·선택 이유가 함께 반환",
    expectedError: "승인 없는 외부 행동은 EXTERNAL_ACTION_HUMAN_APPROVAL_REQUIRED",
    externalRule: "저장·발송 요청은 Human Review 대기",
    externalState: "APPROVAL_REQUIRED",
    recovery: ["요청 문장 확인", "Router 규칙 확인", "Test 이름 확인", "Diff 검토"],
    applications: [
      ["재직자", "반복 업무의 LLM·Workflow·Agent 분류표"],
      ["구직자", "선택 이유와 Guardrail이 있는 Architecture README"],
    ],
    completion: ["세 실행 방식 설명", "Router Test 통과", "01_architecture.json 확인"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k rule_router",
    demoCommand: "jupyter lab materials/day2/day2_service_lab.ipynb",
    saveLine: 'save_json("01_architecture.json", architecture)',
    image: "day2-agent-architecture.png",
    sources: ["local:materials/day2/일반인을_위한_회의기록_Agent_설계.md"],
  },
  {
    shortTitle: "Input Route · STT",
    label: "Input Adapter",
    subtitle: "Google Meet TXT · ClovaNote TXT · Audio",
    focusTitle: "세 입력과 공통 Format",
    conceptTitle: "텍스트 우선, 음성만 STT",
    processTitle: "Meet·ClovaNote·Audio Input Route",
    decisionTitle: "입력 유형별 처리 방식",
    filesTitle: "Input Adapter 파일 구조",
    demoTitle: "세 입력 Adapter Demo",
    resultTitle: "Input Adapter 결과",
    codexTitle: "Codex Task · Input Adapter Test",
    labATitle: "공개 음성·Sample 선택",
    labBTitle: "TranscriptEnvelope 생성",
    completionTitle: "2차시 완료 기준",
    phaseTimes: ["0-10분", "10-20분", "20-45분", "45-50분"],
    focus: "이미 존재하는 전사는 그대로 사용하고, 녹음 파일에만 STT를 적용하는 입력 구조",
    setup: [
      "ffmpeg · ffprobe 설치 확인",
      "공개 10분 MP3 또는 비식별 Sample WAV",
      "텍스트 편집기 · Notebook 2차시 Cell",
    ],
    optional: ["faster-whisper small", "CPU int8", "모델 사전 다운로드"],
    terms: [
      ["Input Adapter", "Meet TXT·ClovaNote TXT·음성을 같은 입력 규격으로 변환"],
      ["TranscriptEnvelope", "출처·발화 ID·시간·화자·STT 정보를 묶은 공통 그릇"],
      ["Reviewed Fixture", "강사가 음성과 전사를 미리 맞춰 본 기본 재현 경로"],
      ["Live STT Opt-in", "사용자가 켰을 때만 실제 faster-whisper를 실행하는 선택 경로"],
    ],
    fileRoles: [
      ["출처", "data/day2_public_audio/sources.json"],
      ["입력", "meeting_ko_ccby_excerpt_10m.mp3 · Sample TXT"],
      ["실행", "scripts/day2_public_audio.py · Notebook 2차시"],
      ["검증", "python -m pytest -q tests/test_day2_meeting_workflow.py -k source"],
    ],
    conceptFiles: [
      "normalize_source()",
      "adapt_audio_stt()",
      "SourceInput.source_mode",
      "TranscriptEnvelope",
    ],
    decisions: [
      ["Meet 전사", "TXT Parser", "화자·시간 유지"],
      ["ClovaNote 내보내기", "TXT Adapter", "참석자 번호 매핑"],
      ["녹음 파일", "Local STT", "Timestamp Segment 생성"],
    ],
    demo: [
      "공개 MP3\n파일 경로·라이선스",
      "세 Input Adapter\n공통 TranscriptEnvelope",
      "출처·Segment ID\nSTT Metadata",
    ],
    resultChecks: [
      "source_mode_count",
      "segment_ids_preserved",
      "stt_metadata",
      "mixed_input_error",
    ],
    mapCheck: "세 Input Adapter\n입력 혼합 오류 차단",
    labA: [
      "기본 Run All의 Reviewed Fixture Label 확인",
      "공개 10분 MP3 경로·SHA-256·출처 확인",
      "강사 Demo: 75초 Live STT Segment·Timestamp 확인",
    ],
    labB: [
      "Notebook 2차시 Cell 실행",
      "세 입력의 source_mode 비교",
      "입력 혼합 차단 Error Code 확인",
    ],
    codexPrompt: [
      "목표: 세 입력 Adapter의 공통 TranscriptEnvelope",
      "허용: Input Adapter·Test·비식별 Fixture만 수정",
      "Test: 빈 TXT·손상 음성·입력 혼합·무음 대체 금지",
      "금지: 다른 회의 전사 대체·외부 API 자동 실행",
    ],
    notebookSnippet: `# 기본: 검토 완료 Fixture / 선택: 실제 Local STT
fixture_lane = {
    "label": "Reviewed Transcript Fixture",
    "live_stt": False,
    "silent_substitution": False,
}
live_stt = run_optional_local_stt_smoke(
    resolved_public_audio,
    workspace_root=ROOT,
    live_opt_in=os.getenv(
        "FASTER_WHISPER_LIVE_OPT_IN", "0") == "1",
)
assert fixture_lane["silent_substitution"] is False
assert live_stt["transcript_substituted"] is False`,
    success: "각 입력의 출처 유형과 발화 구간 ID 보존",
    expectedError: "Live STT 실패 시 다른 음성의 전사로 대체 없음",
    externalRule: "Input Adapter 단계의 외부 서비스 호출 없음",
    externalState: "로컬 결과 생성",
    recovery: ["입력 확장자 확인", "ffmpeg 확인", "Source Mode 확인", "Sample 경로로 재시작"],
    applications: [
      ["재직자", "Meet·ClovaNote·녹음의 단일 업로드 화면"],
      ["구직자", "세 Adapter와 Input Validation Test"],
    ],
    completion: ["세 입력 차이 설명", "Adapter 실행", "02_inputs.json 확인"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k three_source\npython -m pytest -q tests/test_day2_meeting_workflow.py -k source_mode_mixing",
    demoCommand: "python scripts/day2_public_audio.py resolve",
    saveLine: 'save_json("02_inputs.json", input_result)',
    image: "public-korean-meeting-source.png",
    sources: [
      "local:materials/day2/공개_한국어_회의음성_가이드.md",
      "https://creativecommons.org/licenses/by/4.0/",
    ],
  },
  {
    shortTitle: "Domain Context · MCP Policy",
    label: "MCP Policy",
    subtitle: "업무 용어 · 이전 결정 · Read Scope",
    focusTitle: "업무 맥락과 검색 범위",
    conceptTitle: "회의 발화와 사전 맥락의 분리",
    processTitle: "MCP Read Plan",
    decisionTitle: "Connector별 허용 범위",
    filesTitle: "Context·Policy 파일 구조",
    demoTitle: "Read-only MCP Plan Demo",
    resultTitle: "MCP Context · Read Plan 결과",
    codexTitle: "Codex Task · MCP Policy Test",
    labATitle: "Domain Context 작성",
    labBTitle: "MCP Read Plan 생성",
    completionTitle: "3차시 완료 기준",
    phaseTimes: ["0-12분", "12-22분", "22-47분", "47-50분"],
    focus: "산업 용어와 이전 결정을 제공하되, 외부 도구는 필요한 범위만 읽는 정책",
    setup: [
      "Notion·Slack 계정 불필요",
      "비식별 Context Sample",
      "Notebook 3차시 Cell",
    ],
    optional: ["MCP Connector", "회사 Sandbox", "실제 Write 권한 사용 안 함"],
    terms: [
      ["MCP", "AI가 허용된 외부 정보원·도구를 공통 방식으로 연결하는 규약"],
      ["Read-only", "조회만 허용하고 문서 작성·메시지 발송은 막은 권한"],
      ["Scope", "읽을 수 있는 Project·Page·Channel의 허용 범위"],
      ["PLAN_ONLY", "실제 Connector를 부르지 않고 승인용 실행 계획만 만든 상태"],
    ],
    fileRoles: [
      ["가이드", "materials/day2/Codex_Claude_대화_시나리오.md"],
      ["실행", "materials/day2/day2_service_lab.ipynb · 3차시"],
      ["구현", "build_mcp_retrieval_plan()"],
      ["결과", "output/course-labs/day2-v2/03_domain_context.json"],
    ],
    conceptFiles: [
      "DomainContext",
      "build_mcp_retrieval_plan()",
      "MCPRetrievalPolicy",
      "test_mcp_retrieval_plan_*",
    ],
    decisions: [
      ["산업 용어", "Domain Context", "뜻과 사용 기준"],
      ["이전 합의", "Prior Decisions", "회의 발화와 별도 표시"],
      ["외부 자료", "MCP Read Policy", "기간·공간·개수 제한"],
    ],
    demo: [
      "이커머스 CX 용어\n이전 결정",
      "Notion·Confluence·Slack\nRead Plan",
      "executed=false\nexternal_write=false",
    ],
    resultChecks: [
      "connector_count · lookback_days",
      "scope_allowlist · max_items",
      "executed=false",
      "external_write=false",
    ],
    mapCheck: "Read Plan 1건\n실제 Connector 미실행",
    labA: [
      "자신의 산업·업무 목적 한 문단 작성",
      "용어 3개와 이전 결정 2개 입력",
      "발화 근거와 사전 맥락의 표시 차이 확인",
    ],
    labB: [
      "허용 Connector와 14일 범위 설정",
      "허용 Project·Channel 지정",
      "Read Plan만 생성되고 실행되지 않음 확인",
    ],
    codexPrompt: [
      "목표: 필요한 회의 맥락만 찾는 Read Plan",
      "허용: Read Plan·Policy Test·비식별 Fixture만 수정",
      "Test: Connector·14일·Scope·최대 5개·Write 차단",
      "금지: 실제 Connector 호출·Private DM·Write Tool",
    ],
    notebookSnippet: `policy = MCPRetrievalPolicy(
    allowed_connectors=["notion"],
    explicit_user_authorization=True,
    lookback_days=14,
    allowed_scopes={"notion": ["CX PoC"]},
    max_items_per_connector=5,
)
context_result = build_mcp_retrieval_plan(
    envelope=envelopes["google_meet_text"],
    domain=domain_context, policy=policy,
)
assert context_result["executed"] is False
assert context_result["external_write"] is False`,
    success: "Connector·기간·Scope·선택 이유를 가진 Read Plan",
    expectedError: "허용 범위를 벗어난 Channel·기간·고객 문서는 POLICY_BLOCKED",
    externalRule: "MCP Connector 미실행 · Read Plan만 생성",
    externalState: "PLAN_ONLY",
    recovery: ["사용자 승인 확인", "Connector 확인", "기간 축소", "Scope 재입력"],
    applications: [
      ["재직자", "팀 지식 검색 범위를 통제하는 회의 Assistant"],
      ["구직자", "Least Privilege가 반영된 MCP Policy Spec"],
    ],
    completion: ["Domain Context 작성", "Read Plan 생성", "03 JSON 확인"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k mcp_retrieval_plan",
    demoCommand: "jupyter lab materials/day2/day2_service_lab.ipynb",
    saveLine: 'save_json("03_domain_context.json", context_result)',
    image: "mcp-context-policy.png",
    fullScreenDemo: true,
    sources: ["https://modelcontextprotocol.io/introduction"],
  },
  {
    shortTitle: "MeetingRecord Schema",
    label: "MeetingRecord",
    artifact: "04_meeting_record_contract.json",
    subtitle: "Summary · Perspectives · To Do · Insights · Evidence",
    focusTitle: "회의 기록의 공통 결과 형식",
    conceptTitle: "자유 문장과 Structured Output",
    processTitle: "MeetingRecord 생성 순서",
    decisionTitle: "Field별 작성 원칙",
    filesTitle: "Schema·Validator 파일 구조",
    demoTitle: "MeetingRecord Validation Demo",
    resultTitle: "MeetingRecord 결과",
    codexTitle: "Codex Task · Schema와 Validator",
    labATitle: "MeetingRecord 생성",
    labBTitle: "원문 근거 Validation",
    completionTitle: "4차시 완료 기준",
    phaseTimes: ["0-10분", "10-20분", "20-48분", "48-50분"],
    focus: "요약·관점·할 일·인사이트를 원문 구간과 연결하는 재사용 가능한 결과 형식",
    setup: [
      "Pydantic·LangGraph 설치",
      "Notebook 4차시 Cell",
      "세 입력 중 하나의 TranscriptEnvelope",
    ],
    optional: ["Ollama", "OpenAI API", "Provider 없이 Fixture 실행 가능"],
    terms: [
      ["MeetingRecord", "요약·관점·할 일·인사이트·근거를 묶은 최종 결과 규격"],
      ["TodoItem", "할 일·담당자·기한·근거 ID를 가진 실행 항목"],
      ["HorizonInsights", "단기·중기·장기 관점으로 나눈 회의 인사이트"],
      ["Evidence Validation", "결과의 근거 ID가 실제 발화 Segment에 있는지 확인"],
    ],
    fileRoles: [
      ["Schema", "MeetingRecord · TodoItem · HorizonInsights"],
      ["실행", "materials/day2/day2_service_lab.ipynb · 4차시"],
      ["Validator", "validate_record_evidence()"],
      ["결과", "04_meeting_record_contract.json"],
    ],
    conceptFiles: [
      "MeetingRecord",
      "Evidence Validator",
      "TodoItem · owner / due date",
      "MeetingRecord · well-being risks",
    ],
    decisions: [
      ["요약·결정", "원문 근거 필수", "evidence_ids"],
      ["담당자·기한", "추정 금지", "모르면 null"],
      ["Well-being Signal", "진단 금지", "발화와 완화 방안"],
    ],
    demo: [
      "Meet TXT →\nMeetingRecord",
      "Summary · Perspective\nTo Do · Insight",
      "Unknown Evidence\nValidation 차단",
    ],
    resultChecks: [
      "schema · field_count",
      "evidence_errors",
      "human_review_required",
      "external_write=false",
    ],
    mapCheck: "MeetingRecord 생성\n없는 근거 ID 차단",
    labA: [
      "Notebook 4차시 Cell 실행",
      "필수 Field와 nullable Field 구분",
      "실제 MeetingRecord Sample 저장",
    ],
    labB: [
      "존재하지 않는 evidence id 입력",
      "UNKNOWN_EVIDENCE Error 확인",
      "담당자·기한 null 정책 확인",
    ],
    codexPrompt: [
      "목표: MeetingRecord Schema와 근거 Validator",
      "허용: MeetingRecord·Validator·해당 Test만 수정",
      "Test: Unknown Evidence·임의 Owner·Extra Field",
      "금지: 임의 담당자·기한·개인 성향 추정",
    ],
    notebookSnippet: `result = run_meeting_workflow(
    sources["google_meet_text"],
    domain_context,
    review_decision="approve",
    retrieval_policy=retrieval_policy,
)
record = MeetingRecord.model_validate(result["record"])
envelope = TranscriptEnvelope.model_validate(result["envelope"])
errors = validate_record_evidence(record, envelope)
assert errors == []
assert record.external_write is False
record_contract_result = record.model_dump(mode="json")`,
    success: "모든 사실 Field가 실제 Segment ID와 연결",
    expectedError: "없는 근거·임의 담당자·추가 Field는 Validation 실패",
    externalRule: "검증된 MeetingRecord도 Local 결과로 유지",
    externalState: "Validation Only",
    recovery: ["Schema Error 위치 확인", "근거 ID 목록 비교", "nullable Field 확인", "MeetingRecord 재검증"],
    applications: [
      ["재직자", "회의 도구가 달라도 같은 결과를 쓰는 Data Model"],
      ["구직자", "Structured Output·Evidence Validator 구현"],
    ],
    completion: ["필수 Field 설명", "Sample Record 생성", "근거 오류 차단"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k meeting_record_matches",
    demoCommand: "jupyter lab materials/day2/day2_service_lab.ipynb",
    saveLine: 'save_json("04_meeting_record_contract.json", record_contract_result)',
    image: "meeting-record-schema-local.png",
    fullScreenDemo: true,
    sources: ["local:src/course_services/day2_meeting_workflow.py"],
  },
  {
    shortTitle: "Coding Agent Patch",
    label: "Codex Patch",
    artifact: "05_codex_run.json",
    subtitle: "Scenario Tree · Task Spec · Test · Diff Review",
    focusTitle: "Coding Agent와 작업 계약",
    conceptTitle: "Scenario Tree · Harness",
    processTitle: "Harness 기반 개발 순서",
    decisionTitle: "대화형 요청과 Task Spec 비교",
    filesTitle: "Coding Agent 작업 파일",
    demoTitle: "Codex Task 진행 화면",
    resultTitle: "Coding Agent 결과",
    codexTitle: "Codex Task · Human Review Policy",
    labATitle: "Starter 실패 재현",
    labBTitle: "Patch·Test·Diff Review",
    completionTitle: "5차시 완료 기준",
    phaseTimes: ["0-10분", "10-20분", "20-45분", "45-50분"],
    focus: "상위 모델에게 목표·허용 파일·Test·금지 행동을 함께 전달하는 개발 Workflow",
    setup: [
      "Codex App 또는 CLI Login",
      "labs/day2/codex-task/TASK.md",
      "작업 전 git status · Starter 실패 확인",
    ],
    optional: ["Claude Code /login", "독립 Review Session", "OpenAI API 불필요"],
    fileRoles: [
      ["Task", "labs/day2/codex-task/TASK.md"],
      ["Starter", "labs/day2/codex-task/starter/review_policy.py"],
      ["검증", "labs/day2/codex-task/task_check.py"],
      ["Diff", "git diff -- labs/day2/codex-task/starter/review_policy.py"],
    ],
    conceptFiles: [
      "labs/day2/codex-task/TASK.md",
      "AGENTS.md",
      "Codex Task",
      "git diff · Cross-Review",
    ],
    terms: [
      ["Scenario Tree", "입력·목적·오류 조건에 따른 여러 경로"],
      ["Harness", "Goal·Allowed·Test·Do not을 묶은 작업 계약"],
      ["Codex", "코드 수정·Test·Review를 수행하는 Coding Agent"],
      ["Independent Review", "다른 Session의 누락·권한·Fallback 검토"],
    ],
    decisions: [
      ["자유 대화", "탐색·아이디어", "빠르지만 재현성 낮음"],
      ["단계형 요청", "설계→구현→Test", "중간 확인 용이"],
      ["Task Spec", "목표·범위·Test·금지", "반복·Review 적합"],
    ],
    demo: [
      "수정 전 네 Case 중 실패 확인",
      "허용 파일·완료 Test를 Codex에 전달",
      "Patch·Test 결과·Diff를 사람이 검토",
    ],
    resultChecks: [
      "task_status=PASS",
      "case_count=4",
      "external_action_review=true",
      "external_write=false",
    ],
    mapCheck: "Starter 실패 → Patch\n4개 Case PASS",
    labA: [
      "task_check.py 실행 후 실패 Case 확인",
      "TASK.md의 Goal·Allowed·Test·Do not 확인",
      "Codex에 계획과 영향 파일 요청",
    ],
    labB: [
      "Starter 1개 파일 Patch 후 task_check 재실행",
      "05_codex_run.json의 4개 PASS 확인",
      "git diff와 독립 Review 후 사람 판단",
    ],
    codexPrompt: [
      "목표: requires_human_review Policy 완성",
      "허용: starter/review_policy.py 한 파일",
      "Test: local draft·email·Notion·evidence error 4건",
      "금지: task_check·solution·.env·외부 서비스 변경",
    ],
    notebookSnippet: `# Terminal · 수정 전 FAIL, Codex Patch 뒤 PASS
python labs/day2/codex-task/task_check.py \\
  --report output/course-labs/day2-v2/\\
student-run/05_codex_run.json

# 수정 허용 파일 1개
labs/day2/codex-task/starter/review_policy.py

# 사람 확인
git diff -- labs/day2/codex-task/starter/review_policy.py`,
    success: "네 Policy Case PASS와 external_write=false",
    expectedError: "수정 전 email·Notion·evidence error Case는 의도적으로 FAIL",
    externalRule: "자동 Commit·Merge 없이 Diff만 제안",
    externalState: "Human Merge",
    recovery: ["git status 확인", "Task 범위 축소", "Focused Test", "Diff 재검토"],
    applications: [
      ["재직자", "회사 Policy가 포함된 반복 개발 Task Spec"],
      ["구직자", "Prompt가 아닌 Test·Diff 기반 AI 협업 기록"],
    ],
    completion: ["Starter 실패 재현", "4개 Case PASS", "사람 Diff Review"],
    command: "python labs/day2/codex-task/task_check.py --report output/course-labs/day2-v2/student-run/05_codex_run.json",
    demoCommand: "python labs/day2/codex-task/task_check.py",
    saveLine: "student-run/05_codex_run.json",
    image: "codex-conversation-day2-local.png",
    fullScreenDemo: true,
    sources: [
      "https://developers.openai.com/codex/cli",
      "https://docs.anthropic.com/en/docs/claude-code/overview",
    ],
  },
  {
    shortTitle: "LLM Provider · Cost Guardrail",
    label: "Provider Adapter",
    subtitle: "Fixture · Ollama · OpenAI API · Codex · Claude",
    focusTitle: "Model Provider와 실행 비용",
    conceptTitle: "요청 모델과 실제 사용 모델",
    processTitle: "Provider 선택·Fallback Flow",
    decisionTitle: "무료·구독·API 선택표",
    filesTitle: "Provider Adapter 파일 구조",
    demoTitle: "Provider 진단 Demo",
    resultTitle: "Provider 진단 결과",
    codexTitle: "Codex Task · Provider Adapter",
    labATitle: "Ollama qwen3:4b 실행",
    labBTitle: "OpenAI Opt-in 진단",
    completionTitle: "6차시 완료 기준",
    phaseTimes: ["0-12분", "12-22분", "22-47분", "47-50분"],
    focus: "같은 결과 형식 뒤에서 로컬 모델·구독형 CLI·종량제 API를 안전하게 교체하는 구조",
    setup: [
      "Ollama · qwen3:4b 설치",
      "Notebook 6차시 Cell",
      ".env.example 확인 · Key 화면 노출 금지",
    ],
    optional: ["OPENAI_API_KEY", "OPENAI_LIVE_OPT_IN=1", "Codex·Claude CLI"],
    terms: [
      ["Provider Adapter", "모델마다 다른 호출 방식을 같은 입력·결과 계약 뒤에 숨기는 Code"],
      ["Fixture", "네트워크·비용 없이 항상 같은 결과를 내는 수업·Test용 응답"],
      ["Opt-in", "환경 변수 1로 명시한 경우에만 실제 Provider를 호출하는 경계"],
      ["Fallback Reason", "요청 모델 대신 다른 경로를 썼을 때 반드시 남기는 이유"],
    ],
    fileRoles: [
      ["설정", ".env.sample · *_LIVE_OPT_IN"],
      ["Adapter", "run_optional_cli_prompt() · run_optional_openai_record()"],
      ["검증", "validate_model_record_output() · Ollama qwen3:4b"],
      ["결과", "06_provider_diagnostics.json"],
    ],
    conceptFiles: [
      "diagnose_provider_options()",
      "run_optional_cli_prompt()",
      "validate_model_record_output()",
      "06_provider_diagnostics.json",
    ],
    decisions: [
      ["Fixture", "무료·결정적", "수업·회귀 Test"],
      ["Ollama", "로컬·무료", "개인정보·오프라인"],
      ["OpenAI API", "종량제", "고품질 반복 처리"],
      ["Codex·Claude", "구독·Login", "코드 제작·Review"],
    ],
    demo: [
      "Provider 준비 상태 조회",
      "Ollama 또는 Fixture 실행",
      "requested·used·model·fallback_reason 비교",
    ],
    statusDemoRows: [
      ["Fixture", "READY", "기본 완주 · Network 0회"],
      ["Ollama qwen3:4b", "LIVE PASS", "Schema · Evidence 실측 통과"],
      ["OpenAI API", "DEFAULT OFF", "Opt-in 없으면 Fixture와 이유 표시"],
      ["Codex · Claude", "LOGIN 선택", "코드 제작 · Review"],
    ],
    resultChecks: [
      "default_openai_used=fixture",
      "live_provider=ollama qwen3:4b",
      "schema_valid=true",
      "evidence_valid=true",
    ],
    mapCheck: "Ollama·OpenAI 진단\nFallback 이유 확인",
    labA: [
      "ollama list로 qwen3:4b 확인",
      "OLLAMA_LIVE_OPT_IN=1로 Notebook 6차시 실행",
      "MeetingRecord Schema·Evidence 검증",
    ],
    labB: [
      "기본 Opt-in false 결과 확인",
      "선택적으로 Live 진단 1회",
      "Model 미지원·Timeout Error Code 확인",
    ],
    codexPrompt: [
      "목표: Provider 교체 가능한 Adapter",
      "허용: Provider Adapter·해당 Test·.env.example",
      "Test: 미설정·미지원 Model·Timeout·Fallback Reason",
      "금지: Key·Raw Error·Credential 경로 출력",
    ],
    notebookSnippet: `load_dotenv(ROOT / ".env", override=False)
openai_live = os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1"
ollama_live = os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1"
openai_result = run_optional_openai_record(
    envelopes["google_meet_text"], domain_context,
    env=os.environ if openai_live else {},
    allow_fixture_fallback=True,
)
ollama_call = run_optional_cli_prompt(
    "ollama", ollama_prompt, live_opt_in=ollama_live,
    model="qwen3:4b")
ollama_check = validate_model_record_output(
    ollama_call["output_text"], envelopes["google_meet_text"])
assert ollama_check["fallback_used"] is False`,
    success: "선택 Provider와 실제 사용 Provider·Model이 명확히 표시",
    expectedError: "Key 미설정·Model 미지원·Timeout은 일관된 Error Code",
    externalRule: "Live Provider는 사용자 Opt-in 범위에서만 호출",
    externalState: "Opt-in Required",
    recovery: [
      "Provider 준비 상태 확인",
      "요청 Model 이름 확인",
      "Live Opt-in 설정 확인",
      "Fixture 또는 Ollama로 재실행",
    ],
    applications: [
      ["재직자", "데이터 민감도·비용에 따른 Provider 선택"],
      ["구직자", "Provider Adapter와 Deterministic Fallback Test"],
    ],
    completion: ["Ollama 실행", "Opt-in 차이 설명", "06 JSON 확인"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k 'openai_adapter or cli_providers'",
    replayCommand: "python -m pytest -q tests/test_day2_meeting_workflow.py -k openai_adapter",
    demoCommand: "ollama list\nOLLAMA_LIVE_OPT_IN=1 jupyter lab materials/day2/day2_service_lab.ipynb",
    saveLine: 'save_json("06_provider_diagnostics.json", provider_result)',
    image: "meeting-intelligence-provider-status-local.png",
    sources: ["https://developers.openai.com/api/docs/models/gpt-5.6-luna", "https://ollama.com/library/qwen3"],
  },
  {
    shortTitle: "LangGraph · Human Review",
    label: "Human Review",
    subtitle: "State · Conditional Edge · Interrupt · Resume",
    focusTitle: "Graph State와 Reviewer Decision",
    conceptTitle: "고정 Workflow와 중단 지점",
    processTitle: "Interrupt·Resume Flow",
    decisionTitle: "Approve·Edit·Reject 상태",
    filesTitle: "LangGraph 파일 구조",
    demoTitle: "Human Review Interrupt Demo",
    resultTitle: "Human Review 결과",
    codexTitle: "Codex Task · Review State Machine",
    labATitle: "Graph Interrupt 실행",
    labBTitle: "Approve·Edit·Reject Resume",
    completionTitle: "7차시 완료 기준",
    phaseTimes: ["0-10분", "10-20분", "20-48분", "48-50분"],
    focus: "검토 전 멈추고, 사람의 승인·수정·거절에 따라 다음 Node가 달라지는 실제 State Machine",
    setup: [
      "langgraph·checkpointer 설치",
      "Notebook 7차시 Cell",
      "MeetingRecord Sample",
    ],
    optional: ["LangSmith Trace", "별도 Project", "API Key 없이 Local 실행 가능"],
    fileRoles: [
      ["Graph", "build_interruptible_meeting_graph()"],
      ["State", "WorkflowState"],
      ["Notebook", "day2_service_lab.ipynb · 7차시"],
      ["결과", "07_human_review.json"],
    ],
    conceptFiles: [
      "WorkflowState",
      "build_interruptible_meeting_graph()",
      "interrupt() · InMemorySaver",
      "resume_interruptible_meeting_review()",
    ],
    terms: [
      ["State", "각 단계가 함께 사용하는 현재 결과"],
      ["Conditional Edge", "검증·사람 결정에 따라 다음 Node를 고르는 분기"],
      ["Checkpointer", "중단된 State와 thread_id를 저장해 같은 지점에서 재개"],
      ["Interrupt · Resume", "사람 결정을 기다렸다가 같은 Thread로 실행을 이어가는 한 쌍"],
    ],
    pipeline: ["입력 검증", "Graph 실행", "Evidence 검사", "Interrupt", "Resume·분기"],
    decisions: [
      ["Approve", "초안 생성", "외부 반영 없음"],
      ["Edit", "허용 Field 수정 후 재검증", "초안 생성"],
      ["Reject", "종료", "초안·외부 반영 없음"],
    ],
    demo: [
      "Graph 시작\nInterrupt Payload",
      "Approve·Edit\nCommand Resume",
      "Reject·Unknown Evidence\nDraft 차단",
    ],
    resultChecks: [
      "pause=interrupt()",
      "checkpointer · thread_id",
      "resume=Command(...)",
      "approve · edit · reject",
    ],
    mapCheck: "Approve·Edit·Reject\n최종 상태 3종",
    labA: [
      "Notebook 7차시 Interrupt Cell 실행",
      "Thread ID와 중단 Payload 확인",
      "Reviewer에게 필요한 Field 확인",
    ],
    labB: [
      "Approve·Edit·Reject로 각각 Resume",
      "Conditional Edge와 최종 상태 비교",
      "외부 저장·발송 없음 확인",
    ],
    codexPrompt: [
      "목표: 실제 interrupt·resume Human Review Graph",
      "허용: Graph 함수·해당 Test·Notebook 7차시",
      "Test: Interrupt 전 Export 없음·세 Decision·완료 Thread",
      "금지: 승인 전 외부 저장·발송·Thread ID 변경",
    ],
    notebookSnippet: `# Cell A · Interrupt
graph = build_interruptible_meeting_graph()
start = start_interruptible_meeting_review(
    graph, sources["google_meet_text"], domain_context,
    thread_id="day2-learner-review")
assert start["status"] == "WAITING_FOR_HUMAN_REVIEW"

# Cell B · 수강생 결정
REVIEW_DECISION = "edit"  # approve · edit · reject

# Cell C · 같은 thread_id로 Resume
resumed = resume_interruptible_meeting_review(
    graph, thread_id="day2-learner-review",
    decision=REVIEW_DECISION, edits=REVIEW_EDITS)
assert resumed["external_write"] is False`,
    success: "검토 전 Interrupt, 승인 후에만 Local Draft 생성",
    expectedError: "Unknown Evidence·Policy 위반은 Human Review 전 Hold",
    externalRule: "Approve·Edit 뒤에도 Local Draft만 생성",
    externalState: "external_write=false",
    recovery: [
      "Thread ID 확인",
      "Interrupt Payload 필수 Field 확인",
      "같은 Thread ID로 Resume",
      "Approve·Edit·Reject 최종 상태 비교",
    ],
    applications: [
      ["재직자", "메일·문서 반영 전 Reviewer 승인 Workflow"],
      ["구직자", "Interrupt·Checkpoint·Conditional Edge 구현"],
    ],
    completion: ["Interrupt 확인", "세 Decision 실행", "07 JSON 확인"],
    command: "python -m pytest -q tests/test_day2_meeting_workflow.py -k interruptible_human_review",
    demoCommand: "jupyter lab materials/day2/day2_service_lab.ipynb",
    saveLine: 'save_json("07_human_review.json", human_review_result)',
    image: "langgraph-interrupt-demo-local.png",
    fullScreenDemo: true,
    sources: ["https://docs.langchain.com/oss/python/langgraph/interrupts", "https://www.youtube.com/watch?v=6t7YJcEFUIY"],
  },
  {
    shortTitle: "Desktop App Package",
    label: "Desktop App",
    subtitle: "Source App · Local GUI · Docker · Windows EXE · macOS PKG",
    focusTitle: "일반 사용자용 실행 화면",
    conceptTitle: "Desktop App 패키지 용어",
    processTitle: "입력부터 Local Draft까지",
    decisionTitle: "실행 방식별 준비 조건",
    filesTitle: "Desktop App 파일 구조",
    demoTitle: "회의 기록 도우미 Demo",
    resultTitle: "Local App 결과",
    codexTitle: "Codex Task · App 통합 Test",
    labATitle: "Source App Smoke",
    labBTitle: "세 입력과 Local Draft",
    completionTitle: "8차시 완료 기준",
    phaseTimes: ["0-8분", "8-18분", "18-48분", "48-50분"],
    focus: "개발 환경을 모르는 사용자도 파일을 넣고 결과를 검토할 수 있는 로컬 GUI와 설치 패키지",
    setup: [
      "requirements-day2.txt 설치",
      "desktop-app/meeting-intelligence Source",
      "Browser · http://127.0.0.1:8766 또는 Python Smoke",
    ],
    optional: ["Ollama", "Codex·Claude Login", "Unsigned Package는 교육용"],
    terms: [
      ["Source Run", "Python으로 FastAPI App을 직접 실행하는 OS 공통 기본 경로"],
      ["Smoke Test", "Health·처리 API·안전 경계를 짧게 확인하는 실제 실행 검사"],
      ["Docker", "같은 실행 환경을 Container로 묶는 선택 경로"],
      ["Package", "사전 제작한 EXE·PKG Launcher; 수강생은 직접 Build하지 않아도 됨"],
    ],
    fileRoles: [
      ["가이드", "desktop-app/meeting-intelligence/README.md"],
      ["실행", "scripts/day2_desktop_smoke.py · app/main.py"],
      ["UI", "static/index.html · app.js"],
      ["Package", "Windows EXE · macOS PKG"],
    ],
    conceptFiles: [
      "README.md",
      "docker-compose.yml",
      "static/app.js",
      "dist/*.exe · dist/*.pkg",
    ],
    pipeline: ["파일 입력", "Domain Context", "Workflow", "Human Review", "Local Draft"],
    decisions: [
      ["Source Run", "OS 공통 기본", "Docker 없이 실제 API 검증"],
      ["Docker", "선택", "Image 준비 완료 PC에서 실행"],
      ["사전 제작 EXE·PKG", "Windows·macOS", "Checksum·OS 경고 확인"],
    ],
    demo: [
      "Source App Smoke와 Health Check",
      "Meet TXT·Domain Context 입력",
      "MeetingRecord·MD·Email Draft 확인",
    ],
    resultChecks: [
      "markdown_files · email_drafts",
      "email_send_allowed=false",
      "human_review_required",
      "external_write=false",
    ],
    mapCheck: "Local App 실행\nMD·Email Draft",
    labA: [
      "python scripts/day2_desktop_smoke.py 실행",
      "Health·Fixture API·Review Boundary 확인",
      "08_desktop_smoke.json PASS 확인",
    ],
    labB: [
      "Source App 또는 준비된 Package 실행",
      "Meet Fixture와 Domain Context 입력",
      "MeetingRecord·MD·Email Draft Preview 검증",
    ],
    codexPrompt: [
      "목표: API·UI·Docker의 동일 Schema와 Port",
      "허용: App API·UI·Docker·Launcher·해당 Test",
      "Test: 세 입력·Evidence ID·Human Review·Port 8766",
      "금지: 자동 메일·Notion·Confluence 반영",
    ],
    notebookSnippet: `desktop_delivery = {
    "source_smoke": "python scripts/day2_desktop_smoke.py",
    "docker_optional": "docker compose up --build",
    "browser": "http://127.0.0.1:8766",
    "human_review_required": True,
    "external_write": False,
}
export_result = {
    "markdown_files": markdown_files,
    "email_drafts": email_drafts,
    "desktop_delivery": desktop_delivery,
    "checks": {"all_emails_unsent":
        all(not item["send"] for item in email_drafts.values())},
}`,
    success: "세 입력 중 하나로 MeetingRecord·MD·Email Draft 생성",
    expectedError: "로그인 안 됨·STT 실패·미승인 요청은 Hold와 복구 안내",
    externalRule: "Notion·Confluence·Email은 연결 계획만 생성",
    externalState: "PLAN_ONLY",
    recovery: [
      "Docker 실행 상태 확인",
      "127.0.0.1:8766 Health 확인",
      "Provider 준비 상태 확인",
      "Fixture Mode로 재실행",
    ],
    applications: [
      ["재직자", "팀원이 설치해 쓰는 로컬 회의 기록 도구"],
      ["구직자", "Source·Docker·Package·Test가 있는 Portfolio"],
    ],
    completion: ["Source Smoke PASS", "세 입력 중 하나 처리", "Draft Preview와 Test 확인"],
    command: "python scripts/day2_desktop_smoke.py",
    demoCommand: "python scripts/day2_desktop_smoke.py\ncd desktop-app/meeting-intelligence && python -m uvicorn app.main:app --host 127.0.0.1 --port 8766",
    saveLine: 'save_json("08_export_drafts.json", export_result)',
    image: "meeting-intelligence-desktop-local.png",
    fullScreenDemo: true,
    sources: ["local:desktop-app/meeting-intelligence/README.md"],
  },
];

export const DAY2_STUDENT_PERIODS = BASE.map((period, index) => ({
  ...period,
  ...DETAILS[index],
  classNumber: index + 1,
  time: DAY_TIMES[index][0],
}));

export const DAY2_GLOBAL = {
  title: "회의 기록 Agent 제작",
  subtitle: "세 입력 · 원문 근거 · Human Review · Local App",
  service: "Well-being Meeting Record",
  scheduleMorning: [
    ...DAY2_STUDENT_PERIODS.slice(0, 3).map((period) => [
      period.time,
      `${period.classNumber}차시`,
      period.shortTitle,
      period.artifact,
    ]),
    ["11:30-13:00", "Break · Lunch", "오전 결과 저장 · 점심시간", "12:55 복귀"],
  ],
  scheduleAfternoon: [
    ...DAY2_STUDENT_PERIODS.slice(3, 5).map((period) => [
      period.time,
      `${period.classNumber}차시`,
      period.shortTitle,
      period.artifact,
    ]),
    ["14:40-15:00", "Break", "Notebook · 결과 파일 저장", "15:00 재개"],
    ...DAY2_STUDENT_PERIODS.slice(5).map((period) => [
      period.time,
      `${period.classNumber}차시`,
      period.shortTitle,
      period.artifact,
    ]),
    ["17:30-18:00", "Q&A", "실습 복구 · 질문", "Error 첫 줄 · 기대 결과"],
  ],
  requiredSetup: [
    ["Clone", "git clone <repository URL>\ncd llm-agent-and-workflow-automation", "최초 1회"],
    ["macOS", "python3.12 -m venv .venv312\nsource .venv312/bin/activate", "환경 생성"],
    ["Windows", "py -3.12 -m venv .venv312\n.venv312\\Scripts\\Activate.ps1", "환경 생성"],
    ["Install", "python -m pip install -r requirements-day2.txt\npython -m ipykernel install --user --name ipa-day2", "Notebook·App"],
    ["Preflight", "python scripts/run_day2_preflight.py --full-suite", "수업 전 PASS"],
  ],
  optionalSetup: [
    ["Audio", "ffmpeg · ffprobe · faster-whisper", "2차시 Live STT"],
    ["Ollama", "ollama pull qwen3:4b", "6차시 무료 Local LLM"],
    ["Coding Agent", "Codex ChatGPT Login · Claude Code /login", "5차시 Patch·Review"],
    ["확장", "Docker Desktop · OpenAI API + 명시적 Opt-in", "8차시·선택 Live"],
  ],
  references: [
    ["Codex CLI", "https://developers.openai.com/codex/cli"],
    ["LangGraph Interrupt", "https://docs.langchain.com/oss/python/langgraph/interrupts"],
    ["LangGraph Video · Interrupt 08:20-14:00", "https://www.youtube.com/watch?v=6t7YJcEFUIY"],
    ["MCP", "https://modelcontextprotocol.io/introduction"],
    ["공개 음성", "materials/day2/공개_한국어_회의음성_가이드.md"],
  ],
};
