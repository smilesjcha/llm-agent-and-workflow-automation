# 3일차 · GitHub PR·CI·Codex Review

로컬에서 검증한 작은 코드 변경을 branch·commit·Draft PR로 남기고, GitHub Actions와 사람 리뷰를 통과시키는 50분 연결 실습이다. 필수 경로는 무료 GitHub 기능만 사용한다. Codex 리뷰는 계정 연결 또는 API 사용을 명시적으로 선택한 경우에만 진행한다.

## 완료 결과

| 결과 | 확인 위치 | 완료 기준 |
|---|---|---|
| 기능 branch | local Git | `main`이 아닌 개인 branch |
| focused commit | `git show --stat` | 코드·test·문서가 한 목표만 설명 |
| Draft PR | GitHub Pull requests | Goal·Scope·실행 결과·검토 초점 작성 |
| 자동 CI | PR Checks | `course-tests`, `day3-pr-quality` 결과 확인 |
| 사람 리뷰 | Reviewers | CODEOWNER 또는 강사의 승인·수정 요청 |
| 선택 AI 리뷰 | Codex 또는 Actions artifact | 발견 사항을 사람이 재현한 기록 |
| 최종 판단 | Human merge checklist | 자동 merge 없이 사람이 diff와 대상 branch 확인 |

## 두 가지 진행 경로

| 구분 | 필수·무료 경로 | 선택 Codex 경로 |
|---|---|---|
| 인증 | GitHub 로그인 | Codex Cloud 연결 또는 `OPENAI_API_KEY` repository secret |
| 실행 | PR 생성 시 GitHub Actions 자동 실행 | `@codex review` 또는 수동 workflow 실행 |
| 권한 | `contents: read` | 읽기 전용 checkout·`sandbox: read-only` |
| 결과 | PR의 Checks | GitHub review 또는 7일 보관 artifact |
| GitHub 상태 변경 | 학생이 직접 push·PR 생성 | 제공 workflow는 PR comment·commit·merge 금지 |
| 비용 | public repository와 계정 정책 범위의 GitHub 기본 기능 | 계정·API 사용 조건과 비용 확인 후 opt-in |

