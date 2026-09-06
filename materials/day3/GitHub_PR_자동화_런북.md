# 코드 리뷰 Agent · GitHub 연결 런북

3주차의 목표는 주문 오류를 실제로 수정하고 검증한 코드를 준비하는 것이다. 아래 GitHub 단계는 3주차 마지막에 전체 흐름을 보여주고 **4주차의 6개 차시**에서 자세히 구현한다. 로컬 리뷰에 사용하는 Codex CLI와 GitHub에서 실행하는 CI·리뷰 기능을 구분한다.

강의 원본을 새로 받을 때는 `git clone --branch codex/day3-review-intelligence https://github.com/smilesjcha/llm-agent-and-workflow-automation.git`를 사용한다. 개편본은 이 branch에 있으며 main의 이전 버전과 다르다. 자신의 변경이 있는 폴더는 보존하고 다른 새 폴더에 받는다. clone 없이 시작하는 학생은 코드 ZIP을 사용하되, 이 런북의 Git 명령을 실행하기 전에는 Git을 설치한다.

## 연결 구조

```text
주문 코드 + Test
  → 개인 Branch → Commit → Draft PR
  → GitHub Actions Test
  → PR diff 수집 → Local Codex CLI 리뷰
  → 파일·줄·commit SHA 확인
  → 사람이 게시할 리뷰 선택 → 교육용 PR 댓글
  → 수정 commit → 같은 Test → 사람의 Merge 판단
```

| 구성요소 | 이번 역할 | 시점 |
|---|---|---|
| Local Codex CLI | PC에서 로그인된 계정으로 리뷰·코딩 요청 | 3주차 |
| Python Adapter | CLI 호출·응답 검사·실패 처리 | 3주차 |
| GitHub API | PR·파일·Diff 읽기, 선택한 댓글 게시 | 4주차 |
| GitHub Actions | PR이 바뀔 때 실제 Test 실행 | 4주차 |
| Codex GitHub Review | 연결된 저장소에서 `@codex review` 요청 | 설정된 계정의 선택 경로 |

로컬 로그인 자격증명을 GitHub Actions로 복사하지 않는다. Actions의 선택 AI 리뷰가 별도 인증을 필요로 하면 그 서비스의 공식 설정을 따른다. 학생의 기본 흐름은 GitHub CI와 PC의 Local Codex CLI를 연결한다.

## 1. 이번 코드의 분리

Notebook의 `EXERCISE` 변수는 학생이 수정한 폴더다. 3주차의 출력 폴더 전체를 commit하지 않는다. 아래 셀을 **원하는 교육용 저장소 안에서** 실행해 서비스 코드 두 파일만 준비한다. 폴더가 이미 있으면 멈추므로 학생 수정본을 덮어쓰지 않는다.

```python
from pathlib import Path
import shutil

service_dir = ROOT / "my-review-service"
service_dir.mkdir(exist_ok=False)
for name in ("checkout.py", "checkout_checks.py"):
    shutil.copyfile(EXERCISE / "starter" / name, service_dir / name)
print(service_dir)
```

새 개인 저장소로 내보내는 경우에는 별도 준비 셀에서 `service_dir = Path("본인 저장소의 실제 경로") / "my-review-service"`로 목적지를 지정한다. 수업 Notebook의 `ROOT`는 바꾸지 않고, `EXERCISE`는 Notebook이 출력한 기존 실습 폴더를 그대로 사용한다. 실제 환경 파일·인증정보·회사 데이터는 복사하지 않는다.

## 2. 변경 시작점

```bash
git status --short
git branch --show-current
git remote -v
```

현재 수정사항이 있으면 먼저 어떤 작업인지 확인한다. 공용 저장소에 직접 실습 변경을 올리기보다 본인 교육용 저장소 또는 Fork에서 진행한다. `origin`이 본인의 대상 저장소인지 확인한다.

