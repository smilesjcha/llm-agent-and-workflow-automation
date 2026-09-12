# 4주차 1~3차시 · GitHub PR 리뷰 실습

## 수업의 연결

3주차가 **코드를 읽고 근거 있는 리뷰 의견을 만드는 과정**이었다면, 4주차 전반부는 **그 의견을 올바른 PR·commit에 연결하고, 사람이 확인한 내용만 전달하는 과정**입니다. 후반부 Excel·Word·PPT 자동화에서도 같은 원칙을 적용합니다. 입력 확인 → 초안 → 계산·테스트 검증 → 사람 확인 → 전달.

| 차시 | 시간 | 이론 | 실제 코드 작업 | 화면과 파일 |
|---|---|---|---|---|
| 1차시 | 09:00–09:50 | PR과 commit SHA<br>diff의 변경 줄<br>API 읽기와 쓰기 | 합성 PR 읽기<br>저장소·번호·SHA 검사<br>잘못된 대상 차단 | `fixtures/pr.json`<br>`changes.diff`<br>`review.html` |
| 2차시 | 09:50–10:40 | 리뷰의 사용자 영향<br>사람의 확인 범위<br>초안과 게시의 차이 | Codex 리뷰 요청<br>결제 코드 직접 수정<br>Markdown·게시 내용 미리보기 | `checkout.py`<br>`test_checkout.py`<br>`review.md` |
| 3차시 | 10:40–11:30 | CI의 Role<br>최소 권한<br>중복·최신 버전 검사 | 실패 테스트→수정→통과<br>Actions YAML 구성<br>오래된 SHA·중복 리뷰 차단 | `templates/workflow.yml`<br>`publication_preview.json`<br>pytest 출력 |
| 쉬는 시간 | 11:30–12:00 | 3개 차시 후 30분 | — | — |
| 점심시간 | 12:00–13:00 | 2~5주차 공통 운영 | — | — |

온라인 개별 실습입니다. 짝 활동·발표는 필요하지 않습니다. 강사가 먼저 실행하고, 수강생은 같은 파일을 직접 수정하면서 따라옵니다. GitHub 로그인이 준비되지 않아도 필수 실습 전체가 로컬에서 실행됩니다.

## 준비물

| 구분 | 필수 여부 | 준비 내용 | 확인 |
|---|---|---|---|
| Python·VS Code | 필수 | Python 3.12 권장, Python/Jupyter 확장 | `python --version` |
| pytest | 필수 | 현재 Notebook 커널 또는 `.venv`에 설치 | `python -m pip install pytest==8.3.5` |
| 수업 코드 | 필수 | 저장소 루트에서 명령 실행 | `labs/day4/pr_review_lab/` 존재 |
| Codex | 선택 라이브 시연 | 기존 로그인 환경에서 코드·테스트 읽기 요청 | 리뷰 결과는 직접 확인, 무조건 신뢰하지 않음 |
| Git·GitHub CLI | 선택 연결 실습 | 개인 공개 연습 저장소, GitHub CLI 로그인 | `git --version`, `gh auth status` |
| 브라우저 | 필수 | HTML 파일 열기, 인터넷 없이 가능 | `output/day4-pr/review/review.html` |

Mac은 환경에 따라 `python` 대신 `python3`을 사용합니다. Notebook에서는 `%pip install pytest==8.3.5`로 **현재 커널**에 설치합니다. API key는 필요하지 않습니다. Codex를 실제 호출하는 선택 시연에는 개인 계정의 사용량·네트워크 조건이 적용됩니다.

## 실행 파일과 데이터

| 경로 | 역할 | 학생이 수정할 부분 |
|---|---|---|
| `labs/day4/pr_review_lab/service.py` | 검증·리뷰·승인·중복 검사 함수 | 심화 실습에서 함수와 테스트 함께 수정 |
| `labs/day4/pr_review_lab/fixtures/pr.json` | 교육용 합성 PR #42 | 원본 보존, Notebook에서는 deepcopy 후 변경 |
| `labs/day4/pr_review_lab/fixtures/findings.json` | 사람이 작성한 수업용 리뷰 예시 | 실제 Codex 출력으로 오해하지 않음 |
| `labs/day4/pr_review_lab/fixtures/checkout.py` | 쿠폰 기능의 의도적인 오류 | 직접 수정은 prepare로 복사한 파일에서 수행 |
| `labs/day4/pr_review_lab/fixtures/checkout_checks.py` | 5개 주문 테스트 | 실습 폴더에서는 `test_checkout.py`로 생성 |
| `labs/day4/pr_review_lab/review_policy.md` | 제품 규칙·리뷰 기준·Codex 요청 | 개인 서비스의 규칙으로 확장 가능 |
| `labs/day4/pr_review_lab/templates/workflow.yml` | 비활성 Actions 템플릿 | 개인 저장소에서 검토 후 직접 복사 |
| `labs/day4/pr_review_lab/templates/pull_request_template.md` | 목적·테스트·사람 확인 항목 | 개인 PR 설명에 활용 |

