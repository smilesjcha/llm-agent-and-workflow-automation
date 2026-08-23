# LLM Agent & 업무자동화 40H

재직자·구직자가 무료 또는 로컬 환경에서 STT, LLM, LangChain, LangGraph, LangSmith를 연결해 실제 업무 자동화를 구현하는 프로젝트 기반 교육 자료입니다.

## 1일차 핵심 산출물

- `slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pptx`: 1일차 270장 강의 자료
- `output/pdf/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pdf`: 배포·검수용 PDF
- `materials/day1/2026-08-23_Day1_강사용_핵심교안.md`: 시간대별 강의·시연·실습 운영안
- `materials/day1/04_codex_github_pr_lab.md`: GitHub·Codex·PR 리뷰 실습 런북
- `materials/day1/04_ollama_agent_workflow.ipynb`: 환경·Ollama/GPT Tool Calling·LCEL provider 비교 실습
- `materials/day1/04_ollama_agent_workflow.executed.ipynb`: Qwen 성공·GPT opt-in fallback을 포함한 실행 완료본
- `materials/day1/07_langchain_langgraph_workflow.ipynb`: LCEL·StateGraph·interrupt/resume 실행 notebook
- `materials/day1/07_langchain_langgraph_workflow.executed.ipynb`: 설치 실패 시에도 흐름을 확인할 실행 완료본
- `materials/day1/수강생용_4-8차시_실습패키지_가이드.md`: 설치 셀·차시별 실행·복구·제출 안내
- `materials/day1/실행파일_차시별_맵.md`: 1~8차시별 파일·명령·완료 증거
- `materials/day1/강사_회의음성_라이브데모_런북.md`: STT 라이브 데모 및 실패 복구 절차
- `src/langchain_lab.py`: Prompt·Provider·Pydantic parser·policy validator LCEL
- `src/ollama_tool_agent.py`: fixture/Ollama/OpenAI Tool Call 제안과 SafeToolExecutor 연결
- `src/openai_provider.py`: GPT-5.6 Luna Responses API function/text adapter
- `src/langgraph_lab.py`: StateGraph·checkpoint·사람 승인·재개
- `src/workflow_service.py`: LCEL→Graph→local trace→READY/HOLD 전체 흐름
- `web-demo/`: Python 결과를 승인·수정·거절하고 JSON으로 저장하는 결과 UI
- `data/meeting_sample_ko_12min.wav`: 4인 합성 한국어 회의 음성
- `data/meeting_sample_ko_12min.txt`: 회의 원문과 타임라인

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
python scripts/run_day1_preflight.py
python scripts/build_day1_student_bundle.py
```

기존 `.venv`가 Python 3.9로 만들어졌다면 내부 Python을 업그레이드할 수 없으므로 재사용하지 않는다. 위처럼 새 `.venv312`를 만들고, VS Code와 Notebook Kernel도 그 환경의 Python으로 다시 선택한다. `pip3 install -r requirements*.txt`처럼 wildcard로 모든 파일을 한꺼번에 설치하지 말고, 기본·로컬 LLM·OpenAI·STT를 필요한 순서대로 분리한다.

Ollama용 adapter가 필요할 때만 기본 설치 뒤에 다음 명령을 추가한다.

```bash
python -m pip install -r requirements-local-llm-optional.txt
python -m pytest -q tests/test_langchain_langgraph_lab.py tests/test_ollama_tool_agent.py
```

GPT API 비교는 공개된 키를 폐기·재발급한 뒤 로컬에서만 설정한다.

```bash
python -m pip install -r requirements-openai-optional.txt
cp .env.sample .env
# .env의 placeholder를 새 키로 교체하고 실제 비교 시에만 RUN_OPENAI_LIVE=1
python -m src.ollama_tool_agent --provider openai
python -m src.langchain_lab --provider openai
```

모델 ID는 `gpt-5.6-luna`이며 Responses API function calling을 사용한다. `.env`는 Git에서 제외되고 `.env.sample`만 배포된다. 기본 `RUN_OPENAI_LIVE=0`에서는 유료 호출을 만들지 않고 `provider_used=fixture`와 이유를 남긴다. [OpenAI 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.6-luna)

정상 기준은 전체 test 통과, 안전한 파일 Tool 실행, LangGraph `READY_FOR_EXPORT`, 평가 `READY`, `automatic_email=false`다. 선택 provider가 없으면 `provider_used=fixture`와 `fallback_reason`이 함께 남아야 하며, 거절 경로는 `REJECTED/HOLD`여야 한다.
전체 점검 결과는 `output/day1-preflight/preflight_report.json`에서 차시별 명령·종료 코드·결과 파일과 함께 확인한다.
별도 배포용 ZIP은 `dist/day1-student-lab-bundle.zip`에 생성되며, 기본값은 43MB 상세 음성과 비밀정보를 제외한다.

배포된 읽기·검토용 결과 UI: https://web-demo-five-sigma.vercel.app

STT를 로컬에서 실행하려면 선택 의존성을 추가합니다.

```bash
python -m pip install -r requirements-stt-optional.txt
python -m src.meeting_demo --audio data/demo_meeting.wav \
  --transcript data/demo_meeting_transcript.txt \
  --model tiny --device cpu --compute-type int8
```

`tiny`는 강의 전 smoke test용입니다. 품질 비교용 `small` 모델은 수업 전에 미리 내려받습니다. 모델 설치가 없거나 STT가 실패하면 제공된 전사문으로 후속 파이프라인을 계속하되 `quality_gate=HOLD`로 사람 검증을 요구합니다.

## 저장소 운영 기준

- `AGENTS.md`: 구현·리뷰·사람 승인 기준
- `.github/pull_request_template.md`: 검증 증거와 위험을 남기는 PR 템플릿
- `.github/workflows/test.yml`: `pytest`와 diff 검증
- `design-system/ppt/cha-sungjae-musinsa-lecture/`: PPT 디자인 시스템과 콘텐츠 하네스

실행 캐시, 슬라이드 렌더 이미지, 비밀키가 담길 수 있는 `.env`와 `.env.*`는 Git에서 제외하고 `.env.sample`만 추적합니다.

## PPT 재생성

Codex 데스크톱의 프레젠테이션 런타임이 연결된 환경에서는 다음 소스로 동일한 270장 PPT를 다시 생성할 수 있습니다.

```bash
node scripts/slides/build_day1_detail.mjs
```

생성 후에는 오버플로 검사, PDF 변환, 전체 페이지 렌더 검수를 다시 수행합니다.