처음에는 강의 저장소를 Fork한 개인 저장소를 권장한다. 새 개인 저장소를 만들면 GitHub에서 README로 초기화해 기준 branch와 첫 commit을 만든 뒤 clone한다. commit이 하나도 없는 빈 저장소는 비교할 기준이 없어 아래 Draft PR 단계를 바로 진행할 수 없다.

```bash
git switch -c codex/my-review-service
python my-review-service/checkout_checks.py
```

기대 결과는 9개 Test 통과다. 이번 서비스의 Test는 표준 라이브러리 unittest를 사용하므로 다른 과정의 전체 패키지를 설치하지 않고도 실행할 수 있다.

## 3. Codex 대화형 리뷰

저장소 폴더에서 `codex`를 실행하고 다음 요청을 입력한다.

```text
my-review-service/checkout.py와 checkout_checks.py를 읽어줘.
이 서비스는 원 단위 정수만 받고 음수 입력을 막아야 해.
쿠폰은 상품 금액까지만 적용하고 무료 배송은 할인 후 50,000원 이상이 기준이야.
우선 코드를 바꾸지 말고 실제 오류가 있는지 리뷰해줘.
각 지적은 파일·줄·재현 입력·영향·최소 수정 제안으로 적어줘.
실행하지 않은 Test를 통과했다고 쓰지 마.
```

수정할 항목을 확인한 뒤 이어서 요청한다.

```text
선택한 오류 한 가지를 고쳐줘.
수정 범위는 checkout.py와 관련 Test로 제한해줘.
정상 입력과 해당 오류 입력의 Test를 먼저 확인하고 수정 후 다시 실행해줘.
마지막에 변경 Diff와 실제 실행 결과를 보여줘.
```

대화형 Codex는 허용된 범위에서 파일 읽기·수정·Test 도구를 사용할 수 있다. Notebook의 `CodexCLIReviewProvider`는 도구를 끄고 제공된 Context만 분석하므로 역할이 다르다.

## 4. Commit

```bash
git diff -- my-review-service
git add my-review-service/checkout.py my-review-service/checkout_checks.py
git diff --cached --check
git diff --cached
git commit -m "feat: add tested checkout service"
git show --stat --oneline HEAD
```

실제 수정과 Test를 같은 목표의 commit으로 남긴다. 파일명이 현재 존재하는지 확인하고 명시적으로 stage한다.

## 5. 자동 Test

본인 저장소의 `.github/workflows/checkout-tests.yml`에 다음 내용을 넣는다. 프로젝트를 생성하는 실습이므로 파일 생성·내용 입력·실제 PR 실행까지 확인한다.

```yaml
name: checkout-tests
on:
  pull_request:
    paths:
      - 'my-review-service/**'
      - '.github/workflows/checkout-tests.yml'
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python my-review-service/checkout_checks.py
```

강의 저장소에는 전체 회귀 검사 `.github/workflows/test.yml`과 PR 본문 검사 `.github/workflows/day3-pr-quality.yml`이 별도로 있다. 개인 작은 서비스용 위 예제와 검사 범위를 구분한다. GitHub Actions 버전·계정 사용 범위는 실행 시 공식 문서와 조직 정책을 확인한다.

```bash
git add .github/workflows/checkout-tests.yml
git commit -m "ci: test checkout changes on pull requests"
git push -u origin HEAD
```

## 6. Draft PR

GitHub CLI가 준비된 경우:

```bash
gh auth status
gh pr create --draft --title "주문 쿠폰·배송비 계산 검증" --body-file my-review-service/PR.md
```

명령 전에 `my-review-service/PR.md`를 만들고 실제 내용을 작성한다. GitHub CLI가 없으면 웹의 Compare & pull request에서 Draft PR을 만든다.

본문에는 목표·변경 파일·실제 Test 명령과 결과·리뷰 초점을 적는다.

```markdown
## Goal
쿠폰이 상품 금액을 넘는 입력과 할인 후 무료 배송 기준을 정확하게 처리한다.

## Scope
my-review-service/checkout.py, checkout_checks.py

## Test evidence
python my-review-service/checkout_checks.py
실행 결과: 본인이 실제 확인한 내용을 입력

## Review focus
쿠폰 상한·정수/음수 입력·배송비 경계값·누락된 Test
```

