# Day 2-5 · Codex 기반 서비스 운영 블루프린트

## 1. 남은 32시간의 한 줄 구조

Day 2에서 한국어 회의 음성을 구조화하고, Day 3에서 코드 변경을 검토하며, Day 4에서 GitHub 외부 쓰기를 사람 승인으로 보호하고, Day 5에서 두 서비스를 라우팅·관측·평가·배포한다.

```text
Day 2 Well-being Meeting Record
  Meet/Clova/audio → TranscriptEnvelope → domain context → MeetingRecord → evidence → human review → drafts

Day 3 Review Intelligence
  unified diff → line mapping → context pack → finding → static/test evidence → evaluation

Day 4 PR Review Automation
  PR fixture/read API → LangGraph → interrupt → dry-run → approval → idempotent publish

Day 5 Agent Operations Console
  explicit router → local/LangSmith trace → dataset eval → feedback → release gate → demo
```

각 일차 8시간의 상세 논리, 결과 먼저 보여 주는 45초 teaser, Codex 구현 대화와 Claude Code 독립 리뷰 방식은 `Codex_Claude_제작_사례와_오프닝_데모_런북.md`를 따른다.

## 2. Codex를 쓰는 위치

Codex는 모든 코드를 한 번에 생성하는 도구로 쓰지 않는다. 한 번의 요청은 한 가지 책임과 검증 가능한 완료 조건만 가진다.

| 단계 | Codex에게 맡길 일 | 사람이 확인할 일 |
|---|---|---|
| 저장소 이해 | 관련 파일·test·정책 문서 찾기 | context에 secret·무관한 output이 없는지 |
| 구현 | 허용 path 안에서 최소 diff 생성 | 기능 경계와 naming이 과정 의도와 맞는지 |
| test | 정상 case와 가장 중요한 실패 case 작성·실행 | 기존 policy나 assertion을 약화하지 않았는지 |
| 리뷰 | 변경 라인·사용자 영향·재현 조건 중심 finding | merge 여부와 product trade-off |
| 문서 | 실행 명령·결과 contract·복구 경로 갱신 | 처음 보는 수강생이 재현할 수 있는지 |
| 운영 | 반복되는 점검을 skill·script로 고정 | 외부 쓰기·데이터 보존·배포 승인 |

공식 Codex use case에서 이 과정과 직접 연결되는 항목은 큰 저장소 이해, bug triage, 앱 QA, 반복 workflow의 skill화, 보안 변경 검토, 평가 추가, GitHub PR 리뷰, 배포, 문서 갱신이다. 수업에서는 이를 하나의 큰 demo가 아니라 매 차시의 `spec → diff → test → review → human decision` 루프로 분해한다.

## 3. 표준 하루 운영 시간

| 시간 | 구분 | 운영 |
|---|---|---|
| 09:00-09:50 | 1차시 | 강의 12분 · 강사 시연 10분 · Codex 소프트웨어 제작 23분 · 확인 5분 |
| 09:50-10:40 | 2차시 | 같은 구성으로 앞 차시 결과를 이어서 실행 |
| 10:40-11:30 | 3차시 | 오전 통합 결과 저장 |
| 11:30-13:00 | 쉬는 시간·점심시간 | 오전 3개 차시 종료 후 휴식과 점심을 연속 운영 |
| 13:00-13:50 | 4차시 | schema·state·평가 등 두 번째 구현 구간 시작 |
| 13:50-14:40 | 5차시 | software contract 확장과 결과 저장 |
| 14:40-15:00 | 쉬는 시간 | 2개 차시 연강 후 20분 휴식 |
| 15:00-15:50 | 6차시 | 실제 provider·Graph·관측 연결 |
| 15:50-16:40 | 7차시 | 사람 승인·평가·운영 gate 구현 |
| 16:40-17:30 | 8차시 | 차시 통합, focused/full test, 결과 저장 |
| 17:30-18:00 | 쉬는 시간·Q&A | 마지막 3개 차시 종료 후 휴식·질문·미완료 실행 복구 |

자료 탐색·문제 정의·사례 비교는 `자료 수집`, `Ideation`, `설계`로 표현한다. IDE·Notebook·Terminal·Codex에서 실제 코드를 생성·수정·실행하고 결과 파일 또는 test 증거를 남길 때만 `소프트웨어 실습`으로 표현한다. 홈페이지·공식 문서 확인은 `참고 화면` 또는 `자료 확인`으로만 분류한다.

## 4. Day 2 · Well-being Meeting Record

### 강사가 먼저 보여줄 전체 흐름

