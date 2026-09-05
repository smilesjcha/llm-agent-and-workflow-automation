# LLM Agent & 업무자동화 40H

재직자·구직자가 무료 또는 로컬 환경에서 STT, LLM, LangChain, LangGraph, LangSmith를 연결해 실제 업무 자동화를 구현하는 프로젝트 기반 교육 자료입니다.

## 1일차 핵심 산출물

- `slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_PARTS_270p.pptx`: 1일차 270장 강의 자료
- `output/pdf/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_PARTS_270p.pdf`: 배포·검수용 PDF
- `materials/day1/2026-08-23_Day1_강사용_핵심교안.md`: 시간대별 강의·시연·실습 운영안
- `materials/day1/04_codex_github_pr_lab.md`: GitHub·Codex·PR 리뷰 실습 런북
- `materials/day1/04_ollama_agent_workflow.ipynb`: 환경·Ollama/GPT Tool Calling·LCEL provider 비교 실습
- `materials/day1/04_ollama_agent_workflow.executed.ipynb`: Qwen 성공·GPT opt-in fallback을 포함한 실행 완료본
- `materials/day1/07_langchain_langgraph_workflow.ipynb`: LCEL·StateGraph·interrupt/resume 실행 notebook
- `materials/day1/07_langchain_langgraph_workflow.executed.ipynb`: 설치 실패 시에도 흐름을 확인할 실행 완료본
- `materials/day1/08_audio_meeting_agent_workflow.ipynb`: WAV→STT→Ollama→LangGraph HITL 통합 실행 실습
- `materials/day1/08_audio_meeting_agent_workflow.executed.ipynb`: 실제 `small`·`qwen3:4b` 성공 출력을 포함한 실행 완료본
- `materials/day1/수강생용_4-8차시_실습패키지_가이드.md`: 설치 셀·차시별 실행·복구·제출 안내
- `materials/day1/실행파일_차시별_맵.md`: 1~8차시별 파일·명령·완료 증거
- `materials/day1/강사_회의음성_라이브데모_런북.md`: STT 라이브 데모 및 실패 복구 절차
- `src/langchain_lab.py`: Prompt·Provider·Pydantic parser·policy validator LCEL
- `src/ollama_tool_agent.py`: fixture/Ollama/OpenAI Tool Call 제안과 SafeToolExecutor 연결
- `src/openai_provider.py`: GPT-5.6 Luna Responses API function/text adapter
- `src/langgraph_lab.py`: StateGraph·checkpoint·사람 승인·재개
- `src/workflow_service.py`: LCEL→Graph→local trace→READY/HOLD 전체 흐름
- `src/meeting_agent_workflow.py`: 음성 인식부터 STT/요약 이중 사람 검증까지 연결한 전체 회의 Agent
- `web-demo/`: Python 결과를 승인·수정·거절하고 JSON으로 저장하는 결과 UI
- `data/meeting_sample_ko_12min.wav`: 4인 합성 한국어 회의 음성
- `data/meeting_sample_ko_12min.txt`: 회의 원문과 타임라인

## 2~3일차 최종본·4~5일차 초안

