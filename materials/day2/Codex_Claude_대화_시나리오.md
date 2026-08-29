# Codex·Claude 대화 시나리오 · 회의기록 Agent

## 사용 원칙

이 문서는 ChatGPT/Codex와 Claude/Claude Code를 통해 회의기록 서비스를 설계·구현·검증할 때 복사해 쓰는 대화 예시다. 실제 고객·회사 회의, API key, 접속 token을 대화창에 붙여 넣지 않는다.

모델의 숨은 chain-of-thought를 요청하는 대신, 검토 가능한 `선택지 → 선택 기준 → 선택 결과 → 근거 → 중단 조건`을 요청한다.

---

## 1. 모델·환경 진단 대화

### 사용자

> 이 작업은 복잡한 아키텍처와 코드 리뷰가 필요합니다. 현재 환경에서 선택된 모델과 reasoning effort를 알려 주고, `GPT-5.6 Sol + ultra`가 실제 선택지에 있는 경우만 사용해 주세요. 없다면 현재 가용한 최상위 코딩/추론 모델을 쓰되, 실제 모델명을 결과에 남겨 주세요. API 실행은 별도로 `gpt-5.6-luna`의 project 가용성을 작은 진단 호출로 먼저 확인하고, 접근할 수 없으면 실패 이유를 숨기지 말아 주세요.

### 기대 응답

- 설계/코드 모델과 API runtime 모델을 구분한다.
- “ultra”를 API 모델 ID로 임의 번역하지 않는다.
- requested model, used model, fallback reason을 따로 기록한다.

---

## 2. 단계적 대화 · 사용자부터 설계

### 1단계 · 사용자 상황

> 코드를 모르는 사람에게 한국어 회의기록 서비스를 선물하려고 합니다. 사용자에게는 세 상황이 있습니다. (1) Google Meet 전사와 참석자 이력, (2) ClovaNote에서 내보낸 TXT, (3) 녹음 파일만 있는 경우입니다. 코드를 쓰지 말고 먼저 각 사용자의 시작·성공·실패·복구 흐름을 표로 정의해 주세요.

### 2단계 · 아키텍처

> 방금 사용자 흐름을 기준으로 `입력 adapter → 공통 transcript contract → domain context → 선택적 retrieval → 요약/관점/To-do/인사이트 → 근거 검증 → 사람 승인 → MD/email draft`를 가장 작은 컴포넌트로 나누어 주세요. LLM, 고정 workflow, agent가 담당할 부분을 구분하고, 여기서 agent가 불필요한 부분도 명시해 주세요.

### 3단계 · 정책

> 정책을 추가합니다. 외부 write는 기본 금지입니다. Notion·Confluence·Slack·email MCP는 필요성을 먼저 설명하고 사람의 조회 승인을 받은 뒤, read-only·최근 14일·지정 공간·최대 5개·출처 필수로만 쓸 수 있습니다. 민감정보를 제외하고, 실제 게시·발송은 2차 승인 없이 실행하지 마세요.

### 4단계 · 현재 코드 진단

> 이제 저장소를 읽어 주세요. 작성은 하지 말고, 관련 파일·진입점·테스트·fixture·외부 write 경계를 표로 보고해 주세요. ‘이미 됨’, ‘부분 지원’, ‘미구현’을 구분하고, 실제 코드로 확인하지 못한 것은 추측으로 표시해 주세요.

### 5단계 · 첫 vertical slice

> 첫 변경은 Google Meet text 하나만 받아 `TranscriptEnvelope`로 바꾸고 fixture `MeetingRecord`를 만든 뒤 evidence ID를 검증하는 최소 vertical slice로 제한합니다. 정상 테스트와 없는 evidence ID 실패 테스트를 함께 작성하고 실행해 주세요. 외부 연결은 추가하지 마세요.

### 6단계 · 세 시나리오

> 첫 slice의 contract를 바꾸지 말고 ClovaNote TXT와 audio+STT adapter를 추가해 주세요. source는 exactly one이어야 합니다. Meet/Clova text는 STT를 건너뛰고, audio live STT 실패를 다른 fixture transcript로 위장하지 마세요. 정상 3개와 source 0개/2개, 빈 STT, 화자 미식별 테스트를 실행해 주세요.

### 7단계 · LangGraph와 출력

> 정책 → 정규화 → 선택 STT → 구조화 → 근거 검증 → 승인/수정/거절 → draft를 LangGraph state로 표현해 주세요. 승인 전에는 MD/email draft를 만들지 마세요. 승인 후에도 Notion/Confluence/email에 실제로 쓰지 말고 `integration_plan` 미리보기만 만들어 주세요.

---

## 3. 한 번에 넘기는 Harness Prompt

