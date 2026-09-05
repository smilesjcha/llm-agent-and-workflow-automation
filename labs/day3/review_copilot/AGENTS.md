# Review Copilot Lab Rules

## Scope

- Keep implementation changes inside `labs/day3/review_copilot/`.
- Focused tests belong in `tests/test_day3_review_copilot.py`.
- Use only synthetic fixtures from `fixtures/`; never use a real customer repository or private diff.

## Contracts and safety

- Every finding must map to an added line in the parsed diff.
- Preserve named error codes at workflow and HTTP boundaries.
- Keep fixture fallback provenance explicit; never label a fixture result as Ollama, OpenAI, or Claude.
- Resolve paths before checking the workspace boundary.
- GitHub output is dry-run only. Push, PR creation, comment, merge, and external writes require a separate human action.
- Do not read or log tokens, `.env` values, private meeting data, or customer code.

## Completion evidence

- Add a normal test and the most consequential boundary test.
- Run `.venv312/bin/python -m pytest -q tests/test_day3_review_copilot.py`.
- Run `.venv312/bin/python -m pytest -q tests/test_day1_agent.py`.
- Review `git diff --check` and the exact changed paths before a human merge decision.
