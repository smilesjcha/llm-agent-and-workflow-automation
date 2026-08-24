# Day 2~5 · Codex·Claude Code 제작 사례와 오프닝 Demo 런북

## 결론

2~5일차가 각각 8시간인 이유는 한 기능을 네 번 설명하기 때문이 아니다. 매일 하나의 서비스를 `입력 계약 → 핵심 처리 → 실패 경계 → 사람 판단 → 평가 → 실행 증거`까지 완성하고, 다음 날에는 전날 결과를 다른 문제로 확장하기 때문이다.

장표는 설명의 양을 늘리는 용도가 아니다. 강의 중 계속 띄워 둘 입력·코드·명령·결과·오류 복구 화면을 작은 단위로 분리한다. 한 차시 30장 중 강사가 새 개념으로 설명하는 장표는 약 7~8장이고, 나머지는 Demo와 소프트웨어 제작을 따라가는 화면이다.

| 50분 | 기본 시간 | 장표 역할 | 중복 방지 기준 |
|---|---:|---:|---|
| 개념 강의 | 12분 | 7~8장 | 그 차시에 처음 나오는 문제·용어·판단만 설명 |
| 강사 Demo | 10분 | 5~6장 | 완성 결과→입력→명령→정상·실패 결과 |
| 소프트웨어 제작 | 23분 | 12~14장 | Notebook 셀·VS Code 파일·Codex task·test 증거 |
| 실행 확인 | 5분 | 2~4장 | 생성 파일·stable error·다음 차시 입력 |

같은 정의를 뒤에서 다시 요약하지 않는다. 앞 차시의 출력이 다음 차시의 입력으로 재등장할 때는 복습이 아니라 실제 interface로 사용한다.

## 시작 5분 · 결과 먼저 보기

각 일차 첫 화면에서는 45초 teaser를 자동 재생한다. 네 장면은 실제 현재 코드가 만든 JSON과 local browser Demo를 캡처한 것이다.

| 일차 | Teaser | 보여줄 장면 | 시작 질문 |
|---|---|---|---|
| Day 2 | `assets/demo-videos/day2_service_teaser.gif` | 회의 Agent→처리 단계→수치→unknown evidence HOLD | “12분 회의를 몇 분 안에 근거가 있는 업무 데이터로 만들 수 있을까?” |
| Day 3 | `assets/demo-videos/day3_service_teaser.gif` | 리뷰 Agent→diff 처리→F1→empty diff failure | “그럴듯한 코멘트와 merge에 쓸 수 있는 리뷰의 차이는 무엇일까?” |
| Day 4 | `assets/demo-videos/day4_service_teaser.gif` | PR target→dry-run→사람 승인→중복 실행 방지 | “Agent에게 GitHub 쓰기 권한을 언제 열어도 될까?” |
| Day 5 | `assets/demo-videos/day5_service_teaser.gif` | 두 서비스 router→trace→eval→release HOLD | “Demo가 작동한다는 사실과 운영 가능한 상태는 어떻게 구분할까?” |

강사는 teaser가 끝난 뒤 기능을 설명하지 않는다. “오늘 8차시에 이 화면을 현재 저장소에서 다시 만들겠습니다”라고 말한 뒤 1차시 입력 계약으로 바로 이동한다.

### 재생·복구

```bash
open assets/demo-videos/day2_service_teaser.gif
cd web-demo
npm run build
python3 -m http.server 4173 --directory dist
```

브라우저 직접 확인 주소:

```text
http://127.0.0.1:4173/course.html?day=2
http://127.0.0.1:4173/course.html?day=3
http://127.0.0.1:4173/course.html?day=4
http://127.0.0.1:4173/course.html?day=5
```

GIF가 재생되지 않으면 `dayN_overview.png`, `dayN_pipeline.png`, `dayN_result.png`, `dayN_boundary.png`를 순서대로 넘긴다. 영상과 장표가 다른 결과를 보여 주지 않도록 두 형식 모두 같은 `output/course-demos/dayN/demo_result.json`을 원본으로 쓴다.

## Day 2 · 한국어 회의 Agent

### 8시간이 필요한 논리

STT 호출 한 줄만으로는 회의 서비스가 되지 않는다. 음성 파일이 정상인지, 전사 품질이 업무에 충분한지, 긴 회의에서 근거 ID가 보존되는지, LLM 결과가 schema와 정책을 지키는지, 근거 없는 Action Item을 어떻게 멈출지까지 서로 다른 실패 지점이 있다.

