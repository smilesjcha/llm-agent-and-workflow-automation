# 5차시 Codex Task · Human Review Policy

## 목표

`starter/review_policy.py`의 `requires_human_review()`를 완성한다. 로컬 초안 생성은 계속 진행할 수 있지만, 외부 서비스 반영 또는 근거 오류가 있는 결과는 반드시 사람 검토로 보낸다.

## 허용 범위

- 수정 가능: `labs/day2/codex-task/starter/review_policy.py`
- 수정 금지: `task_check.py`, `solution/`, 운영 코드, `.env`
- 외부 게시·메일 발송·API 호출: 없음

## 완료 조건

```bash
python labs/day2/codex-task/task_check.py \
  --report output/course-labs/day2-v2/student-run/05_codex_run.json
```

네 사례가 모두 `PASS`이고, 결과 파일의 `external_write`가 `false`여야 한다.

## Codex 요청 예시

```text
AGENTS.md와 labs/day2/codex-task/TASK.md를 먼저 읽어줘.
starter/review_policy.py만 수정해서 requires_human_review를 완성해줘.
정상 사례와 가장 중요한 경계 사례를 task_check.py로 확인하고,
변경 diff와 남은 위험을 내가 검토할 수 있게 짧게 설명해줘.
외부 서비스에는 쓰지 마.
```

## 진행 순서

1. 수정 전 명령 실행과 실패 사례 확인
2. Codex에 위 Task 전달
3. 제안된 diff 확인
4. 같은 명령 재실행
5. `05_codex_run.json`의 네 사례와 안전 경계 확인
6. 필요할 때만 `solution/review_policy.py`와 비교