1. 완성된 Desktop 화면에서 Google Meet TXT를 넣고 회의록·근거·외부 연결 계획을 먼저 보여 준다.
2. Google Meet 전사, ClovaNote TXT, 녹음 파일 중 하나를 받아 공통 `TranscriptEnvelope`로 바꾼다.
3. 텍스트 입력은 STT를 건너뛰고, 녹음 파일만 local `faster-whisper`를 거친다.
4. 산업 용어·이전 결정과 read-only MCP retrieval policy를 입력한다.
5. 단일 LLM·고정 Workflow·bounded Agent의 선택 기준과 비용을 비교한다.
6. 목적·참석자 관점·To-do·단중장기 인사이트가 있는 `MeetingRecord`를 만들고 evidence를 검증한다.
7. LangGraph에서 approve·edit·reject·HOLD를 실행한다.
8. 승인된 결과를 Markdown·email draft·Notion/Confluence/email `PLAN_ONLY`로 만들고 외부 쓰기 없이 끝낸다.

### 수강생 실행 파일

- Notebook: `materials/day2/day2_service_lab.ipynb`
- 핵심 코드: `src/course_services/day2_meeting_workflow.py`, `desktop-app/meeting-intelligence/app/`
- 입력: `desktop-app/meeting-intelligence/fixtures/`와 `data/day2_public_audio/meeting_ko_ccby_excerpt_10m.mp3`
- 출처 계약: `data/day2_public_audio/sources.json`, `data/day2_public_audio/SHA256SUMS`
- test: `tests/test_day2_meeting_workflow.py`, `tests/test_day2_notebook.py`, `desktop-app/meeting-intelligence/tests/`
- 실행 결과: `output/course-labs/day2-v2/01_architecture.json`~`08_export_drafts.json`, 세 시나리오 Markdown, email draft JSON
- 오프닝 teaser: `assets/demo-videos/day2_service_teaser.gif`

```bash
.venv312/bin/python scripts/build_days2_5_notebooks.py --day 2 --execute --timeout-seconds 900
.venv312/bin/python -m pytest -q tests/test_day2_meeting_workflow.py tests/test_day2_notebook.py
cd desktop-app/meeting-intelligence && ./scripts/test.sh
```

### 운영 가능한 서비스로 가기 위해 남기는 증거

- `provider_requested`, `provider_used`, `fallback_reason`
- `source_mode`, `stt_skipped`, segment별 `start`, `end`, `evidence_id`
- `execution_mode_requested`, `execution_mode_used`, `route_reason`
- `READY/HOLD`, approve·edit·reject, reviewer, reason
- evidence가 없는 담당자·기한은 추측하지 않고 `null`
- `human_review_required=true`, `external_write=false`, integration `PLAN_ONLY`

## 5. Day 3 · Review Intelligence Service

### 강사가 먼저 보여줄 전체 흐름

1. Day 2 회의록 Export 변경인 `meeting_export_pr.diff`에서 `+++` target과 `@@` hunk를 읽는다.
2. 삭제·context·추가 라인에 따라 new line number가 어떻게 변하는지 보여준다.
3. `eval`, 외부 쓰기, broad exception의 deterministic finding을 만든다.
4. path·line·severity·evidence·correction·confidence·rule ID를 검증한다.
5. Codex에게 `AGENTS.md`, 허용 path, focused test를 포함한 작은 구현 요청을 준다.
6. Codex가 만든 diff와 실제 test 결과를 분리해 사람이 검토한다.
7. 8개 golden case의 precision·recall·F1을 비교한다.
8. Localhost에서 finding을 유지·수정·제외하고 Draft PR·CI로 연결한다.

### 수강생 실행 파일

- Notebook: `materials/day3/day3_review_intelligence_lab.ipynb`
- 실행 완료본: `materials/day3/day3_review_intelligence_lab.executed.ipynb`
- 핵심 코드: `labs/day3/review_copilot/`
- 입력: `labs/day3/review_copilot/fixtures/meeting_export_pr.diff`
- 정답: `labs/day3/review_copilot/fixtures/golden_findings.json`
- 실행 결과: `output/course-labs/day3-v2/student-run/01_review_contract.json`~`08_release_evidence.json`
- 오프닝 teaser: `assets/demo-videos/day3_service_teaser.gif`

```bash
.venv312/bin/python -m pytest -q tests/test_day3_review_copilot.py
.venv312/bin/python scripts/run_day3_preflight.py
.venv312/bin/python -m labs.day3.review_copilot.web --port 8765
```

### 좋은 코드 리뷰의 수업 기준

- 실제 추가 라인에 관한 finding만 만든다.
- severity는 문체가 아니라 사용자 영향과 재현 조건으로 정한다.
- linter가 잡을 style은 LLM finding에서 제외한다.
- 존재하지 않는 함수·test 결과를 근거로 쓰지 않는다.
- 한 finding에는 한 문제와 가장 작은 안전한 교정만 담는다.

## 6. Day 4 · PR Review Automation Service

### 강사가 먼저 보여줄 전체 흐름

1. synthetic PR fixture에서 repository·PR number·head SHA를 고정한다.
2. `.env`와 `.gitignore`를 확인하되 token 값은 출력하지 않는다.
3. 401·403·404·422·429를 서로 다른 복구 결정으로 설명한다.
4. LangGraph state에서 token·client·raw customer data를 제외한다.
5. interrupt payload에 target·finding·evidence·선택지를 포함한다.
6. 실제 API와 동일한 review comment payload를 dry-run으로 만든다.
7. fake publisher로 approval과 중복 실행 방지를 검증한다.
8. 선택적으로 본인의 sandbox repository에서 한 건만 게시한다.

