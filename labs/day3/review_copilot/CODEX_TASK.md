# Codex 실습 요청서 · 작은 변경에서 PR까지

## 이번 수업의 기본 Task · 쿠폰 결제 서비스

`exercise --step prepare`를 실행한 뒤 아래 대화를 사용합니다. Notebook에서 별도 폴더를 만들었다면 경로를 해당 폴더로 바꿉니다.

```text
쿠폰 결제 서비스의 코드 리뷰를 부탁해.
먼저 output/day3-redesign/student-service/requirements.md를 읽고
starter/checkout.py와 starter/checkout_checks.py를 확인해.
starter 폴더에서 python checkout_checks.py를 실행해서 실패 조건을 재현해.

상품 10,000원에 쿠폰 15,000원을 적용하면 어떤 문제가 생기는지,
상품 50,000원에 쿠폰 10,000원을 적용하면 배송비는 얼마여야 하는지 확인해.
각 리뷰는 파일·줄 번호·사용자 영향·재현 입력·최소 수정으로 작성해.
지금은 코드를 수정하지 말고 리뷰 결과를 먼저 보여줘.
```

리뷰를 읽고 수정할 항목을 선택한 다음 이어서 요청합니다.

```text
입력 검증, 쿠폰 상한, 할인 후 배송비 기준, 영수증 할인액을 수정하자.
수정 범위는 output/day3-redesign/student-service/starter/checkout.py야.
기존 테스트를 약하게 바꾸지 말고, 같은 9개 테스트를 다시 실행해.
수정 전후 결제 예정액과 실제 테스트 결과를 보여줘.
마지막으로 변경 diff, 수정 이유, 테스트 결과를 PR 본문 초안으로 정리해.
```

기본 Task를 마친 뒤 아래 Rule 추가 과제를 선택합니다.

아래 블록을 Codex에 그대로 전달한 뒤, 학생은 `목표`와 `완료 조건`만 자신의 기능에 맞게 바꿉니다.

```text
목표
Review Copilot이 신뢰할 수 없는 입력을 `pickle.loads()`로 역직렬화하는 코드를
실제 추가 라인에서만 찾도록 새 Rule을 구현해 주세요.

먼저 읽을 파일
- AGENTS.md
- labs/day3/review_copilot/README.md
- labs/day3/review_copilot/review_engine.py
- tests/test_day3_review_copilot.py

변경 허용 범위
- labs/day3/review_copilot/
- tests/test_day3_review_copilot.py

완료 조건
- `pickle.loads(payload)` 추가 라인에 P0 finding이 하나 있어야 함
- Rule ID는 `unsafe-pickle-deserialization`로 고정
- `json.loads(payload)`과 주석·문자열 속 `pickle.loads` 표현에서는 false positive가 없어야 함
- finding은 실제 추가 라인을 정확히 가리켜야 함
- fixture provider와 external_write=false 계약이 유지되어야 함
- .venv312/bin/python -m pytest -q tests/test_day3_review_copilot.py 통과

금지 행동
- .env, token, 실제 고객 코드 읽기·출력·commit
- 사람 승인 없는 push, PR 생성, comment, merge
- 통과를 위한 기존 assertion 또는 안전 정책 약화
- 변경 허용 범위 밖 수정

작업 순서
1. 현재 동작과 관련 test를 먼저 읽기
2. 허용 탐지 test와 `json.loads`·주석·문자열 false-positive test를 먼저 추가
3. 가장 작은 코드 변경
4. focused test 실행
5. git diff --check와 diff 검토
6. 변경 파일·핵심 diff·실행한 test와 실제 결과 보고
```

## 학생 확인표

- Codex가 허용 경로 밖을 바꾸지 않았는가?
- finding이 실제 추가 라인을 가리키는가?
- 실행하지 않은 test 결과를 만들어내지 않았는가?
- provider 실패와 fixture fallback이 구분되는가?
- external write가 여전히 `false`인가?
- PR target이 본인의 repository·branch인가?

## GitHub 자동 검사 연결

이 저장소의 `.github/workflows/day3-pr-quality.yml`은 PR 생성·변경 시 read-only 검사를 수행합니다. `.github/workflows/day3-codex-review-optional.yml`은 수동 실행과 명시적 비용 opt-in이 있을 때만 Codex 검토 artifact를 만들며, PR comment나 merge는 자동 수행하지 않습니다.

```bash
git switch -c codex/day3-review-copilot
git add labs/day3/review_copilot tests/test_day3_review_copilot.py
git diff --cached
git commit -m "feat(day3): add review copilot lab"
git push -u origin codex/day3-review-copilot
gh pr create --draft --base main --head codex/day3-review-copilot
```

명령은 대상 repository와 diff를 사람이 확인한 뒤 한 줄씩 실행합니다. `main` 직접 push와 자동 merge는 이 실습의 기본 동작이 아닙니다.
