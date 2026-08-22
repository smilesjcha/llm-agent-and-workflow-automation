# LLM Agent & 업무자동화 40H

재직자·구직자가 무료 또는 로컬 환경에서 STT, LLM, LangChain, LangGraph, LangSmith를 연결해 실제 업무 자동화를 구현하는 프로젝트 기반 교육 자료입니다.

## 1일차 핵심 산출물

- `slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pptx`: 1일차 270장 강의 자료
- `output/pdf/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pdf`: 배포·검수용 PDF
- `materials/day1/2026-08-23_Day1_강사용_핵심교안.md`: 시간대별 강의·시연·실습 운영안
- `materials/day1/04_codex_github_pr_lab.md`: GitHub·Codex·PR 리뷰 실습 런북
- `materials/day1/강사_회의음성_라이브데모_런북.md`: STT 라이브 데모 및 실패 복구 절차
- `data/meeting_sample_ko_12min.wav`: 4인 합성 한국어 회의 음성
- `data/meeting_sample_ko_12min.txt`: 회의 원문과 타임라인

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-day1.txt
python -m pytest -q
python -m src.day1_agent
```

STT를 로컬에서 실행하려면 선택 의존성을 추가합니다.

```bash
python -m pip install -r requirements-stt-optional.txt
python -m src.meeting_demo --audio data/demo_meeting.wav \
  --transcript data/demo_meeting_transcript.txt
```

모델 설치가 없거나 STT가 실패해도 제공된 전사문으로 동일한 후속 파이프라인을 검증할 수 있습니다.

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