`training-example/checkout-demo#42`는 **실제 GitHub PR이 아닌 합성 데이터**입니다. URL·SHA는 연결 구조를 설명하기 위한 값입니다. 실존 고객·학생·회사 코드는 포함하지 않습니다. 로컬 수정 파일과 fixture의 원본 PR은 서로 다릅니다. 로컬 테스트 통과를 원본 PR의 GitHub CI 통과로 표시하지 않습니다.

## 1차시 · 대상 PR과 변경 코드

| 분 | 진행 | 강사 설명·시연 | 수강생 작업 | 확인 기준 |
|---:|---|---|---|---|
| 0–5 | 완성 결과 시연 | HTML 작업대에서 코드·테스트·리뷰를 함께 비교 | 최종 화면 확인 | JSON만 보는 실습이 아님 |
| 5–13 | PR 구조 | repo/number는 주소, SHA는 리뷰 기준 버전 | `pr.json`에서 3개 값 찾기 | PR 번호와 commit 구분 |
| 13–20 | diff 해석 | `-` 삭제, `+` 추가, RIGHT 줄 번호 | 6번째 줄의 새 계산식 찾기 | `position`과 파일 줄 번호 혼동 방지 |
| 20–32 | 코드 실행 | `load_fixture()`와 `validate_snapshot()` 한 함수씩 실행 | 정상 입력 검증 | 저장소·PR·URL·SHA 일치 |
| 32–43 | 실패 주입 | 잘못된 repo·번호·SHA를 각각 변경 | 오류 코드와 한국어 설명 확인 | `REPO_MISMATCH`, `INVALID_SHA` |
| 43–50 | 결과 연결 | `demo`로 diff·Markdown·HTML 생성 | 브라우저에서 파일 열기 | 실제 코드 파일과 화면 연결 |

```bash
python -m labs.day4.pr_review_lab prepare --out output/day4-pr/my-exercise
python -m labs.day4.pr_review_lab demo --exercise-dir output/day4-pr/my-exercise
```

이미 생성한 실습 폴더에는 덮어쓰지 않습니다. 재실행하려면 `my-exercise-2`처럼 새 폴더명을 사용합니다.

```python
from copy import deepcopy
from labs.day4.pr_review_lab import load_fixture, validate_snapshot, LabError

snapshot = load_fixture()
broken = deepcopy(snapshot)
broken["repo"] = "another/repository"
try:
    validate_snapshot(broken, expected_repo=snapshot["repo"], expected_pr=42)
except LabError as error:
    print(error.code, str(error))  # REPO_MISMATCH
```

강사 발화 예시: “AI가 의견을 잘 작성해도 다른 저장소에 남기면 사고입니다. 먼저 확인할 것은 문장력이 아니라 목적지와 코드 버전입니다.”

## 2차시 · 리뷰 초안과 결제 코드 수정

| 분 | 진행 | 강사 설명·시연 | 수강생 작업 | 확인 기준 |
|---:|---|---|---|---|
| 0–8 | 리뷰 품질 | 추상적인 ‘개선 필요’와 입력·영향이 있는 의견 비교 | 재현 입력을 계산 | 1,000−5,000 = −4,000 |
| 8–18 | Codex 요청 | 정책·코드·테스트를 주고 수정 전 설명 요청 | 기존 Codex 환경에서 같은 요청 또는 fixture 검토 | 모델 출력과 fixture 출처 구분 |
| 18–28 | 테스트 실행 | 5개 테스트 중 4개 실패 확인 | 직접 `check` 실행 | 정상 쿠폰 1개는 원래 통과 |
| 28–40 | 직접 수정 | 입력 검사와 `max(0, ...)` 최소 수정 | `checkout.py` 수정 | 제품 규칙을 코드로 표현 |
| 40–46 | 리뷰 문서 | 영향·재현·최소 수정·테스트 링크 확인 | `review.md` 읽기 | 취향 지적 대신 사용자 영향 |
| 46–50 | 사람 확인 | 승인할 대상과 내용 해시 비교 | 승인 전·후 preview 차이 확인 | 실제 GitHub 게시 없음 |

