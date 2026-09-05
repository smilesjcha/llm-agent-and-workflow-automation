# Day 3 · Review Copilot

상품 금액보다 큰 쿠폰을 넣었을 때 결제 예정액이 음수가 되는 버그를 직접 재현합니다. 요구사항과 코드를 읽고, 실제 테스트를 실행한 뒤, 로컬 Codex CLI에 리뷰를 요청합니다. 수강생이 코드를 수정하면 같은 테스트와 브라우저 화면에서 달라진 결과를 확인합니다.

주 실행 모델은 **Codex CLI + ChatGPT 로그인**입니다. CLI는 PC에서 실행되며 모델 추론은 온라인에서 진행됩니다. API Key나 Ollama 설치는 필요하지 않습니다. `CODEX_MODEL`을 지정하지 않으면 CLI 기본 모델을 사용하며, 계정의 모델 접근 권한과 이용 한도가 적용됩니다. `fixture`는 연결을 못 하는 경우 명시적으로 선택하는 예시 재생입니다.

## 쿠폰 서비스 실습

```bash
python3 -m pip install -r requirements-day3.txt
codex --version
codex login
codex login status
python3 -m labs.day3.review_copilot.cli exercise --step prepare
python3 -m labs.day3.review_copilot.cli exercise --step demo
python3 -m labs.day3.review_copilot.cli exercise --step test
python3 -m labs.day3.review_copilot.cli exercise --step review --provider codex_cli --live
```

초안 테스트는 의도적으로 **9개 중 7개 실패**하며 exit code는 1입니다. 초안의 버그를 재현한 결과입니다. 환경 설치 실패와 구분해 봅니다.

| 직접 확인할 것 | 파일 또는 실행 | 기대 변화 |
|---|---|---|
| 업무 정책 | `fixtures/checkout/requirements.md` | 할인 상한·배송비 기준·금액 입력 조건 |
| 수정할 Python | `output/day3-redesign/student-service/starter/checkout.py` | 학생 또는 Codex가 선택한 수정 |
| 같은 테스트 재실행 | `exercise --step test` | 실패 조건 감소 → 전체 통과 |
| 수정 참고 구현 | `fixtures/checkout/solution/checkout.py` | 금액 검증·할인 상한·할인 후 배송비 |
| 실제 리뷰 | `output/day3-redesign/student-service/review.md` | 파일·줄 번호·재현 조건·수정 제안 |
| 변경 코드 | `exercise --step diff --version solution` | 초안과 참고 구현의 diff |
| 웹 화면 | `python3 -m labs.day3.review_copilot.web --port 8765` | 결제 예정액·테스트·Codex 리뷰 |

```bash
# starter/checkout.py를 수정한 뒤
python3 -m labs.day3.review_copilot.cli exercise --step test
python3 -m labs.day3.review_copilot.cli exercise --step demo
# 참고 구현의 결과와 비교
python3 -m labs.day3.review_copilot.cli exercise --step test --version solution
python3 -m labs.day3.review_copilot.cli exercise --step demo --version solution
```

상품 10,000원·쿠폰 15,000원 입력은 초안에서 결제 예정액 -2,000원, 수정 참고 구현에서 3,000원입니다. 상품 50,000원·쿠폰 10,000원은 초안 40,000원, 수정 참고 구현 43,000원입니다. 두 번째 사례에서 배송비 정책은 **할인 후 상품 금액**을 기준으로 합니다. 실제 결제는 일어나지 않습니다.

`prepare`를 다시 실행해도 수정한 초안은 덮어쓰지 않습니다. Notebook의 별도 실습 폴더를 화면에서 쓰려면 `web --exercise-dir <Notebook에 표시된 경로> --port 8765`로 실행합니다.

## Notebook에서 호출할 함수

```python
from labs.day3.review_copilot.codex_cli import CodexCLIReviewProvider
from labs.day3.review_copilot.exercise import (
    prepare_exercise, run_exercise_tests, run_exercise_demo, review_exercise,
)

lab = prepare_exercise(workspace_root=ROOT)
before = run_exercise_tests(workspace_root=ROOT)
review = review_exercise(
    workspace_root=ROOT,
    provider=CodexCLIReviewProvider(live_opt_in=True),
    allow_fallback=False,
)
print(review["markdown"])
```

`review_exercise`는 실제 변경 코드와 정책, 테스트 출력만 Codex에 전달합니다. 임시 작업 폴더·read-only sandbox·shell tool 비활성화·사용자 config 제외를 사용합니다. 로그인 파일을 복사하거나 읽지 않으며 API Key를 자식 프로세스에 전달하지 않습니다. 모델 응답을 Pydantic으로 검사하고 실제 추가 라인에 연결한 뒤 Markdown 리뷰로 보여줍니다.

| 사용 경로 | 코드·테스트 실행 Role | Codex Role |
|---|---|---|
| Notebook·Localhost의 Adapter | Python 함수가 정해진 파일을 읽고 테스트 실행 | 전달받은 Context를 검토하고 리뷰 후보 생성 |
| Codex와 직접 나누는 대화 | Codex가 지정한 폴더에서 탐색·수정·테스트 도구 사용 | 상황에 따라 다음 작업을 선택하고 결과 확인 |

Notebook에서 작성한 Prompt는 `review_instructions=`에 전달하면 실제 Codex 요청에 반영됩니다. 화면의 `최근 리뷰 불러오기`는 저장된 실행 결과임을 표시하며 모델을 다시 호출하지 않습니다. 테스트 비교표는 실제 unittest 출력에서 각 테스트의 통과·실패를 추출합니다.

모델 연결이 안 되는 경우에는 `exercise --step review --provider fixture`로 수업용 예시를 확인합니다. Codex 실행 실패를 fixture 성공으로 조용히 바꾸지 않습니다. 주요 오류는 `CODEX_CLI_NOT_INSTALLED`, `CODEX_LOGIN_REQUIRED`, `CODEX_USAGE_LIMIT`, `CODEX_TIMEOUT`, `CODEX_OUTPUT_CONTRACT_INVALID`입니다.

## 내부 Workflow 모듈

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

이 모듈 진단 명령의 결과는 `output/course-labs/day3-v2/student-run/` 아래 JSON으로 저장됩니다. 기본 실행은 test를 실행하지 않고 사람 결정도 없으므로 `REVIEW_REQUIRED/HOLD`입니다. `--run-tests`는 고정된 focused test의 실제 exit code를 저장하며, Finding을 사람이 확인한 뒤 `--decision approve`를 추가합니다. 이 JSON은 처리 중간 상태를 확인하는 자료이며 실습의 최종 결과는 **수정된 Python 서비스·통과한 테스트·리뷰 Markdown·PR**입니다. 브라우저 demo는 `http://127.0.0.1:8765`에서 열립니다.

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

기존 Ollama adapter는 이전 자료의 재실행을 위해 남아 있습니다. 이번 3주차 주 실습에는 사용하지 않습니다. fixture 복구는 `--allow-fallback`을 추가했을 때에만 사용하며 실제 provider와 이유를 함께 표시합니다.

## 공식 참고

- [Codex 비대화형 실행](https://learn.chatgpt.com/docs/non-interactive-mode)
- [codex exec 명령 옵션](https://learn.chatgpt.com/docs/developer-commands#codex-exec)

2026-09-06 설치된 `codex-cli 0.151.0`에서 실제 실행을 확인했습니다. 설치 버전에 `--ignore-user-config`가 없으면 CLI를 업데이트한 뒤 다시 실행합니다.