Codex의 GitHub Code Review는 연결된 repository에서 PR comment의 `@codex review`로 요청할 수 있고, 적용 범위의 `AGENTS.md` 규칙을 읽는다. 공식 절차는 [OpenAI Codex GitHub Review](https://learn.chatgpt.com/docs/third-party/github), GitHub Action 입력과 권한 경계는 [OpenAI Codex GitHub Action](https://learn.chatgpt.com/docs/github-action)을 따른다.

## 강사 1회 설정

실습 PR보다 먼저 아래 설정 파일을 `main`에 반영한다. 새 workflow와 CODEOWNERS는 base branch에 있어야 이후 학생 PR에서 일관되게 동작한다.

| 파일 | 역할 | GitHub 변경 권한 |
|---|---|---|
| `.github/CODEOWNERS` | 검토 가능한 PR에서 `@smilesjcha` 사람 reviewer 요청 | 없음 |
| `.github/pull_request_template.md` | 목표·범위·test·검토 초점 입력 | 없음 |
| `.github/workflows/day3-pr-quality.yml` | PR contract·민감 경로·공백 검사 | `contents: read` |
| `.github/workflows/test.yml` | 전체 Python·Go 회귀 test | `contents: read` |
| `.github/workflows/day3-codex-review-optional.yml` | 수동·읽기 전용 Codex 검토 | `contents: read` |

첫 `day3-pr-quality` 실행이 성공한 뒤 GitHub의 default branch ruleset에 다음 기준을 연결한다.

1. `main` 직접 push 대신 Pull Request 사용
2. 사람 approval 1명 이상
3. required status checks에 첫 실행 화면의 `course-tests / pytest`, `day3-pr-quality / pr-contract` 지정
4. 가능하면 code owner review와 stale approval 해제 사용
5. force push·branch deletion·자동 merge 비활성화

메뉴와 사용 가능 범위는 repository 유형·조직 정책에 따라 다를 수 있다. CODEOWNERS 기준은 [GitHub Code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), branch 정책은 [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)에서 확인한다.

## 수업 전 준비

### 공통

```bash
git --version
python3 --version
git remote -v
git status --short
```

- GitHub에 로그인 가능한 browser
- 이 repository를 clone한 폴더
- Python 3.12 권장
- 본인 또는 강사가 소유한 교육용 repository의 push 권한
- 실제 고객 정보·사내 회의록·token이 없는 synthetic data

### 선택

```bash
gh --version
gh auth status
```

`gh`가 없으면 GitHub 웹 화면에서 PR을 만든다. 인증 결과 화면에 token 값을 출력하거나 캡처하지 않는다.

## 50분 진행표

| 시간 | 구분 | 강사 화면 | 수강생 작업 | 확인 결과 |
|---:|---|---|---|---|
| 0~5분 | 강의 | branch→PR→CI→review→human merge 전체 흐름 | 결과 화면 관찰 | 오늘의 완료 상태 이해 |
| 5~12분 | 환경 실습 | `git status`, remote, Python 확인 | 본인 환경 진단 | 작업 시작점 확인 |
| 12~22분 | 코드 실습 | 작은 정책 변경과 허용·차단 test | 코드와 test 한 쌍 수정 | focused test 통과 |
| 22~30분 | Git 실습 | diff 검토·선택적 stage·commit | branch와 commit 생성 | 예상 파일만 commit |
| 30~38분 | GitHub 실습 | Draft PR·PR 본문 작성 | push 후 Draft PR 생성 | PR contract PASS |
| 38~45분 | CI·Review 실습 | 실패 원인→최소 수정→재실행 | Checks와 review 확인 | green 또는 원인 기록 |
| 45~50분 | Human gate | merge checklist와 rollback | 수정 계획·Exit Ticket | merge 여부를 사람이 결정 |

## 1. 작업 시작점 고정

현재 작업을 덮어쓰지 않는다. 출력이 있으면 먼저 강사에게 확인한다.

```bash
git status --short
git branch --show-current
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/day3-pr-guard-본인이니셜
```

교육장에서 공용 repository push 권한이 없으면 GitHub의 Fork를 만든 뒤 fork를 `origin`, 강사 repository를 `upstream`으로 둔다.

```bash
git remote -v
git remote add upstream https://github.com/smilesjcha/llm-agent-and-workflow-automation.git
git fetch upstream
```

## 2. 코드 변경과 test

기본 과제는 “민감 파일 확장자 하나를 PR guard에 추가하고 허용·차단 test를 함께 추가”이다. 구현 전 다음 범위를 Codex에 전달할 수 있다.

```text
목표: scripts/day3_pr_guard.py의 민감 경로 정책에 강사가 지정한 확장자 하나를 추가한다.
허용 경로: scripts/day3_pr_guard.py, tests/test_day3_pr_guard.py
필수 test: 허용 가능한 sample 경로 1개, 차단할 secret 경로 1개
금지: 실제 secret 생성·읽기, GitHub API 호출, 기존 assertion 약화, 자동 commit·push·merge
완료 조건: focused test와 git diff --check 통과, diff를 사람이 확인
```

실행한다.

```bash
python3 -m pytest -q tests/test_day3_pr_guard.py
python3 -m pytest -q
git diff --check
```

실패는 지우지 말고 “명령·exit code·핵심 오류·수정” 네 항목으로 기록한다. AI가 말한 `passed`가 아니라 터미널에서 실제로 본 결과만 PR에 적는다.

## 3. diff와 commit

```bash
git diff -- scripts/day3_pr_guard.py tests/test_day3_pr_guard.py
git status --short
git add scripts/day3_pr_guard.py tests/test_day3_pr_guard.py
git diff --cached --check
git diff --cached --stat
git commit -m "test: extend day3 PR secret-path guard"
git show --stat --oneline HEAD
```

`git add .` 대신 허용한 파일만 stage한다. `.env`, credential, 실제 회의 파일이 보이면 commit을 중단한다.

## 4. push와 Draft PR

여기부터 원격 상태를 바꾸므로 본인 branch와 remote를 다시 확인한다.

```bash
git remote -v
git branch --show-current
git push -u origin HEAD
```

GitHub CLI 선택 경로:

```bash
cp .github/pull_request_template.md .git/day3-pr-body.md
# VS Code에서 .git/day3-pr-body.md의 안내문을 실제 실행 결과로 교체
gh pr create --draft \
  --title "test: extend Day 3 PR guard" \
  --body-file .git/day3-pr-body.md
```

Windows PowerShell에서는 첫 줄 대신 `Copy-Item .github/pull_request_template.md .git/day3-pr-body.md`를 사용한다. `.git/day3-pr-body.md`는 commit 대상이 아니며, 원본 template를 그대로 PR 본문에 게시하지 않는다.

웹 경로에서는 repository의 `Compare & pull request`를 누르고 `Create draft pull request`를 선택한다. 템플릿의 HTML 안내문을 답으로 남기지 말고 다음을 직접 채운다.

- Goal: 바뀌는 동작 한 가지
- Changed files / Intentionally unchanged: 변경 범위와 제외 범위
- Safety and data: 직접 확인한 세 항목
- Result: 실행한 명령의 실제 test 결과
- Risk to inspect: 리뷰어가 가장 먼저 볼 경계

Draft PR을 `Ready for review`로 전환하면 `.github/CODEOWNERS`가 저장소 소유자를 사람 reviewer로 요청한다. 다른 repository로 옮길 때는 `@smilesjcha`를 실제 강사 또는 팀 계정으로 바꾼다.

## 5. 자동 CI 읽기

PR의 Checks에서 역할을 구분한다.

| Check | 역할 | 실패 시 첫 확인 |
|---|---|---|
| `course-tests` | 전체 Python·Go 회귀 test | 첫 실패 test와 변경 코드의 관계 |
| `day3-pr-quality` | PR 본문·안전 확인·민감 경로·공백 | 출력된 안정적 error code |

`day3-pr-quality`의 대표 복구:

| error code | 의미 | 수정 |
|---|---|---|
| `PR_GOAL_REQUIRED` | Goal이 비어 있음 | 변경 동작 한 문장 작성 |
| `PR_SAFETY_ATTESTATION_REQUIRED` | 안전 항목 미확인 | 실제 확인 후 세 항목 체크 |
| `PR_TEST_RESULT_REQUIRED` | test 결과가 없음 | local 명령 재실행 후 실제 결과 기록 |
| `PR_REVIEW_FOCUS_REQUIRED` | 리뷰 초점이 없음 | 가장 위험한 조건 한 가지 작성 |
| `SENSITIVE_PATH_CHANGED` | secret 가능 파일이 diff에 포함 | 해당 파일을 commit에서 제거·key 교체 검토 |

CI를 다시 돌리기 위해 빈 commit을 만들지 않는다. PR 본문 오류는 본문을 수정하고, 코드 오류는 최소 수정 commit을 push한다.

## 6. Codex review 선택 경로

### 경로 A · Codex Cloud가 연결된 repository

PR comment에 정확히 입력한다.

```text
@codex review
```

한 번만 초점을 좁힐 수도 있다.

```text
@codex review for regressions in the sensitive-path policy and missing boundary tests
```

연결·권한이 없으면 필수 실습 실패가 아니다. 사람 reviewer와 무료 CI 결과로 계속 진행한다.

### 경로 B · API 기반 수동 GitHub Action

repository Settings에서 다음 두 값을 강사가 직접 설정한 경우에만 사용한다.

- Actions variable: `ENABLE_CODEX_REVIEW=true`
- Actions secret: `OPENAI_API_KEY=<실제 값>`

실제 key는 repository 파일, `.env.sample`, Notebook, screenshot에 넣지 않는다. Actions의 `day3-codex-review-optional`을 default branch에서 `Run workflow`로 열고 PR 번호와 비용 확인을 입력한다. 제공 workflow는 다음 경계를 고정한다.

- 수동 `workflow_dispatch`만 허용
- workflow 실행 ref는 default branch만 허용
- repository opt-in variable과 비용 확인 모두 필요
- `contents: read`, `sandbox: read-only`
- 검토 대상은 PR merge ref, 검토 prompt는 default branch에서 `$RUNNER_TEMP`로 별도 추출
- PR이 바꾼 prompt 파일은 실행 지시로 사용하지 않음
- commit·push·PR comment·merge 권한 없음
- 결과는 `codex-review-pr-<번호>` artifact로 7일만 보관

## 7. 리뷰 반영과 사람 판단

리뷰마다 다음 네 질문을 답한다.

1. 변경된 line에서 실제 재현되는가?
2. 사용자 영향 또는 권한 위험이 있는가?
3. 기존 test가 놓친 실패 조건은 무엇인가?
4. 가장 작은 수정과 회귀 test는 무엇인가?

수정했다면 같은 branch에 새 commit으로 남긴다.

```bash
python3 -m pytest -q tests/test_day3_pr_guard.py
git diff --check
git add scripts/day3_pr_guard.py tests/test_day3_pr_guard.py
git commit -m "fix: address PR guard review finding"
git push
```

AI 리뷰, CI green, 사람 approval은 서로 다른 증거다. 모두 통과해도 merge 대상과 최종 diff는 사람이 확인하며 자동 merge는 사용하지 않는다.

## 8. 복구

merge 전에는 branch에서 수정 commit을 추가한다. 이미 merge한 commit을 되돌려야 할 때는 기록을 보존하는 `revert`를 사용한다.

```bash
git log --oneline -5
git revert <되돌릴-commit-sha>
python3 -m pytest -q tests/test_day3_pr_guard.py
git push
```

공용 branch를 `reset --hard` 또는 force push로 되돌리지 않는다.

## 강사용 시연 순서

1. 완성된 PR의 Checks·review·commit 세 화면을 2분 이내로 먼저 보여준다.
2. 안전 항목을 하나 비운 PR body fixture로 `PR_SAFETY_ATTESTATION_REQUIRED`를 재현한다.
3. `.env.sample`은 통과하고 `.env` 경로는 차단되는 focused test를 실행한다.
4. Draft PR을 만들고 두 Actions의 목적 차이를 설명한다.
5. 사람 리뷰 또는 Codex 결과 중 한 finding만 골라 재현→test 추가→수정한다.
6. Human merge checklist에서 자동화가 대신하지 못하는 결정을 확인한다.

## 수강생 Exit Ticket

```text
PR URL:
변경 목표 한 문장:
실행한 test와 결과:
CI가 확인한 것:
사람이 확인해야 할 것:
리뷰 finding을 수용/보류한 근거:
rollback 방법:
```
