## Goal

3일차 수강생이 PR Diff를 근거로 Review Finding을 만들고 Human Review와 GitHub CI까지 재현할 수 있는 Review Intelligence Service를 제공합니다.

## Scope

- Changed files: `labs/day3/review_copilot/`, `materials/day3/`, Day 3 Notebook·PPT·PDF·test·GitHub workflow
- Intentionally unchanged: 실제 고객 코드, 실제 회의 데이터, 자동 GitHub comment, 자동 merge, 외부 서비스 자동 변경

## Safety and data

- [x] No secret, token, real customer data, or private meeting data is included.
- [x] File, tool, and external-write boundaries remain explicit.
- [x] Human approval is preserved for consequential actions.

## Test evidence

~~~text
.venv312/bin/python -m pytest -q tests/test_day3_review_copilot.py tests/test_day3_notebook.py tests/test_day3_curriculum.py tests/test_day3_pr_guard.py tests/test_day3_preflight.py tests/test_day3_student_bundle.py
~~~

- Result: `80 passed`
- Added/updated normal test: Diff parsing, provider provenance, Review workflow, Golden Set, localhost smoke
- Added/updated failure or boundary test: Workspace escape, sensitive path, invalid schema, unresolved Human Review, live candidate gate

~~~text
.venv312/bin/python -m pytest -q tests/test_day1_agent.py tests/test_langchain_langgraph_lab.py tests/test_meeting_agent_workflow.py tests/test_openai_provider.py tests/test_ollama_tool_agent.py
~~~

- Result: `35 passed`
- Clean worktree full suite: `204 passed`
- Slide validation: `176 pages`, overflow `0`, exact headline duplicate `0`
- Student bundle: `62 files`, allowlist 기반 deterministic ZIP

## Review request

- Risk to inspect: Human Review 결정이 없거나 실패한 test 결과가 GitHub 전달 가능 상태로 잘못 바뀌지 않는지 확인
- Expected behavior: 미결정은 `REVIEW_REQUIRED/HOLD`, 승인·수정은 실제 test 통과 시에만 `DRY_RUN_READY`, 거절은 `BLOCKED`
- Known limitation: 선택 Live LLM의 품질은 별도 candidate evaluation을 통과해야 하며 AI Review 결과는 사람의 merge 승인이 아님

## Human merge checklist

- [ ] Diff matches the stated goal.
- [ ] CI is green.
- [ ] Review findings were fixed or answered with a reason.
- [ ] AI review output was treated as advice, not approval.
- [ ] A human checked the final diff and merge target.