```bash
python -m labs.day4.pr_review_lab check --exercise-dir output/day4-pr/my-exercise
```

처음에는 **4 failed, 1 passed**가 정상 학습 출발점입니다. 수정 대상은 `output/day4-pr/my-exercise/checkout.py`입니다. 테스트 파일의 기대값을 바꿔서 통과시키지 않습니다.

Codex 요청 예시:

> `labs/day4/pr_review_lab/review_policy.md`와 내가 만든 실습 폴더의 checkout.py, test_checkout.py를 읽어 줘. 테스트가 실패하는 입력과 사용자 영향을 먼저 설명해 줘. 내가 확인하기 전에는 파일을 수정하거나 GitHub에 게시하지 마. 리뷰는 중요도·파일 줄·재현 조건·최소 수정·관련 테스트 순서로 써 줘.

수강생 직접 수정 후 선택 요청:

> 내가 수정한 checkout.py의 diff를 리뷰해 줘. 기존 정상 쿠폰 계산이 유지되는지, 잘못된 입력을 ValueError로 처리하는지, 테스트 기대값을 약하게 바꾸지 않았는지 확인해 줘. 코드가 간단하다는 이유만으로 새로운 추상화나 라이브러리를 추가하지 마.

```python
from labs.day4.pr_review_lab import build_review, approve_preview, preview_publication

review = build_review(snapshot)  # provider='fixture': 수업용 리뷰 예시
# review['markdown']을 직접 읽은 후에만 True로 선택합니다.
approval = approve_preview(snapshot, review, approved=True, reviewer="수강생")
preview = preview_publication(snapshot, review, approval,
                              current_head_sha=snapshot["head_sha"])
print(preview["status"])                   # PREVIEW_ONLY
print(preview["remote_write_performed"])  # False
```

강사 발화 예시: “승인은 ‘AI를 믿겠습니다’가 아닙니다. 이 저장소의 이 commit에, 내가 지금 읽은 이 내용을 쓰겠다는 좁은 선택입니다.”

## 3차시 · 테스트·CI·재실행 안전

| 분 | 진행 | 강사 설명·시연 | 수강생 작업 | 확인 기준 |
|---:|---|---|---|---|
| 0–10 | 수정 검증 | 같은 명령을 다시 실행 | 5 passed 확인, 잘못된 입력 한 가지 추가 | 코드 수정으로 통과 |
| 10–18 | CI 구조 | trigger→runner→install→pytest | YAML에서 각 단계 표시 | CI가 AI 리뷰와 다른 이유 |
| 18–30 | YAML 작성 | 비활성 템플릿을 개인 연습 파일로 복사 | 작업 경로·Python·pytest 수정 및 확인 | read-only, no secrets |
| 30–38 | 버전 변경 | review 이후 새 commit 시뮬레이션 | `STALE_HEAD_SHA` 확인 | 새 diff→새 리뷰→새 확인 필요 |
| 38–46 | 중복 재실행 | 동일 리뷰 표식이 있는 이력 입력 | `DUPLICATE_REVIEW` 확인 | 같은 내용을 두 번 보내지 않음 |
| 46–50 | 문서 자동화 연결 | 리뷰 결과를 문서화할 때 입력·검증·승인 재사용 | Excel 작업의 검증 기준 한 가지 선정 | ‘계산은 코드, 설명은 AI’ 연결 |

CLI에서 Markdown을 읽은 뒤에만 실행할 미리보기:

```bash
python -m labs.day4.pr_review_lab preview --approve --reviewer student
python -m labs.day4.pr_review_lab preview --approve --reviewer student --simulate-stale
python -m labs.day4.pr_review_lab preview --approve --reviewer student --simulate-duplicate
```

첫 번째는 `PREVIEW_ONLY`, 두 번째와 세 번째는 의도된 `BLOCKED`입니다. 예상된 차단도 성공적인 검증입니다. 실제 GitHub POST/자동 승인/merge는 구현하지 않았습니다.

### 개인 GitHub 저장소 연결 · 선택 확장