| 차시 | 새 질문 | 제작 대상 | 다음 차시로 넘기는 interface |
|---|---|---|---|
| 1차시 | 입력 파일 자체를 믿어도 되는가 | audio metadata validator | `audio_metadata` |
| 2차시 | provider가 바뀌어도 segment 형식은 같은가 | STT adapter | `segments[{id,start,end,text}]` |
| 3차시 | 문자 생성과 업무 사용 가능을 어떻게 나누는가 | STT quality gate | `READY/HOLD` |
| 4차시 | LLM 출력의 필수 field는 무엇인가 | `MeetingBrief` contract | typed brief |
| 5차시 | 긴 회의에서 근거를 잃지 않는가 | evidence-preserving chunk | chunks+segment IDs |
| 6차시 | fixture·Ollama·OpenAI를 어떻게 교체하는가 | LangChain adapter pipeline | same schema+policy |
| 7차시 | 존재하지 않는 근거를 어떻게 막는가 | evidence validator | errors or validated brief |
| 8차시 | 이 서비스를 다시 배포해도 되는가 | scorecard+focused test | `READY/HOLD` |

### 수강생이 끝날 때 가진 것

- 실행 Notebook: `materials/day2/day2_service_lab.ipynb`
- 실행 증거: `materials/day2/day2_service_lab.executed.ipynb`
- 결과 폴더: `output/course-labs/day2/01_audio_metadata.json`부터 `08_day2_scorecard.json`
- 서비스 Demo: `output/course-demos/day2/demo_result.json`
- 정상 수치: 45 segments, 7 chunks, 5 Action Items, evidence error 0
- 실패 수치: `ACTION_1_UNKNOWN_EVIDENCE:s999` → `HOLD`

### Codex Desktop 작업 대화 예시

아래 문구는 복사 가능한 강사 시연 대본이다. ChatGPT Desktop의 Codex에서 저장소를 연 뒤 한 번에 한 책임만 요청한다.

```text
목표: Action Item의 evidence_ids가 실제 transcript segment에 있는지 검사하는 함수를 추가해줘.
허용 경로: src/course_services/meeting_service.py, tests/test_course_services.py
정상 조건: 존재하는 s12, s18은 오류가 없어야 함.
실패 조건: s999는 ACTION_1_UNKNOWN_EVIDENCE:s999로 반환해야 함.
금지: broad exception, raw traceback contract, 자동 메일, workspace 밖 파일 접근.
완료 전 실행: python -m pytest -q tests/test_course_services.py
마지막에 diff와 test 결과를 분리해서 보고해줘.
```

Codex가 구현하면 강사는 함수보다 먼저 test 이름, 오류 code, 변경 path를 확인한다. “통과했다”는 문장 대신 실제 명령과 return code를 확인한다.

### Claude Code 독립 리뷰 예시

Claude Desktop의 Code tab에서 같은 저장소의 별도 isolated session을 연다. Codex와 같은 working tree를 동시에 수정하지 않는다.

```text
변경 내용을 구현하지 말고 리뷰만 해줘.
AGENTS.md의 workspace path, stable error contract, normal+boundary test 기준을 적용해줘.
action evidence validator 변경 라인에서 실제 사용자 영향이 있는 finding만 보고해줘.
각 finding은 severity, path, line, reproduction, smallest safe correction을 포함해줘.
style-only 의견은 제외해줘.
```

Claude Code 결과도 자동 승인으로 쓰지 않는다. Codex diff, Claude finding, test는 사람 merge 판단의 세 가지 입력이다.

## Day 3 · 코드 리뷰 Agent

### 8시간이 필요한 논리

코드 리뷰는 LLM에게 diff를 붙이고 “검토해 줘”라고 말하는 일이 아니다. 변경 줄 복원, 저장소 규칙 선택, finding contract, 재현 가능한 baseline, test 증거, LLM 의견의 위치, offline evaluation, Codex 작업 통제가 각각 다른 품질 문제다.

| 차시 | 새 질문 | 제작 대상 | 누적 결과 |
|---|---|---|---|
| 1차시 | 좋은 finding의 필수 요소는 무엇인가 | review rubric | 9 fields+severity |
| 2차시 | 실제 추가 줄 번호를 어떻게 찾는가 | unified diff parser | added line mapping |
| 3차시 | 모델에게 무엇만 보여줄 것인가 | context pack | changed path+focus |
| 4차시 | review 결과를 어떻게 검증할 것인가 | `ReviewReport` contract | typed findings |
| 5차시 | LLM 없이 무엇을 재현할 수 있는가 | deterministic rules | 3 findings |
| 6차시 | static·test·LLM을 어떻게 결합할까 | hybrid report | evidence layers |
| 7차시 | review 품질을 어떻게 수치화할까 | precision·recall·F1 | release gate |
| 8차시 | Codex 변경을 어떻게 통제할까 | task spec+merge gate | READY/HOLD |

