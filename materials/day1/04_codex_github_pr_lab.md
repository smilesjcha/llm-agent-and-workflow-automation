# 1일차 4차시 · Codex와 GitHub PR 실습 가이드

## 이 실습의 목표

Codex에게 코드를 맡기는 것이 목표가 아니다. 작은 요구사항을 파일로 제한하고, 생성된 diff와 unit test를 확인한 뒤, Draft PR과 리뷰 기록을 사람이 최종 판단하는 흐름을 경험한다.

## 강의와 실습 구분

| 시간 | 구분 | 강사 화면 | 수강생 행동 | 완료 증거 |
|---|---|---|---|---|
| 12:00-12:10 | 강의 | Python·VS Code·Git·GitHub·Codex 역할 설명 | 화면을 보고 내 환경 상태 표시 | 준비 상태표 |
| 12:10-12:25 | 강사 시연 | venv→interpreter→branch→Codex 작업 계약→pytest→Draft PR | 명령과 화면 순서 체크 | 따라하기 순서 |
| 12:25-12:37 | 필수 개인 실습 | 막힌 지점 지원 | venv·interpreter·Git 상태 확인 | 버전·경로 |
| 12:37-12:45 | 선택 개인 실습 | sandbox repo 지원 | Codex로 test 1건 작성, diff·pytest 확인 | local diff 또는 commit |
| 12:45-12:50 | 확인 | 성공·fallback 화면 비교 | Draft PR 또는 local diff 저장 | 다음 차시 복구 지점 |

GitHub 로그인, push 권한, GitHub CLI가 없는 수강생은 PR을 만들지 않아도 된다. local branch, diff, test 결과까지 남기면 같은 학습 목표를 달성한 것으로 본다.

## 사용할 파일

| 파일 | 역할 | 실습에서 볼 내용 |
|---|---|---|
| src/day1_agent.py | 안전한 Tool 실행 코드 | workspace 경계·확장자 allowlist·오류 코드 |
| tests/test_day1_agent.py | 자동 검증 | 정상·실패·경계 unit test |
| data/meeting_sample_ko.txt | 빠른 fixture | 파일 읽기 정상 입력 |
| data/meeting_sample_ko_12min.txt | 상세 PBL 입력 | 실제 같은 회의 맥락·정정·모호성 |
| AGENTS.md | Codex 저장소 지침 | 안전 경계·test·Clean Code·Review Rules |
| .github/pull_request_template.md | PR 완료조건 | 목표·범위·위험·test·사람 확인 |
| .github/workflows/test.yml | 결정론적 자동검사 | PR마다 pytest·diff check |

## 강사 사전 점검

~~~bash
python3 --version
git --version
git status --short
git remote -v
python3 -m pytest -q
~~~

추가로 확인할 항목:

- 교육용 sandbox GitHub repository를 사용한다.
- 회사 저장소·고객 데이터·개인 token 화면을 사용하지 않는다.
- main branch에 직접 push하지 않는다.
- GitHub CLI를 쓸 경우 gh auth status를 먼저 확인한다.
- Codex GitHub Code Review는 연결된 repository와 권한이 있을 때만 시연한다.

## 필수 경로 · 모든 수강생

### 1. 같은 Python을 보고 있는지 확인

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-day1.txt
python -c "import sys; print(sys.executable)"
~~~

Windows PowerShell:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-day1.txt
python -c "import sys; print(sys.executable)"
~~~

VS Code의 Python Interpreter와 Notebook Kernel이 위 경로와 같아야 한다.

### 2. 변경 전 상태 확인

~~~bash
git status --short
git diff --check
python3 -m pytest -q
~~~

예상 결과는 10 passed다. 실패하면 새 기능을 만들기 전에 첫 오류 한 줄부터 복구한다.

### 3. 교육용 branch 생성

~~~bash
git switch -c test/reject-python-file
~~~

이미 같은 branch가 있으면 새 이름을 사용한다. main에서 직접 수정하지 않는다.

## Codex 연결 실습

Codex에 아래 작업 계약을 그대로 준다.