강의 저장소의 PR 계약을 사용하는 경우에는 아래처럼 **템플릿의 복사본**을 만든다. 원본 템플릿을 PR 본문으로 바로 게시하지 않는다. 일반 clone의 `.git` 폴더에 둔 작성본은 commit에 포함되지 않는다. 같은 작성본이 이미 있으면 내용을 보존하고 다른 이름을 사용한다.

```bash
cp .github/pull_request_template.md .git/day3-pr-body.md
# VS Code에서 .git/day3-pr-body.md를 열어 Goal·범위·실제 Test 결과·리뷰 초점을 작성
# 안내용 문구와 체크 항목을 실제 확인 내용으로 바꾼 뒤 파일을 다시 읽어 검토
gh pr create --draft --title "주문 쿠폰·배송비 계산 검증" --body-file .git/day3-pr-body.md
```

Windows PowerShell에서는 첫 줄 대신 `Copy-Item .github/pull_request_template.md .git/day3-pr-body.md`를 사용한다. 이 템플릿 복사 경로를 선택하면 앞의 `my-review-service/PR.md` 방식은 중복 실행하지 않는다. 본문의 Test 결과는 실제 명령을 실행한 뒤 기록하며, 미리 적힌 PASS를 복사하지 않는다.

## 7. PR 읽기·댓글·재시도

4주차는 다음 기능을 Python으로 하나씩 만든다. 이 문서의 목록만 읽는 것으로 실습을 완료하지 않는다.

| 순서 | 구현 기능 | 직접 검증할 조건 |
|---|---|---|
| 1 | 본인 교육용 PR 읽기 | 없는 PR·읽기 권한 오류 |
| 2 | 변경 파일·Diff 수집 | Pagination·Diff 없는 파일 |
| 3 | Finding 위치 매핑 | 추가 줄·삭제 줄·오래된 commit SHA |
| 4 | 댓글 본문 미리보기 | 정확한 파일·줄·재현 근거 |
| 5 | 사람 선택 후 게시 | 선택하지 않은 리뷰 미게시 |
| 6 | 중복 요청 방지 | 같은 PR/SHA/Finding 두 번 요청 |
| 7 | 제한된 재시도 | Timeout·429·권한 오류 구분 |
| 8 | 수정 commit 이후 재검사 | 이전 리뷰와 새로운 변경의 관계 |

동일 PR·commit SHA·Finding으로 안정적인 식별값을 만들고, 같은 댓글을 재게시하지 않는지 교육용 저장소에서 직접 확인한다. 필요 이상의 GitHub 권한을 부여하지 않는다.

## 8. 선택 Codex GitHub Review

Codex GitHub Review가 연결된 저장소에서는 PR 댓글에 `@codex review`로 검토를 요청할 수 있다. 로컬 CLI에 로그인한 것만으로 해당 GitHub 연결이 자동 설정되는 것은 아니다. [공식 GitHub Review 안내](https://developers.openai.com/codex/integrations/github/)를 따른다.

기존 `.github/workflows/day3-codex-review-optional.yml`은 별도 opt-in을 요구하는 선택 기능이다. 기본 수업은 이 Action의 API 인증에 의존하지 않는다. CI Test·Local Codex 리뷰·사람의 판단만으로 핵심 흐름을 완료할 수 있다.

## 9. 리뷰 반영

1. 지적한 코드 위치와 재현 조건 확인
2. 실제 Test로 오류 재현
3. 최소 범위 수정
4. 같은 Test와 회귀 Test 실행
5. 수정 commit·push
6. PR Checks·리뷰 결과 확인

자동 Merge는 사용하지 않는다. 통과한 CI와 AI 리뷰는 판단 근거이며, 최종 코드와 대상 branch를 사람이 확인한다. 수정이 잘못되면 일반적인 새 revert commit으로 이력을 남기는 방법을 다룬다. 공유 이력을 강제로 덮어쓰는 명령을 수업 기본 절차로 쓰지 않는다.