1. 본인 소유의 공개 연습 저장소를 사용합니다. 회사 저장소를 실습 대상으로 삼지 않습니다.
2. 저장소 루트의 `exercise/`에 수정한 `checkout.py`와 `test_checkout.py`를 둡니다.
3. `templates/workflow.yml`을 읽고 `.github/workflows/day4-checkout-tests.yml`로 직접 복사합니다. 원본 템플릿 위치에서는 자동 실행되지 않습니다.
4. `.github/pull_request_template.md`에는 제공한 PR 양식을 복사합니다.
5. `git status`와 `git diff`로 개인 데이터·키가 없는지 확인합니다. 본인 저장소에만 커밋·브랜치 push·PR을 직접 생성합니다.
6. PR의 Checks에서 `Run checkout tests`를 확인합니다. 실패를 만드는 코드를 잠시 추가한 뒤 고쳐서 재실행되는 흐름을 비교합니다.
7. 승인·merge는 사람이 결정합니다. 기본 실습 코드는 대신 게시하거나 merge하지 않습니다.

GitHub Actions를 실행할 수 없는 학습자는 같은 `python -m pytest -q test_checkout.py`를 로컬에서 실행하고 YAML까지 작성하면 필수 학습 목표를 완료합니다. Actions 사용 조건·한도는 개인 계정과 저장소 설정에 따라 확인합니다.

공개 PR을 읽는 별도 선택 코드:

```python
from labs.day4.pr_review_lab import fetch_public_pr

# 아래 YOUR_NAME/YOUR_REPO 및 PR 번호는 본인의 공개 연습 저장소로 변경합니다.
public_pr = fetch_public_pr("YOUR_NAME/YOUR_REPO", 1, allow_network=True)
```

이 함수는 `gh api --method GET --hostname github.com ...`만 사용합니다. 비공개 저장소 차단, 30개 이하 변경 파일, 최대 200KB diff, 리뷰 100개 미만이라는 실습 범위를 둡니다. 파일 누락·binary diff·읽는 동안 바뀐 SHA를 조용히 무시하지 않습니다. 받아온 PR 코드를 checkout하거나 실행하지 않습니다. 실제 공개 PR에는 `build_review(public_pr, findings=직접_검토한_의견, provider="human-reviewed")`처럼 별도 의견이 필요하며 합성 정답을 재사용하지 않습니다.

## 결과 확인

| 파일 | 눈으로 확인할 내용 |
|---|---|
| `output/day4-pr/review/review.html` | diff·현재 로컬 테스트·리뷰·게시 내용 미리보기 |
| `output/day4-pr/review/review.md` | 사람이 읽고 편집할 리뷰 문서 |
| `output/day4-pr/review/changes.diff` | 기준 PR의 코드 변경 |
| `output/day4-pr/review/test_result.txt` | 실제 실행한 로컬 pytest 출력 |
| `output/day4-pr/review/publication_preview.json` | commit_id·COMMENT·본문. 전송한 기록이 아님 |
| `output/day4-pr/my-exercise/checkout.py` | 학생이 수정한 실제 기능 코드 |
| `output/day4-pr/my-exercise/test_checkout.py` | 다음 변경 때도 재사용할 테스트 |

`preview`를 다시 실행하면 HTML의 테스트 영역은 다시 실행하지 않습니다. 최종 화면에 최신 테스트까지 넣으려면 Notebook의 `render_outputs(..., preview=preview, test_result=check_exercise(...))`를 사용합니다.

## Codex 실제 호출 선택

기본 Notebook은 `RUN_CODEX_LIVE=False`입니다. CLI 설치·로그인·계정 사용량을 확인한 뒤 직접 선택하면 수업용 공개 세 파일로 실제 리뷰를 요청할 수 있습니다.

```bash
python -m labs.day4.pr_review_lab.codex_review --live --output output/my-review.md
```

```python
from labs.day4.pr_review_lab.codex_review import run_codex_review

result = run_codex_review(ROOT, "output/my-review.md", live=True, model="gpt-5.6-sol")
print(result["path"])
```

- `--live` 또는 `live=True`가 없으면 `LIVE_NOT_REQUESTED`로 중단하며 모델을 호출하지 않습니다.
- adapter는 공개 `review_policy.md`, `fixtures/checkout.py`, `fixtures/checkout_checks.py`만 새 작업 폴더에 복사하고 그 폴더에서 CLI를 실행합니다.
- CLI는 `--ignore-user-config --ephemeral --sandbox read-only --skip-git-repo-check` 및 `--output-last-message`를 사용합니다. 사용자 설정을 불러오지 않지만 기존 CLI 인증을 사용합니다. read-only는 쓰기 제한이며 세 파일만 읽도록 강제하는 OS 격리와 같지 않습니다.
- stdout·stderr 계정 로그는 표시하거나 저장하지 않습니다. 최종 Markdown만 새 파일에 저장하고 기존 파일·범위 밖 경로는 차단합니다.
- timeout·로그인·모델 접근 실패는 이름 있는 오류로 반환하고 fixture 결과로 바꾸지 않습니다. 자동 재시도도 하지 않습니다.
- 줄 번호와 재현 입력을 사람이 다시 확인합니다. 원문을 자동으로 고쳐 모델이 처음부터 맞춘 것처럼 표시하지 않습니다. GitHub에 게시하지 않습니다.

