## Goal

<!-- 변경할 동작 또는 학습 목표 하나를 한 문장으로 적습니다. -->

## Scope

- Changed files: <!-- 예: src/course_services/review_service.py, tests/test_course_services.py -->
- Intentionally unchanged: <!-- 예: 실제 GitHub 게시, 자동 merge -->

## Safety and data

- [ ] No secret, token, real customer data, or private meeting data is included.
- [ ] File, tool, and external-write boundaries remain explicit.
- [ ] Human approval is preserved for consequential actions.

## Test evidence

~~~text
python3 -m pytest -q
~~~

- Result: <!-- 예: 4 passed -->
- Added/updated normal test:
- Added/updated failure or boundary test:

## Review request

- Risk to inspect: <!-- 가장 먼저 검토할 오류·안전 경계 -->
- Expected behavior:
- Known limitation:

## Human merge checklist

- [ ] Diff matches the stated goal.
- [ ] CI is green.
- [ ] Review findings were fixed or answered with a reason.
- [ ] AI review output was treated as advice, not approval.
- [ ] A human checked the final diff and merge target.