- `slides/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pptx`: 2일차 수강생용 최종 강의 자료
- `output/pdf/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pdf`: 2일차 배포·검수용 최종 PDF
- `materials/day2/2026_Day2_수강생_실습가이드.md`: 1~8차시 실행·복구·산출물 안내
- `materials/day2/2026_Day2_강사용_상세교안.md`: 강사 진행·시연·복구 안내
- `materials/day2/2026_Day2_강의직전_체크리스트.md`: 릴리스·환경·시연 점검표
- `materials/day2/day2_service_lab.ipynb`: 회의기록 Workflow·Agent·Human Review 실습
- `materials/day2/day2_service_lab.executed.ipynb`: 실행 완료 참고본
- `output/course-labs/day2-v2/`: 읽기 전용 기준 결과; 수강생 실행 결과는 `student-run/`과 `run_manifest.json`에 분리
- `slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx`: **206장 코드 리뷰 Agent 정본**. Context 비교·단계별 코드 수정·직접 LangGraph 구현·사람 판정 Eval·Localhost
- `output/pdf/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pdf`: 같은 장표의 배포·검수용 PDF. 이전 176p 파일은 구버전
- `slides/IPA_LLM_Agent_업무자동화_Day4_DRAFT_240p.pptx`: GitHub target·권한·LangGraph·승인·dry-run·idempotency
- `slides/IPA_LLM_Agent_업무자동화_Day5_DRAFT_240p.pptx`: router·LangSmith·dataset eval·human feedback·release/demo
- `materials/day3/day3_review_intelligence_lab.ipynb`: 직접 구현·실패 재현·실제 코드 수정·재실행을 포함한 1~8차시 실습
- `materials/day3/day3_review_intelligence_lab.executed.ipynb`: fixture 기반 실행 완료 참고본
- `materials/day3/2026_Day3_수강생_실습가이드.md`: 설치·차시별 실행·복구·PR 안내
- `materials/day3/2026_Day3_강사용_상세교안.md`: 8시간 발화·시연·실습 운영안
- `materials/day3/코드리뷰_Agent_아키텍처.md`: Mermaid 마스터 구조·대화형 Agent와 리뷰 Adapter의 구분
- `materials/day3/4·5주차_운영안_및_미니프로젝트.md`: GitHub 자동 리뷰·마지막 주 개인 프로젝트 3시간 운영
- `materials/day3/페이지별_강의_진행.md`: 페이지별 권장 시간·설명·코드·실습 연결
- `materials/day3/심화_4개차시_강사운영안.md`: 3·5·6·7차시 50분 상세 운영, 필수 실습과 선택 보충 자료
- `materials/day3/글로벌_사례_해설.md`: Google·Anthropic·CodeRabbit·Sentry·LangGraph·LangSmith의 공식 사례와 코드 연결
- `materials/day3/day3_global_references.json`: OpenAI 포함 16개 공식 출처·확인일·적용 범위·한계
- `labs/day3/review_copilot/`: diff·context·provider·review·LangGraph·evaluation·localhost 서비스
- `output/course-labs/day3-v2/`: 8개 차시 검토 완료 기준 결과
- `dist/day3-student-code-bundle.zip`: 정본 Notebook·서비스·Fixture·Test만 담은 학생용 코드 묶음
- `materials/day4/day4_service_lab.ipynb`: GitHub dry-run·사람 승인·중복 실행 방지
- `materials/day5/day5_service_lab.ipynb`: 서비스 router·golden evaluation·release gate
- `materials/days2_5/32시간_Codex_서비스_운영_블루프린트.md`: 강사 시연·수강생 실행·파일·명령·운영 기준
- `materials/40시간_실습_정의와_차시별_실행지도.md`: 실습 정의·1~5일차 40개 차시·준비 상태·보강 순서
- `src/course_services/`: Day 2-5 서비스 contract·meeting·review·GitHub·Codex harness·evaluation·router

## 빠른 시작

```bash
python3.12 --version
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-day1.txt
python -m pip check
python -m pytest -q
python -m src.day1_agent
python -m src.ollama_tool_agent --probe
python -m src.ollama_tool_agent --provider ollama
python -m src.ollama_tool_agent --provider openai
python -m src.langchain_lab --provider fixture
python -m src.langgraph_lab --decision all
python -m src.workflow_service --decision approve --out output/day1-workflow
python -m src.meeting_agent_workflow \
  --audio data/demo_meeting.wav \
  --transcript-fixture data/demo_meeting_transcript.txt \
  --out output/day1-meeting-agent \
  --stt-model small --device cpu --compute-type int8 --local-files-only \
  --provider ollama --llm-model qwen3:4b \
  --transcript-decision accept --summary-decision approve
python scripts/run_day1_preflight.py
python scripts/build_day1_student_bundle.py
```

기존 `.venv`가 Python 3.9로 만들어졌다면 내부 Python을 업그레이드할 수 없으므로 재사용하지 않는다. 위처럼 새 `.venv312`를 만들고, VS Code와 Notebook Kernel도 그 환경의 Python으로 다시 선택한다. `pip3 install -r requirements*.txt`처럼 wildcard로 모든 파일을 한꺼번에 설치하지 말고, 기본·로컬 LLM·OpenAI·STT를 필요한 순서대로 분리한다.

