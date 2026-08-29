# 나의 회의 기록 도우미 · Day 2

일반 사용자가 가진 회의 자료를 `입력 → 업무 맥락 → 원하는 결과 → 근거 검사 → 사람 확인` 순서로 처리하는 로컬 GUI입니다. 결과는 자동 확정하지 않으며 Notion·Confluence·이메일에 실제로 쓰거나 보내지 않습니다.

## 지원하는 세 입력

| 가지고 있는 자료 | 앱의 실제 처리 | 준비할 것 |
|---|---|---|
| Google Meet 또는 일반 회의 전사 | TXT 파싱, 화자·시간·발화 구간 생성 | 전사 TXT, 참석자 이름·역할·팀·이메일(선택) |
| ClovaNote 내보내기 | `참석자 1 00:00` 형식 파싱, 참석자 메타데이터와 이름 매핑 | ClovaNote TXT, 참석자 정보(선택) |
| 회의 녹음 | 파일 검사 후 로컬 `faster-whisper`로 실제 음성 변환 | WAV·MP3·M4A·OGG·WEBM, 최대 100MB |

텍스트 입력에는 음성 변환이 필요하지 않습니다. 음성 변환이 실패하면 포함된 예시 전사로 바꾸지 않고 `HOLD`로 멈춥니다. 다른 회의 결과를 업로드한 녹음의 결과처럼 보여주지 않기 위한 정책입니다.

화면에서 다음을 추가할 수 있습니다.

- 산업·업무 용어와 해석 기준
- 회의 전에 이미 합의되거나 논의된 맥락
- 원하는 결과: 요약, 참석자별 관점, 할 일, 단기·중기·장기 인사이트
- 자연어 추가 요청

## LLM·Workflow·Agent 선택 기준

앱은 이름만 바꾸는 것이 아니라 rule-based router로 실행 방식을 기록합니다.

| 방식 | 적합한 요청 | 앱에서 하는 일 |
|---|---|---|
| LLM | 맥락이 없는 TXT 한 번 요약 | 입력 정리 → 구조화 결과 → 근거 검사 |
| Workflow | 음성 변환 또는 여러 결과를 같은 순서로 반복 | 입력 → 품질 → 맥락 → 결과 → 문서·메일 초안 → 근거 검사 |
| Agent | 외부 기록 조회·문서 저장·이메일 같은 다음 행동의 판단이 포함된 요청 | 목적 판단 → 필요한 정보·연결 후보 계획 → 승인 대기 |

자동 선택에서 단순 요약은 LLM, 고정 단계가 여러 개면 Workflow, 추가 요청에 Notion·Confluence·Slack·이메일·외부 조회 단서가 있으면 Agent로 분기합니다. Agent 모드도 외부 서비스를 실제로 읽거나 쓰지 않습니다. 허용된 회의 입력으로 결과를 만들고 `integration_plan`만 남깁니다.

## 실행

고정 진입점:

| 항목 | 위치 |
|---|---|
| 로컬 GUI | `http://127.0.0.1:8766` |
| 상태 확인 | `GET http://127.0.0.1:8766/health` |
| 처리 API | `POST http://127.0.0.1:8766/api/process` |
| 예시 TXT | `GET http://127.0.0.1:8766/api/samples/google-meet` |

가장 빠른 실행:

```bash
cd desktop-app/meeting-intelligence
docker compose up --build
```

브라우저에서 `http://127.0.0.1:8766`을 엽니다. Docker image와 Whisper model을 처음 받을 때는 네트워크와 시간이 필요합니다.

종료·복구:

```bash
docker compose down
docker compose up --build
```

모델 cache까지 지워 처음 상태로 되돌리는 `docker compose down -v`는 Whisper model을 다시 내려받게 되므로 필요한 경우에만 사용합니다.

## 결과를 만들 AI

| 화면 선택 | 실제 adapter | 준비 조건 |
|---|---|---|
| 인터넷 없이 연습용 결과 | deterministic grounded record | 없음 |
| Ollama | `POST /api/generate`, 기본 `qwen3:4b` | `ollama pull qwen3:4b`, `ollama serve` |
| Codex 프로그램 | localhost token bridge → 공식 `codex exec` | 패키지 launcher와 CLI 로그인 |
| Claude Code 프로그램 | localhost token bridge → 공식 `claude -p` | 패키지 launcher와 CLI 로그인 |
| OpenAI API | Responses API Structured Outputs | `OPENAI_API_KEY` 환경 변수 |

OpenAI API는 키를 화면이나 요청 body로 받지 않습니다. 다음 파일에는 빈 값과 모델명만 있습니다.

```bash
cp .env.example .env
# .env의 OPENAI_API_KEY를 실행하는 PC에서만 입력
docker compose up --build
```

`.env`와 `.env.*`는 이 디렉터리의 `.gitignore`에 포함되고 `.env.example`만 배포됩니다. 기본 모델은 환경 변수로 바꿀 수 있는 `gpt-5.6-luna`입니다. 모델 이름 형식이 잘못됐거나 API에서 사용할 수 없는 모델이면 `OPENAI_MODEL_INVALID`라는 안정된 사유로 끝납니다. 화면에서 fallback을 허용한 경우 연습용 결과로 전환되고, 허용하지 않으면 `HOLD`입니다. API 키나 provider 원문 오류는 결과 JSON에 포함하지 않습니다.

Ollama:

```bash
ollama pull qwen3:4b
ollama serve
```

