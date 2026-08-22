# Day 1 Tutorial 화면 커버리지

대상 deck: `slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_HUMAN_300p.pptx`

- 총 장표: 300장
- Tutorial Map: 8장(시간대별 1장)
- 실제 화면 캡처: 33장
- 캡처 기준일: 2026-08-22(Asia/Seoul)
- 보안: API key, PAT, 회사 데이터, 개인 저장소 및 개인 식별 정보 없음
- 운영: BLOCK A 09:00-12:00, BLOCK B 12:00-14:00, 점심 14:00-15:00, BLOCK C 15:00-17:30, Q&A 17:30-18:00
- 휴식: BLOCK A 30분, BLOCK B 20분, BLOCK C 30분을 구간 내에서 묶어 운영

## 화면 배치

| 시간 | Map | 실제 화면 장표 | 포함 화면 | 수업 종료 신호 |
|---|---:|---:|---|---|
| BLOCK A · PART 1/3 | 20 | 21-24 | Codex CLI, Claude Code, VS Code의 로컬 저장소, 로컬 Agent 코드 | Agent/Automation 차이를 설명하고 강사 demo 구조를 읽는다. |
| BLOCK A · PART 2/3 | 58 | 59-62 | Ollama API, GitHub REST 인증, pytest 공식 문서, 로컬 9 tests | Tool 계약과 검증·side effect 경계를 설명한다. |
| BLOCK A · PART 3/3 | 96 | 97-100 | 서울 열린데이터광장, 국립국어원 말뭉치, 국회도서관 데이터셋, Google Meet 전사 | 공개 한국어 입력과 근거 보존 원칙을 구분한다. |
| BLOCK B · PART 1/2 | 134 | 135-138 | Python 설치, VS Code Python, Git 첫 설정, GitHub repository quickstart | Python·interpreter·repository의 연결을 직접 확인한다. |
| BLOCK B · PART 2/2 | 171 | 172-175 | Jupyter 설치, VS Code Python, Codex CLI, Claude Code | Notebook Run All, pytest 10개, 첫 commit 전 준비를 끝낸다. |
| BLOCK C · PART 1/3 | 208 | 209-212 | Ollama 다운로드, Qwen3 library, LM Studio server, Jan server | 로컬 provider와 fixture fallback을 같은 계약으로 연결한다. |
| BLOCK C · PART 2/3 | 245 | 246-249 | LangChain overview, LangGraph overview, interrupts, persistence | state·retry·checkpoint·human approval 경계를 설계한다. |
| BLOCK C · PART 3/3 | 281 | 282-286 | faster-whisper, whisper.cpp, Google Meet 자동 노트, LangSmith observability, LangSmith evaluation | STT 입력부터 trace·dataset·release gate까지 한 흐름으로 설명한다. |

## 강사 캡처 교체 규칙

1. 새 캡처는 `assets/screenshots/`에 같은 파일명으로 저장한다.
2. 화면에는 클릭 위치, 입력값, 성공 신호, 실패 시 대체 경로가 보여야 한다.
3. 로그인 화면은 비식별 강사 계정을 사용하고 `.env`, API key, PAT는 절대 노출하지 않는다.
4. UI가 바뀌면 해당 시간의 Tutorial Map 문구와 speaker notes의 URL도 함께 갱신한다.
5. 교체 후 300장을 다시 렌더하고 screenshot 장표, montage, overflow 검사를 확인한다.