### 2일차 실행

```bash
python -m pip install -r requirements-day2.txt
python scripts/run_day2_preflight.py --full-suite
python scripts/build_day2_student_bundle.py
jupyter lab materials/day2/day2_service_lab.ipynb
python scripts/run_day2_local_app.py
```

Notebook의 기본 실행은 강사가 검토한 음성·전사 fixture를 사용한다. 8차시는 Docker 없는 localhost App이 기본이며 macOS `run-local.command`, Windows `run-local.cmd`, 공통 `run_day2_local_app.py` 중 하나로 실행한다. 화면의 `예시로 바로 시작`을 누르면 파일 선택 없이 전체 흐름을 확인할 수 있다. `faster-whisper`, Ollama, OpenAI는 필요한 의존성과 opt-in을 준비한 경우만 실행한다. 기준 결과는 `output/course-labs/day2-v2/`에서 읽고, 자신의 결과는 `output/course-labs/day2-v2/student-run/`과 `run_manifest.json`에서 확인한다.

### 3일차 실행

```bash
python -m pip install -r requirements-day3.txt
codex --version
codex login status
python scripts/run_day3_preflight.py
jupyter lab materials/day3/day3_review_intelligence_lab.ipynb
python -m labs.day3.review_copilot.web --port 8765
# 실제 코드 준비·실행·테스트
python -m labs.day3.review_copilot.cli exercise --step prepare
python -m labs.day3.review_copilot.cli exercise --step demo
python -m labs.day3.review_copilot.cli exercise --step test
# 로그인 확인 후 명시적 실제 리뷰
python -m labs.day3.review_copilot.cli exercise --step review --provider codex_cli --live
python scripts/build_day3_student_bundle.py
```

3주차 주 실행 경로는 **로컬 Codex CLI + ChatGPT 로그인**이다. 모델 추론은 연결된 클라우드 서비스에서 수행하며 인터넷·계정 이용 권한·한도가 필요하다. Ollama나 API key는 3주차 필수 준비물이 아니다. Notebook의 `RUN_CODEX_LIVE=True`에서 실제 리뷰를 실행하고, 기본 Run All은 출처를 표시한 Fixture로 재현한다. 실습은 결제 계산의 실제 오류 재현→리뷰→Python 파일 수정→동일 Test 재실행→화면 확인이다. Notebook 실행마다 생성되는 폴더 경로를 확인해 자신의 코드를 보존한다. GitHub push·Draft PR·리뷰 요청은 본인 저장소와 변경 Diff를 확인한 뒤 실행하고 자동 merge는 하지 않는다. 기존 8개 JSON은 내부 단계 호환·디버깅용이며 실습 완료 기준이 아니다.

코드 ZIP만 받은 경우 `python scripts/run_day3_preflight.py --code-only`로 검사한다. 전체 PPT/PDF 배포 검사는 Git 저장소의 기본 preflight를 사용한다.

Ollama용 adapter가 필요할 때만 기본 설치 뒤에 다음 명령을 추가한다.

```bash
python -m pip install -r requirements-local-llm-optional.txt
python -m pytest -q tests/test_langchain_langgraph_lab.py tests/test_ollama_tool_agent.py
```

GPT API 비교는 공개된 키를 폐기·재발급한 뒤 로컬에서만 설정한다.

```bash
python -m pip install -r requirements-openai-optional.txt
cp .env.sample .env
# .env의 placeholder를 새 키로 교체. Notebook 비교 시 OPENAI_LIVE_OPT_IN=1
python -m src.ollama_tool_agent --provider openai
python -m src.langchain_lab --provider openai
```