[강사 실제 실행 및 줄 번호 오류 사례](Codex_실행사례_및_검증.md)에서 원문과 사람 검증의 차이를 확인할 수 있습니다. 학생이 선택해서 새로 호출한 결과와 강사의 이전 실행 기록은 다른 자료입니다.

공식 근거: [OpenAI Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [OpenAI CLI commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli). 상세 옵션은 2026-09-12 로컬 `codex exec --help`에서도 확인했습니다.

## API와 한계

| API | 입력 | 반환·주요 오류 |
|---|---|---|
| `validate_snapshot(snapshot, expected_repo=..., expected_pr=...)` | PR 대상·diff | 원본 snapshot / 대상·SHA·경로 오류 |
| `prepare_exercise(ROOT, "output/...")` | 새 하위 폴더 | edit_file / `EXERCISE_EXISTS` |
| `check_exercise(ROOT, path)` | prepare로 만든 로컬 파일 | PASSED/FAILED·출력 / timeout |
| `build_review(snapshot, findings=None, provider="fixture")` | 검증한 의견 | Markdown·내용 해시 / 변경 줄 불일치 |
| `approve_preview(..., approved=True, reviewer=...)` | 사람이 확인한 리뷰 | PR·SHA·내용 해시 결합 승인 |
| `preview_publication(..., current_head_sha=..., existing_reviews=...)` | 현재 버전·게시 이력 | PREVIEW_ONLY / stale·duplicate·approval mismatch |
| `render_outputs(ROOT, output, snapshot, review, preview=None, test_result=None)` | 위 결과 | Markdown·HTML·diff·JSON·테스트 파일 경로 |

이 실습은 **원격 게시 이전의 안전 계약**을 학습하는 것입니다. 실제 게시 서비스로 확장할 때는 직전 GitHub 재조회, 서버 측 승인 인증·만료, 중복 작업 직렬화, 네트워크 불확실 응답 후 이력 재조회가 추가로 필요합니다. 현재 승인 객체는 암호학적으로 서명된 인증 수단이 아닙니다. 두 프로세스가 동시에 POST하는 상황을 원자적으로 막는 서비스도 아닙니다. preview 생성 이후 새 commit이 생길 수 있으므로, 미리보기를 그대로 나중에 자동 전송하는 방식은 사용하지 않습니다.

## 공식 자료

2026-09-12 확인. 제품 설명을 다시 보는 시간이 아니라, 수업 코드의 설계 근거입니다.

- [GitHub REST · Pull requests](https://docs.github.com/en/rest/pulls/pulls): 대상 PR·head SHA·변경 파일 읽기, diff 수집의 근거.
- [GitHub REST · Pull request reviews](https://docs.github.com/en/rest/pulls/reviews): 리뷰의 `commit_id`, `body`, `event=COMMENT` 및 쓰기 권한. API를 호출하면 알림이 발생할 수 있으므로 기본 실습은 payload만 준비.
- [GitHub Actions · Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax): trigger·job·step·permissions·concurrency 구성.
- [GitHub Actions · Secure use](https://docs.github.com/en/actions/reference/security/secure-use): 최소 권한, untrusted PR 코드와 privileged workflow의 분리, Action을 전체 commit SHA로 고정하는 기준.
- [GitHub CLI · gh api](https://cli.github.com/manual/gh_api): `--method GET`과 `--hostname`을 명시한 읽기 adapter.

## 강사용 검증 명령

```bash
python -m pytest -q tests/test_day4_pr_review_lab.py
python -m pytest -q tests/test_day1_agent.py tests/test_langchain_langgraph_lab.py tests/test_meeting_agent_workflow.py tests/test_openai_provider.py tests/test_ollama_tool_agent.py
```

테스트는 네트워크·유료 모델을 호출하지 않습니다. GitHub 읽기는 fake runner로 검증하고, 학생 수정 과정은 임시 폴더의 실제 pytest로 **4 failed/1 passed → 5 passed**를 확인합니다. 현재 원격 PR 생성·리뷰 게시·merge는 수행하지 않았습니다.