### 실제 제작 결과

- Notebook 결과 8개: `output/course-labs/day3/`
- 의도적 위험 diff: `data/day3_review_cases/unsafe_pr.diff`
- 실제 finding 3개, precision 1.0, recall 1.0, F1 1.0
- boundary: 빈 diff → `EMPTY_DIFF`
- Codex task spec 정상 판단 → `READY_FOR_HUMAN_MERGE`
- `.env`·secret·미실행 test 조건 → `HOLD`

### Codex 구현 시연

```text
목표: GitHub HTTP 응답을 status별 stable recovery contract로 분류하는 순수 함수를 추가해줘.
허용 경로: src/course_services/github_service.py, tests/test_course_services.py
정상 조건: 200은 SUCCESS.
실패 조건: 401/403/404/422/500은 retryable=false, 429만 retryable=true.
금지: 실제 GitHub 호출, token 출력, 무제한 retry.
test: python -m pytest -q tests/test_course_services.py
```

이 저장소에는 위 사례가 `classify_github_response()`와 normal/boundary test로 반영되어 있다. 3일차에는 요구 계약과 review를 만들고, 4일차에는 실제 workflow adapter에서 사용한다.

## Day 4 · GitHub·LangGraph 승인 Workflow

### 8시간이 필요한 논리

GitHub 자동화의 어려움은 comment body 생성이 아니다. 정확한 PR·SHA 식별, secret과 최소 권한, status별 복구, state 분기, checkpoint와 중복 방지, 사람 승인, dry-run, live 게시 전 audit가 모두 외부 상태를 보호한다.

| 차시 | 새 질문 | 제작 대상 | 안전 경계 |
|---|---|---|---|
| 1차시 | 어느 PR에 쓰는가 | target validator | repo·number·SHA |
| 2차시 | token을 어떻게 다루는가 | auth status | 값 미출력 |
| 3차시 | 어떤 오류를 재시도하는가 | response contract | 429만 retry |
| 4차시 | 승인·수정·거절을 어떻게 모델링하는가 | LangGraph state | terminal states |
| 5차시 | 같은 요청을 두 번 보내면 어떻게 되는가 | idempotency store | publisher 1회 |
| 6차시 | 누가 외부 쓰기를 결정하는가 | human decision | rejection BLOCKED |
| 7차시 | 게시 전 무엇을 볼 수 있는가 | dry-run plan | publisher 미호출 |
| 8차시 | live 게시 조건은 무엇인가 | sandbox audit | C 선택 경로 |

### 실제 제작 결과

- fake publisher call count 1
- duplicate request `reused=true`
- 사람 거절 → `HUMAN_APPROVAL_REQUIRED`
- 수업 기본 결과의 `external_write=false`
- 실제 GitHub 게시가 없어도 payload·target·hash·approval·audit를 모두 검증

### 강사 시연 순서

1. `04_graph_states.json`의 approve·edit·reject terminal state를 40초에 비교한다.
2. `05_idempotency.json`에서 같은 요청 두 번과 publisher 한 번을 보여준다.
3. `06_review_decision.json`에서 reject가 외부 쓰기 없이 끝나는지 확인한다.
4. `07_review_comment_plan.json`에서 실제 API와 같은 body를 dry-run으로 확인한다.
5. live GitHub는 필수 성과가 아니라 강사 소유 sandbox에서만 선택한다.

## Day 5 · Agent Operations Console

### 8시간이 필요한 논리

Demo가 한 번 성공한 상태와 운영 가능한 상태 사이에는 router, trace, monitoring view, dataset comparison, human feedback, PII·retention, release packaging, final scorecard가 필요하다. 각 항목은 서로 다른 운영 질문에 답한다.