모델 ID는 `gpt-5.6-luna`다. Tool Calling은 Responses API function calling, 회의 구조화는 `responses.parse`와 `MeetingBrief` Structured Outputs를 사용한다. 직접 `provider="openai"`를 지정하면 API 실행을 명시적으로 선택한 것으로 처리한다. Notebook Run All은 기본 `OPENAI_LIVE_OPT_IN=0`에서 OpenAI 셀을 fixture로 복구한다. `.env`는 Git에서 제외되고 `.env.sample`만 배포된다. [OpenAI 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [Structured Outputs 문서](https://developers.openai.com/api/docs/guides/structured-outputs)

LangSmith 웹에는 합성 또는 비식별 데이터의 실행 요약만 명시적으로 업로드한다. `.env`에 `LANGSMITH_API_KEY`와 `LANGSMITH_PROJECT`를 설정하고, 자동 추적으로 원문이 전송되지 않도록 `LANGSMITH_TRACING=false`를 유지한다.

```bash
python -m src.workflow_service \
  --decision approve \
  --out output/day1-workflow \
  --upload-langsmith \
  --data-classification synthetic
```

CLI는 Git에서 제외된 `.env`를 자동으로 읽는다. 성공 결과는 `langsmith.uploaded=true`, 프로젝트명, `run_id`를 출력한다. `local_only`, API key 누락, API 오류는 전송하지 않고 `LANGSMITH_*` 오류 코드와 종료 코드 `2`를 반환한다. 업로드 payload에는 transcript·모델 원문·파일 경로를 넣지 않고, 단계별 상태·지연시간과 `READY/HOLD`만 기록한다.

정상 기준은 전체 test 통과, 안전한 파일 Tool 실행, LangGraph `READY_FOR_EXPORT`, 평가 `READY`, `automatic_email=false`다. 선택 provider가 없으면 `provider_used=fixture`와 `fallback_reason`이 함께 남아야 하며, 거절 경로는 `REJECTED/HOLD`여야 한다.
전체 점검 결과는 `output/day1-preflight/preflight_report.json`에서 차시별 명령·종료 코드·결과 파일과 함께 확인한다.
별도 배포용 ZIP은 `dist/day1-student-lab-bundle.zip`에 생성되며, 기본값은 43MB 상세 음성과 비밀정보를 제외한다.

배포된 읽기·검토용 결과 UI: https://web-demo-five-sigma.vercel.app

1일차 회의 데모에서 STT를 로컬로 실행하려면 선택 의존성을 추가합니다.

```bash
python -m pip install -r requirements-stt-optional.txt
python -m src.meeting_demo --audio data/demo_meeting.wav \
  --transcript data/demo_meeting_transcript.txt \
  --model tiny --device cpu --compute-type int8
```

`tiny`는 1일차 강의 전 smoke test용입니다. 품질 비교용 `small` 모델은 수업 전에 미리 내려받습니다. 모델 설치가 없거나 STT가 실패하면 1일차에서 제공한 같은 음성의 전사문으로 후속 파이프라인을 계속하되 `quality_gate=HOLD`로 사람 검증을 요구합니다.

## 저장소 운영 기준

- `AGENTS.md`: 구현·리뷰·사람 승인 기준
- `.github/pull_request_template.md`: 검증 증거와 위험을 남기는 PR 템플릿
- `.github/workflows/test.yml`: `pytest`와 diff 검증
- `design-system/ppt/cha-sungjae-lecture/`: PPT 디자인 시스템과 콘텐츠 하네스

실행 캐시, 슬라이드 렌더 이미지, 비밀키가 담길 수 있는 `.env`와 `.env.*`는 Git에서 제외하고 `.env.sample`만 추적합니다.

## PPT 재생성

프레젠테이션 빌드 환경에서는 다음 소스로 강의 자료를 다시 생성할 수 있습니다. 3일차는 `CODEX_CLI` 리디자인 정본이며, 4·5일차 PPT는 초안입니다. 4·5일차의 최신 운영 계획은 3일차 가이드에 연결되어 있습니다.

```bash
node scripts/slides/build_day1_detail.mjs
node scripts/slides/build_day2_student_ready.mjs
# 기존 정본을 보존하며 새 파일로 검증·출력
DAY3_FINAL_PATH="$PWD/slides/Day3_CODEX_CLI_next.pptx" node scripts/slides/build_day3_codex_cli.mjs
node scripts/slides/build_days2_5_drafts.mjs --day 4
node scripts/slides/build_days2_5_drafts.mjs --day 5
```

생성 후에는 오버플로 검사, PDF 변환, 전체 페이지 렌더 검수를 다시 수행합니다.
