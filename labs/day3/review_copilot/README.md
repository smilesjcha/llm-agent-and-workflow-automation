# Day 3 · Review Copilot

실제 코드 변경을 읽고, 추가된 줄에만 근거를 둔 리뷰 초안을 만든 뒤, Human Review와 GitHub dry-run까지 연결하는 오프라인 서비스입니다. 기본 실행은 네트워크·토큰 사용과 외부 서비스 변경이 전혀 없는 fixture 모드입니다.

## 1~8차시 누적 구조

| 차시 | 직접 코드화할 부분 | 핵심 파일 | 완료 증거 |
|---|---|---|---|
| 1차시 | 좋은 리뷰의 범위·severity·금지 행동 | `contracts.py` | `01_review_contract.json` |
| 2차시 | Unified Diff와 변경 후 line mapping | `diff_parser.py` | `02_parsed_diff.json` |
| 3차시 | 최소 context와 민감 경로 제외 | `context_builder.py`, `workspace.py` | `03_context_pack.json` |
| 4차시 | LLM adapter와 fixture fallback | `providers.py` | `04_candidate_review.json` |
| 5차시 | rule baseline·LLM 후보 결합·근거 검증 | `review_engine.py` | `05_hybrid_review.json` |
| 6차시 | 승인·수정·거절 Human Review | `human_review.py` | `06_human_review.json` |
| 7차시 | 8개 golden case·precision·recall·F1 | `evaluation.py` | `07_evaluation.json` |
| 8차시 | GitHub dry-run·localhost demo·release evidence | `github_plan.py`, `workflow.py`, `web_app.py` | `08_release_evidence.json` |

## 실행

저장소 루트에서 실행합니다.

```bash
python3 -m labs.day3.review_copilot.cli
python3 -m labs.day3.review_copilot.cli --run-tests
python3 -m labs.day3.review_copilot.cli run --run-tests --decision approve
python3 -m labs.day3.review_copilot.cli cases
python3 -m labs.day3.review_copilot.cli inspect --case unsafe_dynamic_execution
python3 -m labs.day3.review_copilot.cli context --case external_write
python3 -m labs.day3.review_copilot.cli review --case all --provider fixture
python3 -m labs.day3.review_copilot.cli evaluate
python3 -m labs.day3.review_copilot.web --port 8765
python3 -m pytest -q tests/test_day3_review_copilot.py
```

결과는 `output/course-labs/day3-v2/student-run/` 아래에 차시별 JSON으로 저장됩니다. 기본 실행은 test를 실행하지 않고 사람 결정도 없으므로 `REVIEW_REQUIRED/HOLD`입니다. `--run-tests`는 고정된 focused test의 실제 exit code를 저장하며, Finding을 사람이 확인한 뒤에만 `--decision approve`를 추가합니다. 브라우저 demo는 `http://127.0.0.1:8765`에서 열립니다. `08_release_evidence.json` 안의 GitHub 명령은 설명용 제안일 뿐 자동 실행되지 않습니다. 환경 준비는 `python3 -m pip install -r requirements-day3.txt`로 진행합니다.

## Codex와 GitHub 연결

1. 작업 전 `git status --short`와 현재 commit을 기록합니다.
2. Codex 요청에 목표, 허용 경로, 금지 행동, focused test를 함께 적습니다.
3. `codex/day3-review-copilot`처럼 별도 branch에서 작은 변경만 만듭니다.
4. `python -m pytest -q tests/test_day3_review_copilot.py`를 실행합니다.
5. 사람이 `git diff`와 test 결과를 확인합니다.
6. dry-run의 repository·base·branch·PR 본문을 다시 확인합니다.
7. 승인 후에만 `git push`와 `gh pr create`를 사람이 실행합니다.
8. PR에서는 자동 검사 결과와 Codex/Claude 리뷰를 참고하되 merge는 사람이 결정합니다.

Codex에 전달할 완성형 요청과 학생 확인표는 `CODEX_TASK.md`에 있습니다. 기존 `day3-pr-quality.yml`은 PR마다 deterministic guard를 실행하고, `day3-codex-review-optional.yml`은 명시적 opt-in이 있을 때 read-only 리뷰 결과를 artifact로 남깁니다. 둘 다 자동 merge나 자동 comment를 하지 않습니다.

## Provider 교체 규칙

`ReviewProvider` protocol의 `review(prompt)`만 구현하면 OpenAI, Ollama, Claude adapter를 주입할 수 있습니다. 인증값은 provider 내부의 환경변수에서만 읽고 prompt·trace·JSON 결과에 넣지 않습니다. 연결 실패를 성공으로 표시하지 않으며, fixture fallback을 사용하면 `provider_used=fixture`, 실제 `model`, `schema_valid`, `fallback_reason`을 함께 남깁니다. Live Provider 결과는 별도 Candidate 평가 증거가 없으면 `LIVE_PROVIDER_CANDIDATE_EVALUATION_REQUIRED/HOLD`이며 Fixture의 8개 Case 점수로 대신 승인하지 않습니다.

Ollama는 `--provider ollama`와 `OLLAMA_LIVE_OPT_IN=1`이 함께 있을 때만 loopback API를 호출합니다. 기본 모델은 `qwen3:4b`이며, 연결 실패·계약 불일치는 fixture로 복구하면서 실제 사용 provider를 명시합니다.