```text
목표
코드를 모르는 일반 사용자가 쓸 수 있는 한국어 Well-being 회의기록 서비스를 만든다.

사용자 시나리오
1. Google Meet 전사 + 참석자 정보
2. ClovaNote TXT
3. 녹음 파일 + local STT

공통 결과
회의 목적, 기존 맥락, 요약, 결정, 구성원별 확인된 관점, owner/due/evidence가 있는 To-do, 단기/중기/장기 인사이트, well-being risk를 구조화한다. 내면을 추측하지 말고 원문에 없는 담당자·기한을 만들지 마라.

아키텍처
세 input adapter가 하나의 TranscriptEnvelope로 수렴해야 한다. 고정 순서는 workflow로, 맥락에 따른 검색·도구 선택만 bounded agent로 두어라. 신뢰 경계는 일반 Python validator와 LangGraph human gate가 담당한다.

Retrieval/MCP 정책
필요성을 먼저 판단하고, 사람의 조회 승인 후 read-only·지정 공간·최근 14일·최대 5개·출처 필수로만 조회한다. 민감정보를 제외한다.

안전 경계
- source는 exactly one
- text input은 STT skip
- audio live STT 실패를 fixture로 위장하지 않음
- 모든 주요 결론에 실제 segment evidence ID
- 승인/수정/거절
- external_write=false
- MD/email draft와 Notion/Confluence/email integration plan만 생성
- 비밀·credential·실제 회의 데이터를 읽거나 출력하지 않음

Provider
Run All은 fixture로 완주해야 한다. 선택적으로 Ollama, 공식 Codex/Claude CLI, OpenAI API를 쓸 수 있다. API는 OPENAI_MODEL=gpt-5.6-luna를 요청하되 project 가용성을 먼저 진단한다. requested/used/model/fallback reason을 반드시 남긴다.

작업 방법
1. 작성 전 현재 파일·test·더티 worktree를 읽어라.
2. 작은 vertical slice로 구현하고 매 slice마다 정상·경계 test를 추가하라.
3. 기존 사용자 변경을 덮어쓰지 마라.
4. 에러를 raw traceback으로 끝내지 말고 stable error code로 반환하라.
5. 끝나면 실행 명령, 테스트 결과, 남은 Gap을 솔직히 보고하라.
```

---

## 4. 실패 복구 대화

### API가 fixture로 바뀐 경우

> `provider_requested=openai`인데 `provider_used=fixture`로 끝났습니다. 마지막 오류 한 줄만 고치지 말고, (1) live opt-in 조건, (2) API key load 경로, (3) model project 권한, (4) provider fallback 정책을 순서대로 점검해 주세요. 비밀 값은 출력하지 말고, 재현 명령과 확인된 오류 코드만 보여 주세요. fallback을 끄면 어떤 HOLD가 되는지도 테스트해 주세요.

### STT 실패가 숨겨진 경우

> 업로드한 audio와 결과 transcript가 같은 쌍인지 확인해 주세요. live STT 실패 후 합성 fixture transcript를 성공으로 보여 주는 경로가 있다면 제거하고 `LIVE_STT_FAILED` HOLD로 끝내 주세요. fixture mode는 “업로드한 음성을 전사하지 않음”을 화면과 JSON에 모두 표시해 주세요.

### 없는 근거가 통과한 경우

> `s999`가 transcript에 없는데 승인 단계에 도달했습니다. LLM prompt를 먼저 바꾸지 말고 evidence validator의 known ID 집합, 검증 순서, LangGraph conditional edge를 점검해 주세요. 정상·빈 evidence·unknown evidence 세 테스트를 추가하고 가장 작은 수정만 적용해 주세요.

### MCP가 연결되지 않은 경우

> 실제 조직 MCP 연결을 추가하지 말고, 현재 환경에서 사용 가능한 connector를 진단해 주세요. 없다면 read-only simulated `integration_plan`으로 복귀하고, 실제 조회를 했다고 표시하지 마세요. 필요 권한·범위·기간·출처·승인 지점만 결과로 남겨 주세요.

---

## 5. ChatGPT/Claude 프로젝트에서 회의 하나를 처리하는 요청

```text
이 프로젝트는 한국어 회의기록 초안을 만듭니다.

1. 입력이 Google Meet/ClovaNote text면 STT를 요청하지 마세요.
2. audio면 녹음 동의를 먼저 묻고, 현재 환경의 STT 기능을 진단한 뒤 가능한 경우만 전사하세요.
3. 도메인, 회의 목적, 기존 맥락, 용어집, 제약, 독자, 문체를 먼저 확인하세요.
4. 외부 정보가 정말 필요한지 판단하세요. 필요하다면 조회할 서비스, 공간, 최근 기간, 검색어, 최대 결과 수를 제안하고 승인을 기다리세요.
5. 회의 목적·기존 맥락·요약·결정·구성원별 확인된 관점·To-do·단중장기 인사이트·well-being 확인 항목을 작성하세요.
6. 각 주요 항목에 원문 발화를 출처로 붙이세요. 없는 담당자·기한·의도를 만들지 마세요.
7. Markdown과 이메일 초안을 미리보기하되 실제 게시·발송하지 마세요.

입력 유형: [google_meet_text | clovanote_txt | audio]
도메인:
회의 목적:
기존 맥락:
용어집:
제약:
독자:
문체:
원하는 결과:
```

이 대화 경로는 한 번의 업무 초안에 적합하다. 매번 같은 Schema·근거 검증·승인·복구가 필요하다면 Notebook과 local App Workflow로 옮긴다.

---

## 6. 대화 결과 검증

대화가 그럴듯하다고 완료로 보지 않는다.

- 사용자 세 상황이 모두 다루어졌는가?
- text 입력에 불필요한 STT를 하지 않는가?
- LLM·Workflow·Agent의 역할이 구분되었는가?
- Agent의 tool call·기간·결과 수에 제한이 있는가?
- 원문에 없는 담당자·기한·의도를 만들지 않았는가?
- 근거를 실제 source로 돌아가 확인할 수 있는가?
- 승인 전 외부 write가 없는가?
- 실제로 쓴 provider·model·fallback이 기록되었는가?
- 정상·가장 중요한 실패 테스트가 모두 통과했는가?
