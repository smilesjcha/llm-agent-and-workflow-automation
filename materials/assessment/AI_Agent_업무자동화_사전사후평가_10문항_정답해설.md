# AI Agent·업무자동화 사전·사후평가 · 10문항 정답·해설

> 강사용 문서다. 평가 시행 전 수강생에게 배포하지 않는다.

## 정답표

| 문항 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 정답 | B | A | D | C | B | C | A | A | C | D |

## 문항별 해설

| 문항 | 정답 | 핵심 해설 | 평가 의도 |
|---|---:|---|---|
| 1 | B | LLM은 주어진 맥락에서 결과를 생성한다. Agent는 LLM의 판단을 활용해 다음 단계나 도구를 선택하고 작업을 이어간다. | LLM·Workflow·Agent 구분 |
| 2 | A | STT는 음성을 텍스트로 바꾸는 기술이다. 이미 텍스트가 있다면 다시 STT할 필요가 없다. | 음성 입력의 기본 개념 |
| 3 | D | 이미 전사된 TXT는 입력 형식과 품질을 확인해 공통 입력 구조로 변환한다. 불필요한 STT 반복은 시간·비용·오류를 늘린다. | 입력별 적절한 처리 경로 |
| 4 | C | LLM은 Tool Call을 제안할 수 있지만, 실제 실행 전 도구 이름·인자·경로·권한을 코드가 검증해야 한다. | Tool Calling 안전 경계 |
| 5 | B | LangGraph는 State·Checkpoint·Interrupt·Resume이 필요한 장기 실행 Workflow와 Human Review에 적합하다. | LangGraph 적용 상황 |
| 6 | C | Human Review는 외부 저장·게시·발송 전에 사람이 Approve·Edit·Reject를 결정하는 실제 실행 경계다. | 사람 승인 단계의 의미 |
| 7 | A | Evidence ID는 요약·결정·할 일이 어떤 원문 Segment에 근거했는지 추적하게 한다. 근거가 없으면 HOLD하는 것이 안전하다. | 근거 기반 결과 검증 |
| 8 | A | 좋은 Harness는 Goal·Allowed Scope·Expected Result·Test를 고정하고, 작은 Patch와 Diff를 사람이 검토하게 한다. | Codex 활용과 코드 품질 |
| 9 | C | LangSmith는 Node별 입력·출력·상태·Latency·Error를 Trace하고 결과를 평가하는 관측 도구다. 민감정보는 기록 전에 비식별화한다. | LLMOps 관측과 평가 |
| 10 | D | 고정된 순서는 Workflow가 더 저렴하고 재현성이 높다. Agent는 상황 판단이나 도구 선택이 실제로 필요한 구간에 제한한다. | 비용·복잡도 기반 설계 |

## 권장 점수 해석

| 점수 | 해석 | 사후 지도 방향 |
|---:|---|---|
| 0~3 | 개념 입문 | STT·LLM·Workflow·Agent의 차이부터 재설명 |
| 4~6 | 기초 이해 | Tool Calling·Evidence·Human Review 사례 보강 |
| 7~8 | 실무 적용 가능 | LangGraph·Harness·Trace 실습으로 확장 |
| 9~10 | 핵심 메시지 이해 | Boundary Test·비용·운영 판단 심화 |

## 사전·사후 비교 기준

- 개인 향상도: `사후점수 - 사전점수`
- 과정 평균 향상도: `사후평균 - 사전평균`
- 핵심 문항: 1번 Agent 구분, 4번 Tool 안전, 6번 Human Review, 7번 Evidence, 10번 비용 판단
- 사후에도 핵심 문항 오답률이 높다면 기능 Demo보다 설계 판단과 실패 사례를 다시 설명한다.