Docker 컨테이너는 `host.docker.internal:11434`로 호스트 Ollama에 접근합니다.

## Codex·Claude localhost bridge

컨테이너에 홈 디렉터리, 브라우저 cookie, ChatGPT·Claude credential 파일을 마운트하지 않습니다. 패키지 launcher가 `127.0.0.1:8765`에 여는 일회성 bridge가 공식 CLI에만 위임합니다.

```text
Container → 실행 때마다 새로 만든 256-bit token → localhost bridge
          → codex exec --ephemeral --sandbox read-only
          또는 claude -p --tools "" --no-session-persistence
```

안전 경계:

- bridge는 localhost에만 bind
- `codex`, `claude`만 allowlist하고 shell 이름은 거부
- prompt·output 최대 크기, 동시 실행 1개, 120초 timeout
- Codex는 빈 임시 폴더와 read-only sandbox 사용
- Claude는 tools·MCP·session persistence 비활성화
- CLI stderr·credential 경로·bridge token을 API 응답으로 전달하지 않음
- 모든 결과를 Pydantic Schema와 evidence validator로 다시 검사

개발 중 launcher 실행:

```bash
go run . --app-dir "$(pwd)"
```

수동 `docker compose` 실행에는 bridge token이 없으므로 Codex·Claude는 명시적 연결 실패 또는 허용된 연습 결과 fallback으로 끝납니다.

## 출력 계약

핵심 결과:

```json
{
  "status": "READY",
  "source_mode": "google_meet",
  "execution_mode_requested": "auto",
  "execution_mode_used": "workflow",
  "route_reason": "...",
  "workflow_steps": ["회의 입력 정리", "품질 확인", "..."],
  "provider_requested": "openai",
  "provider_used": "openai",
  "model_requested": "gpt-5.6-luna",
  "model_used": "gpt-5.6-luna",
  "meeting_record": {
    "title": "...",
    "summary": {"text": "...", "evidence_ids": ["s001"]},
    "participant_perspectives": [],
    "action_items": [],
    "short_term_insights": [],
    "mid_term_insights": [],
    "long_term_insights": []
  },
  "evidence": [{"segment_id": "s001", "speaker": "...", "text": "..."}],
  "human_review_required": true,
  "external_write": false,
  "markdown_preview": "# ...",
  "email_draft": {"send_status": "DRAFT_ONLY"},
  "integration_plan": [
    {"destination": "notion", "status": "PLAN_ONLY", "approval_required": true},
    {"destination": "confluence", "status": "PLAN_ONLY", "approval_required": true},
    {"destination": "email", "status": "PLAN_ONLY", "approval_required": true}
  ]
}
```

`READY`는 사람이 검토할 수 있다는 뜻이지 최종 확정이 아닙니다. 결과의 모든 요약·참석자 관점·결정·할 일·인사이트·질문은 실제 `segment id`를 가져야 하며, 없는 근거 ID가 하나라도 있으면 외부 계획과 초안을 실행 가능한 상태로 내보내지 않습니다.

Google Meet TXT API 예시:

```bash
curl -s http://127.0.0.1:8766/api/process \
  -F 'source_mode=google_meet' \
  -F 'transcript_file=@fixtures/google_meet_sample_ko.txt;type=text/plain' \
  -F 'participants=<fixtures/participants_sample.json' \
  -F 'requested_outputs=summary,participant_perspectives,todos,insights' \
  -F 'execution_mode=auto' \
  -F 'provider=fixture'
```

음성 API 예시에서는 `source_mode=audio`, `audio=@meeting.wav`를 전달합니다. 새 GUI는 음성 입력에서 항상 live STT를 사용합니다. 기존 Day 2 notebook 호환을 위한 `stt_mode=fixture`는 API에만 남아 있고 GUI에는 노출하지 않습니다.

## 검증과 패키징

로컬 테스트:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./scripts/test.sh
```

테스트 범위:

- Google Meet TXT 정상 처리와 참석자 메타데이터
- ClovaNote 참석자 번호→이름 매핑
- 음성 업로드→live STT adapter 경계
- 세 입력별 빈 파일·손상 파일·인코딩·짧은 전사
- LLM·Workflow·Agent rule router
- OpenAI Responses adapter, 키 미설정, 잘못된 모델, fallback on/off
- 모든 결과의 근거 ID, `human_review_required=true`, `external_write=false`
- localhost bridge token·provider allowlist·CLI tool 비활성화

Windows EXE와 macOS PKG:

```bash
./scripts/build-packages.sh
```

산출물:

```text
dist/MeetingIntelligence-Windows.exe
dist/MeetingIntelligence-macOS.pkg
dist/SHA256SUMS
```

현재 파일은 교육·내부 검증용 unsigned build입니다. 외부 배포 전 조직 인증서로 Windows code signing과 Apple Developer ID signing·notarization이 필요합니다.

## 파일 구조

```text
meeting-intelligence/
├── app/
│   ├── ingestion.py       Google Meet·ClovaNote adapter
│   ├── stt.py             faster-whisper adapter
│   ├── providers.py       fixture·Ollama·CLI·OpenAI adapter
│   ├── pipeline.py        router·workflow·근거·승인 gate
│   └── models.py          공개 결과 Schema
├── fixtures/              비식별 합성 TXT·참석자 예시
├── static/                일반 사용자용 한국어 GUI
├── tests/                 정상·경계·보안 test
├── main.go                embedded Docker launcher·safe CLI bridge
├── Dockerfile
└── docker-compose.yml
```
