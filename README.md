# LLM Agent & 업무자동화 40H

재직자·구직자가 무료 또는 로컬 환경에서 STT, LLM, LangChain, LangGraph, LangSmith를 연결해 실제 업무 자동화를 구현하는 프로젝트 기반 교육 자료입니다.

## 1일차 핵심 산출물

- `slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pptx`: 1일차 270장 강의 자료
- `output/pdf/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pdf`: 배포·검수용 PDF
- `materials/day1/2026-08-23_Day1_강사용_핵심교안.md`: 시간대별 강의·시연·실습 운영안
- `materials/day1/04_codex_github_pr_lab.md`: GitHub·Codex·PR 리뷰 실습 런북
- `materials/day1/04_ollama_agent_workflow.ipynb`: 12시부터 이어지는 환경·Ollama Tool Calling·LCEL 실습
- `materials/day1/04_ollama_agent_workflow.executed.ipynb`: Ollama 미설치 fallback까지 포함한 실행 완료본
- `materials/day1/07_langchain_langgraph_workflow.ipynb`: LCEL·StateGraph·interrupt/resume 실행 notebook
- `materials/day1/07_langchain_langgraph_workflow.executed.ipynb`: 설치 실패 시에도 흐름을 확인할 실행 완료본
- `materials/day1/실행파일_차시별_맵.md`: 1~8차시별 파일·명령·완료 증거
- `materials/day1/강사_회의음성_라이브데모_런북.md`: STT 라이브 데모 및 실패 복구 절차
- `src/langchain_lab.py`: Prompt·Provider·Pydantic parser·policy validator LCEL
- `src/ollama_tool_agent.py`: Ollama/fixture Tool Call 제안과 SafeToolExecutor 연결
- `src/langgraph_lab.py`: StateGraph·checkpoint·사람 승인·재개
- `src/workflow_service.py`: LCEL→Graph→local trace→READY/HOLD 전체 흐름
- `web-demo/`: Python 결과를 승인·수정·거절하고 JSON으로 저장하는 결과 UI
- `data/meeting_sample_ko_12min.wav`: 4인 합성 한국어 회의 음성
- `data/meeting_sample_ko_12min.txt`: 회의 원문과 타임라인

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-day1.txt
python -m pytest -q
python -m src.day1_agent
python -m src.ollama_tool_agent --probe
python -m src.ollama_tool_agent --provider ollama
python -m src.langchain_lab --provider fixture
python -m src.langgraph_lab --decision all
python -m src.workflow_service --decision approve --out output/day1-workflow
python scripts/run_day1_preflight.py
```

정상 기준은 `23 passed`, 안전한 파일 Tool 실행, LangGraph `READY_FOR_EXPORT`, 평가 `READY`, `automatic_email=false`다. Ollama가 없으면 `provider_used=fixture`와 `fallback_reason`이 함께 남아야 하며, 거절 경로는 `REJECTED/HOLD`여야 한다.
전체 점검 결과는 `output/day1-preflight/preflight_report.json`에서 차시별 명령·종료 코드·결과 파일과 함께 확인한다.

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

실행 캐시, 슬라이드 렌더 이미지, 비밀키가 담길 수 있는 `.env`는 Git에서 제외합니다.

## PPT 재생성

Codex 데스크톱의 프레젠테이션 런타임이 연결된 환경에서는 다음 소스로 동일한 270장 PPT를 다시 생성할 수 있습니다.

```bash
node scripts/slides/build_day1_detail.mjs
```

생성 후에는 오버플로 검사, PDF 변환, 전체 페이지 렌더 검수를 다시 수행합니다.