### 수강생 실행 파일

- Notebook: `materials/day4/day4_service_lab.ipynb`
- 핵심 코드: `src/course_services/github_service.py`, `contracts.py`, `src/langgraph_lab.py`
- 입력: `data/day4_github/pr_fixture.json`
- 실행 결과: `output/course-labs/day4/01_pr_target.json`~`08_day4_audit_record.json`
- 오프닝 teaser: `assets/demo-videos/day4_service_teaser.gif`

```bash
.venv312/bin/python -m pytest -q tests/test_course_services.py -k github
.venv312/bin/python -m pytest -q tests/test_course_services.py -k dry_run
```

### 외부 쓰기 안전 순서

`fixture → read-only → dry-run → target 확인 → 사람 승인 → 한 건 게시 → remote ID 기록`

실제 GitHub publisher와 PAT는 repository 기본 코드에 포함하지 않는다. 강사와 학습자가 소유한 sandbox 대상이 확인된 경우에만 별도 branch 또는 local adapter로 연결한다.

## 7. Day 5 · Agent Operations Console

### 강사가 먼저 보여줄 전체 흐름

1. `input_kind`를 명시해 meeting과 code review service를 호출한다.
2. local trace에서 node status·latency·fallback·READY/HOLD를 확인한다.
3. synthetic 또는 비식별 결과 요약만 LangSmith에 선택 upload한다.
4. golden dataset으로 baseline과 candidate를 같은 입력에서 비교한다.
5. approve·edit·reject의 reason을 human feedback으로 남긴다.
6. PII·secret·retention·incident checklist를 release gate에 포함한다.
7. Python output JSON과 Vercel demo가 같은 contract인지 확인한다.
8. 정상 한 건과 대표 HOLD 한 건으로 3분 demo를 구성한다.

### 수강생 실행 파일

- Notebook: `materials/day5/day5_service_lab.ipynb`
- 핵심 코드: `src/course_services/service_router.py`, `eval_service.py`, `src/observability_lab.py`
- 입력: `data/meeting_sample_ko.txt`, `data/day3_review_cases/unsafe_pr.diff`
- 실행 결과: `output/course-labs/day5/01_unified_service_result.json`~`08_release_scorecard.json`
- 오프닝 teaser: `assets/demo-videos/day5_service_teaser.gif`

```bash
.venv312/bin/python -m pytest -q tests/test_course_services.py -k router
.venv312/bin/python -m pytest -q tests/test_course_services.py -k offline_eval
```

## 8. 강의 전 준비할 실제 화면

| 화면 | 캡처할 내용 | 실패 시 대체 |
|---|---|---|
| VS Code | repository root, `.venv312`, `src/course_services`, `tests` | 제공 PNG와 notebook |
| Jupyter | install cell, ROOT, 정상 결과 JSON | 실행 완료본 또는 fixture |
| Terminal | focused test와 full suite의 실제 통과 결과 | 마지막 검증 log |
| Ollama | `qwen3:4b` model 존재와 provider_used | fixture + fallback_reason |
| LangGraph | approve·edit·reject state | local JSON 세 개 |
| GitHub | 본인 sandbox PR target과 dry-run payload | synthetic fixture |
| LangSmith | synthetic trace의 node·latency·status | local `trace.json` |
| Vercel | Python output과 같은 결과 schema, `course.html?day=2~5` | `web-demo/` local server |

실제 고객 회의·회사 코드·token·로그는 캡처하지 않는다. 화면 캡처에는 repository와 sample이 교육용 synthetic임을 확인할 수 있어야 한다.

## 9. 현재 서비스 코드 지도

```text
src/course_services/
├── contracts.py          # Review·PR payload contract
├── meeting_service.py    # segment chunk와 evidence 검사
├── review_service.py     # unified diff parser와 deterministic baseline
├── github_service.py     # dry-run·approval·idempotency
├── codex_harness.py      # Codex task spec과 merge gate
├── eval_service.py       # precision·recall·release gate
└── service_router.py     # meeting·review 명시 routing
```

## 10. 최종 merge 전 검증

```bash
.venv312/bin/python -m pytest -q tests/test_course_services.py
.venv312/bin/python -m pytest -q tests/test_meeting_agent_workflow.py
.venv312/bin/python -m pytest -q
```

Codex review, 다른 LLM review, test 통과는 merge 판단의 증거다. 최종 반영·외부 게시·배포는 사람이 결정한다.

## 참고

- [OpenAI Codex use cases](https://learn.chatgpt.com/use-cases)
- [OpenAI Codex documentation](https://developers.openai.com/codex/)
- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangSmith observability](https://docs.langchain.com/langsmith/observability)
- [GitHub REST authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