| 차시 | 새 질문 | 제작 대상 | 운영 판단 |
|---|---|---|---|
| 1차시 | 어느 서비스를 호출할까 | explicit router | unknown kind 차단 |
| 2차시 | 어디에서 느리거나 실패했나 | local trace | span status·latency |
| 3차시 | 무엇으로 필터링할까 | monitoring view | provider·fallback·decision |
| 4차시 | 새 버전이 더 좋은가 | dataset experiment | precision·recall·latency |
| 5차시 | 사람의 수정을 어떻게 학습 자산으로 남기나 | structured feedback | approve·edit·reject reason |
| 6차시 | trace에 무엇을 올리면 안 되나 | redaction+retention | raw content 차단 |
| 7차시 | Python 결과와 UI가 같은가 | local web build | same demo JSON |
| 8차시 | 배포할 것인가 | release scorecard | READY/HOLD |

### 실제 제작 결과

- meeting·review service 2개를 explicit router로 실행
- local trace span 3개
- review precision·recall·F1 1.0
- 낮은 recall·precision, safety failure, latency 초과 → `HOLD`
- `test@example.com`, 전화번호, token 형태 redaction
- `web-demo/dist/course.html`과 Day 2~5 actual JSON build

### Codex 기반 UI 연결 시연

```text
목표: output/course-demos/day2~5/demo_result.json을 읽는 정적 결과 화면을 추가해줘.
허용 경로: web-demo/course.html, web-demo/course.js, web-demo/course.css, web-demo/build.mjs
정상 조건: ?day=2~5가 각각 title, stage, metric, boundary를 렌더링.
실패 조건: JSON 404는 Demo data error 화면.
금지: API key, 고객 데이터, 실제 외부 쓰기.
검증: npm run check && npm run build
디자인: black/white, navy 보조, 짧은 제목, 실제 결과 JSON을 크게.
```

현재 결과 화면과 16개 캡처는 이 task contract의 실행 결과다. PPT의 opening slide는 실제 화면 캡처를 사용하며, 추상적인 AI 이미지를 사용하지 않는다.

## ChatGPT Desktop·Codex와 Claude Desktop·Claude Code의 역할

| 역할 | ChatGPT Desktop with Codex | Claude Desktop with Claude Code | 공통 Harness |
|---|---|---|---|
| 저장소 시작 | 관련 파일·test·정책 탐색 | 별도 isolated session에서 독립 해석 | 목표·허용 path·금지 행동 |
| 구현 | 작은 책임의 코드·test·문서 수정 | 선택적 대안 구현 또는 review-only | normal+boundary test |
| 검토 | changed lines·test 결과 요약 | 반대 관점 finding과 누락 검사 | severity·impact·reproduction |
| 완료 | diff·test·artifact path 보고 | independent review report | 사람 merge·publish 결정 |

ChatGPT와 Codex의 공식 학습 자료는 ChatGPT를 ideation·작업 보조에, Codex를 codebase 이해·구현·test·review·배포에 연결한다. Claude Code Desktop 공식 문서는 Local session, project와 permission mode, Git isolation을 이용한 parallel session, terminal·file editor·visual diff·app preview·PR monitoring을 설명한다. 수업에서는 제품마다 다른 UI보다 `spec → small diff → test → independent review → human decision`이라는 동일한 Harness를 가르친다.

- OpenAI Academy: <https://learn.chatgpt.com/>
- OpenAI use cases: <https://learn.chatgpt.com/use-cases>
- Claude Code Desktop: <https://code.claude.com/docs/en/desktop>
- Claude Code Desktop quickstart: <https://code.claude.com/docs/en/desktop-quickstart>

## 강의 전 강사 체크

```bash
.venv312/bin/python scripts/build_days2_5_notebooks.py

for day in 2 3 4 5; do
  .venv312/bin/jupyter nbconvert \
    --to notebook --execute "materials/day${day}/day${day}_service_lab.ipynb" \
    --output "day${day}_service_lab.executed.ipynb" \
    --output-dir "materials/day${day}" \
    --ExecutePreprocessor.timeout=420
done

cd web-demo
npm run check
npm run build
```

최종적으로 확인할 것은 장표 수가 아니다.

1. teaser의 수치와 현재 JSON이 같은가.
2. 8개 차시가 서로 다른 질문을 해결하는가.
3. 앞 차시 출력이 다음 차시 입력으로 실제 사용되는가.
4. 모든 Notebook이 `Run All`로 오류 없이 끝나는가.
5. 정상 경로뿐 아니라 대표 실패가 stable error 또는 HOLD로 남는가.
6. Codex·Claude Code 결과가 test와 diff 없이 자동 승인되지 않는가.
7. 실제 외부 쓰기·게시·배포는 사람이 결정하는가.