~~~text
Objective: .py 파일 읽기가 차단되는 것을 증명하는 unit test 1건을 추가해줘.
Scope: tests/test_day1_agent.py만 수정.
Do not: src/day1_agent.py 동작, 기존 test, error_code를 변경하지 말 것.
Verify: python3 -m pytest -q
Deliver: 변경 diff, 추가한 test가 필요한 이유, 실행 명령과 결과.
~~~

Codex가 답하면 바로 commit하지 않고 다음을 확인한다.

1. 허용한 파일 한 개만 바뀌었는가?
2. test 이름이 기대 동작을 설명하는가?
3. 실제로 .py 경로를 넣고 POLICY_BLOCKED를 확인하는가?
4. 기존 test를 삭제하거나 assertion을 약하게 만들지 않았는가?
5. 전체 test가 통과하는가?

~~~bash
git status --short
git diff -- tests/test_day1_agent.py
python3 -m pytest -q
git diff --check
~~~

## Commit과 Draft PR

~~~bash
git add tests/test_day1_agent.py
git diff --cached
git commit -m "test: reject python file reads"
git push -u origin HEAD
~~~

GitHub CLI가 준비된 경우:

~~~bash
gh pr create --draft --fill
~~~

GitHub CLI가 없으면 repository 웹 화면의 Compare & pull request를 사용한다. push 자체가 불가능하면 git diff 결과를 파일로 저장하고 다음 차시로 진행한다.

## Codex PR 리뷰

Codex GitHub Code Review가 설정된 교육용 repository에서 PR comment에 다음을 입력한다.

~~~text
@codex review
~~~

특정 관점을 요청할 때:

~~~text
@codex review for workspace path safety, error-code compatibility, and missing unit tests
~~~

자동 리뷰를 켜려면 연결된 GitHub repository와 repository 설정 권한이 필요하다. Codex는 AGENTS.md의 적용 가능한 Code Review Rules를 읽는다. 포맷팅·lint 같은 기계적 검사는 CI에 두고, AGENTS.md에는 저장소 특화 안전 경계와 제품 동작을 둔다.

공식 OpenAI 문서: https://learn.chatgpt.com/docs/third-party/github

## 사람이 최종 확인할 Review 기준

| 기준 | 질문 | 자동 증거 | 사람 판단 |
|---|---|---|---|
| 기능 정확성 | 요구한 동작을 구현했는가? | unit test·CI | 요구사항과 diff 비교 |
| 회귀 | 기존 정상 동작이 유지되는가? | 전체 pytest | 바뀐 계약 확인 |
| 안전 경계 | 파일·도구·외부 쓰기 권한이 넓어졌는가? | 실패 test | 위험한 side effect 판단 |
| 오류 계약 | 같은 실패가 안정된 error_code로 남는가? | assertion | 사용자가 복구할 수 있는가 |
| Clean Code | 함수 책임과 이름이 명확한가? | 일부 lint | 추상화가 더 이해하기 쉬운가 |
| 데이터·보안 | secret·고객·회사 데이터가 포함됐는가? | secret scan 선택 | 화면·문맥 포함 최종 확인 |
| 관측 가능성 | 실패 원인을 trace/log로 찾을 수 있는가? | 구조화 event test | 운영 질문에 답할 수 있는가 |

## Clean Code 관점의 강사 기준

- 함수 하나는 한 가지 책임을 가진다.
- 입력·출력·오류 형식을 이름과 타입으로 드러낸다.
- broad except로 오류를 숨기지 않는다.
- 외부 상태 변경은 함수 경계와 승인 지점이 보인다.
- 중복 제거보다 이해하기 쉬운 구조를 우선한다.
- 주석은 코드 번역이 아니라 정책과 이유를 설명한다.
- 테스트하기 어려운 코드는 책임이 너무 크거나 side effect가 섞였는지 의심한다.

## Merge 전 Human Gate

- CI가 통과했다.
- PR 목표와 실제 diff가 일치한다.
- Codex 지적 사항을 수정했거나 반박 이유를 남겼다.
- secret·실제 회사 데이터·불필요 파일이 없다.
- 정상·실패 test가 함께 있다.
- 사람이 최종 diff와 merge target을 확인했다.

이 Gate를 통과하기 전에는 자동 merge하지 않는다.
