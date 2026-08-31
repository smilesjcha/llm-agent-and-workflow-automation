# AI Agent·업무자동화 사전·사후평가 · 20문항 정답·해설

> 강사용 문서다. 평가 시행 전 수강생에게 배포하지 않는다.

## 정답표

| 문항 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 정답 | B | C | A | D | B | C | D | A | B | C |

| 문항 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 정답 | A | D | B | C | A | D | B | C | A | D |

> 정답 분포: A 5문항·B 5문항·C 5문항·D 5문항

## 문항별 해설

| 문항 | 정답 | 핵심 해설 | 평가 의도 |
|---|---:|---|---|
| 1 | B | LLM은 주어진 맥락에서 결과를 생성한다. Agent는 LLM의 판단을 활용해 다음 단계나 도구를 선택하고 작업을 이어간다. | LLM·Workflow·Agent 구분 |
| 2 | C | 처리 순서와 실패 규칙이 정해져 있다면 Workflow로 고정하는 편이 재현성과 비용 면에서 유리하다. | Workflow 적용 판단 |
| 3 | A | STT는 음성을 텍스트로 바꾸는 기술이다. | 음성 입력 기본 개념 |
| 4 | D | 이미 전사된 TXT는 입력 형식과 품질을 확인해 공통 구조로 변환한다. 불필요한 STT 반복은 시간·비용·오류를 늘린다. | 입력별 처리 경로 |
| 5 | B | 전문 영역에서는 용어, 기존 결정, 업무 정책, 원하는 결과 형식이 결과 품질을 좌우한다. | Prompt·Domain Context |
| 6 | C | LLM은 Tool Call을 제안할 수 있지만 실제 실행 전 도구·인자·경로·권한을 코드가 검증해야 한다. | Tool Calling 안전 경계 |
| 7 | D | 허용되지 않은 Tool은 실행하지 않고 `POLICY_BLOCKED` 같은 안정된 오류 계약을 남겨야 한다. | Allowlist·오류 계약 |
| 8 | A | LangChain은 Prompt·Model·Parser·Retriever·Tool과 Adapter를 조합해 처리 흐름을 구성한다. | LangChain 기본 역할 |
| 9 | B | LangGraph는 State·Checkpoint·Interrupt·Resume이 필요한 장기 실행 Workflow와 Human Review에 적합하다. | LangGraph 적용 상황 |
| 10 | C | Human Review는 외부 저장·게시·발송 전에 사람이 Approve·Edit·Reject를 결정하는 실제 실행 경계다. | 사람 승인 단계 |
| 11 | A | Evidence ID는 요약·결정·할 일이 어떤 원문 Segment에 근거했는지 추적하게 한다. | 근거 기반 검증 |
| 12 | D | Schema는 필수 Field와 자료형을 고정하고, 잘못된 결과가 다음 단계로 넘어가는 것을 막는다. | Structured Output |
| 13 | B | Fixture는 Provider가 없어도 같은 계약을 재현한다. 다만 `provider_used`와 `fallback_reason`을 명확히 남겨야 한다. | 재현성과 정직한 Fallback |
| 14 | C | `127.0.0.1`은 기본적으로 자신의 PC에서만 접근하는 Loopback 주소다. 상용 배포나 외부 공개를 의미하지 않는다. | Localhost 이해 |
| 15 | A | 좋은 Harness는 Goal·Allowed Scope·Expected Result·Test를 고정하고 작은 Patch와 Diff를 사람이 검토하게 한다. | Codex·Claude 활용 |
| 16 | D | 기능 변경은 정상 경로뿐 아니라 권한·입력 오류·실패 경계까지 Test해야 운영 중 회귀를 줄일 수 있다. | Test 설계 |
| 17 | B | Git과 PR은 변경 이력, Review, Test Evidence와 Rollback 지점을 제공한다. 최종 Merge는 사람의 판단이다. | Git·PR 운영 |
| 18 | C | LangSmith는 Node별 입력·출력·상태·Latency·Error를 Trace하고 결과를 평가하는 관측 도구다. | LLMOps 관측 |
| 19 | A | 외부 Trace에는 개인정보·고객정보·API Key를 그대로 남기지 않는다. 비식별·합성 데이터와 Redaction이 우선이다. | 개인정보·보안 |
| 20 | D | 고정된 순서는 Workflow가 더 저렴하고 재현성이 높다. Agent는 상황 판단이나 Tool 선택이 실제로 필요한 구간에 제한한다. | 비용·복잡도 판단 |

## 난이도 구성

| 구간 | 문항 | 확인 역량 |
|---|---|---|
| 기초 | 1~5 | LLM·Agent·Workflow·STT·Context |
| 핵심 기능 | 6~12 | Tool Calling·LangChain·LangGraph·Human Review·Evidence·Schema |
| 실무 운영 | 13~20 | Fallback·Localhost·Harness·Test·Git·LangSmith·보안·비용 |

## 권장 점수 해석

| 점수 | 해석 | 사후 지도 방향 |
|---:|---|---|
| 0~6 | 개념 입문 | LLM·Workflow·Agent와 STT부터 재설명 |
| 7~12 | 기초 이해 | Tool·Schema·Evidence·Human Review 사례 보강 |
| 13~16 | 실무 적용 가능 | LangGraph·Harness·Test·Trace 실습으로 확장 |
| 17~20 | 핵심 메시지 이해 | 비용·보안·운영 자동화 설계 심화 |

## 영역별 점수

| 영역 | 문항 | 만점 |
|---|---|---:|
| AI·입력 기본기 | 1~5 | 5 |
| Agent Workflow 설계 | 6~12 | 7 |
| 개발·운영·안전 | 13~20 | 8 |

## 사전·사후 비교 기준

- 개인 향상도: `사후점수 - 사전점수`
- 과정 평균 향상도: `사후평균 - 사전평균`
- 영역 향상도: 세 영역의 사전·사후 정답률을 각각 비교
- 핵심 문항: 1번 Agent 구분, 6번 Tool 안전, 10번 Human Review, 11번 Evidence, 15번 Harness, 18번 Trace, 20번 비용 판단
- 사후에도 핵심 문항 오답률이 높다면 기능 설명보다 실패 사례와 설계 판단을 다시 보여준다.
