# Day 3 콘텐츠 검증 이력

## 2026-09-06 · Codex CLI 기반 개편 정본

이 절이 아래 176p·Ollama 중심 기록보다 우선한다. 아래 내용은 변경 이력으로 보존한다.

- 원본 6개 모듈 40H와 1·2주차 진행 내용을 연결했다. 3주차는 코드 리뷰 Agent 8H, 4주차는 GitHub 자동 리뷰 6H와 문서 연결 2H, 5주차는 문서 2H·통합/운영 3H·개인 프로젝트 3H다. 과거 실제 시간의 측정값이 아닌 향후 운영을 위한 주제 배분이다.
- 실습 완료 기준은 JSON 파일이 아니라 오류 재현·직접 함수 구현·Codex 리뷰·실제 checkout.py 수정·9개 테스트 재실행·HTTP 화면과 Markdown 리뷰다.
- 주 경로는 로컬 Codex CLI다. PC 클라이언트와 클라우드 추론을 구분하고 인터넷·로그인·계정 이용 권한을 설명한다. Ollama 설치와 API key는 3주차 필수 조건이 아니다.
- Reviewer Adapter는 제공된 Context만 검토하는 제한된 LLM 호출이다. 학생과 대화형 Codex의 코드 탐색·수정·테스트 Agent 과정은 별도 Role로 표현했다. Python의 검증 로직과 LangGraph의 interrupt/resume도 분리했다.
- 실제 Codex CLI 리뷰에서 4개 지적을 얻었고 fixture fallback은 없었다. 별도 대화형 코드 수정에서는 checkout.py만 변경하고 테스트 파일을 유지했다. 9개 테스트 중 7개 실패에서 9개 통과로 개선됐다. 실행 기록은 `output/day3-redesign/live-evidence/`와 `codex-authoring-demo/`에 있다.
- Notebook 49셀의 기본 전체 실행은 명시적인 Fixture 재현이다. 별도 Live 전체 실행도 완료했다. 실패를 Live 성공으로 표시하지 않고 `allow_fallback=False`를 유지한다. 학생은 `RUN_CODEX_LIVE=True`로 실제 리뷰를 선택한다.
- 단계별 안전 검증에 workspace 이탈·잘못된 출력·CLI 시간 초과·출력 인코딩·테스트 미실행을 포함한다. exit code 0이라도 실행된 테스트가 0개면 `NO_TEST_EVIDENCE`다.
- 매 Notebook 실행마다 고유 실습 폴더를 만든다. 직접 수정한 폴더·Day 2 기존 작업은 보존한다. Localhost는 Notebook이 출력한 `--exercise-dir`로 동일 코드를 실행한다.
- 수업 8차시 각 50분이다. 오전 3차시 뒤 11:30~12:00 휴식, 12:00~13:00 점심, 4·5차시 뒤 14:40~15:00 휴식, 마지막 17:30~18:00 휴식·Q&A다.
- 5주차 프로젝트는 15:00~18:00 안에서 제작·검증·개선 정리 150분과 후반 휴식·Q&A 30분이다. 온라인 개인 실습이며 발표를 강제하지 않는다.
- 121장 정본은 짧은 명사형 제목, 26개 편집 가능한 표, 코드·설명·비교·실제 화면을 교차 사용한다. 본문 21pt 이상, 표 19.5pt, 코드 18pt 기준이다. Mermaid 원본은 `assets/components/day3/master-code-review-agent.mmd`에 보존한다.
- 전체 PDF 121쪽을 렌더해 개별 검수했다. 작은 테스트·리뷰 캡처는 원본의 해당 영역만 확대하고 잘린 함수명 설명은 교정했다. PDF에는 AppleGothic·Menlo를 포함한다. Windows PowerPoint에서의 글꼴 대체는 직접 실행 검증하지 않았으므로 배포에는 PDF를 함께 제공한다.
- Day 3 6개 테스트 파일 실행: `120 passed`. Day 1 5개 회귀 테스트 파일 실행: `35 passed`. 정확한 명령은 `materials/day3/2026_Day3_개편_검증결과.md`에 기록한다.
- 학생 ZIP은 74개 allowlist 파일만 포함하며 `.env`, 토큰, 실제 고객 자료, 생성 Output, 실행 완료 Notebook은 포함하지 않는다. PDF·PPT·실행 예시는 별도 배포다.

## 2026-09-04 · Review Intelligence 정본 전환

- 구형 21셀 Notebook과 범용 240장 초안을 참고본으로 유지하고, 55셀 `day3_review_intelligence_lab.ipynb`를 3일차 정본으로 지정했다.
- 시간표를 2~5일차 공통 운영인 `1~3차시 → 90분 쉬는 시간·점심시간 → 4~5차시 → 20분 쉬는 시간 → 6~8차시 → 30분 쉬는 시간·Q&A`로 통일했다.
- “웹사이트 구경”을 소프트웨어 실습으로 부르지 않는다. 각 차시는 Python code, Notebook cell, terminal command, test, local artifact 중 하나 이상을 직접 만든다.
- Review Contract → Diff Parser → Context Pack → Provider Adapter → Hybrid Review → LangGraph Human Review → Golden Evaluation → Localhost·GitHub PR 순서로 메시지 소유권을 고정했다.
- Day 2의 회의록 Export 변경을 `meeting_export_pr.diff`로 재사용해 40시간 과정의 연결성을 보존했다.
- 기본 Run All은 fixture, network 0회, credential 출력 0회, external write 0회다. Ollama와 OpenAI는 별도 설치와 명시적 opt-in이 함께 있을 때만 실행한다.
- Local UI는 초심자용 동기식 Human Review, 실제 LangGraph `interrupt()`·`Command(resume=...)`는 Notebook 6차시의 학습 Lane으로 구분했다.
- `@codex review`와 API 기반 Codex Action은 선택 경로다. GitHub Actions, AI Review, passing test는 사람 merge 결정을 대신하지 않는다.
- 장표 제목은 짧은 명사형, 본문은 학생 행동과 판단에 필요한 내용만 표시한다. 내부 제작 지침·장표 역할 tag·페이지 수 목표는 화면에 노출하지 않는다.
- 색상은 black·white·gray를 기본으로 하고 navy·blue는 상태 또는 핵심 경고에만 쓴다. 마지막 열·행·순서라는 이유만으로 accent를 적용하지 않는다.
- 글꼴은 PDF 변환 환경에서 확인된 일반 고딕을 사용하고, 본문 18pt·표 17pt·code 15pt 아래로 축소하지 않는다.

## Release Gate

- PPTX 176장과 PDF 176쪽 일치
- 전 페이지 렌더 및 overflow·font·잘림 검사
- exact headline duplicate 0건 목표
- 차시별 주 메시지 중복 없음
- 8개 Golden Case와 clean negative·expected failure 포함
- Focused Day 3 test와 Day 1 회귀 test 통과
- `git diff --check` 통과
- 의도된 Day 3 파일만 stage
- 실제 credential, `.env`, 고객 데이터, private PR 미포함

## 2026-09-05 · Student-ready 176p 검증

- 중복 검사는 설명 문장과 재실행용 기술 앵커를 분리한다. 정본 경로, 명령, JSON 결과 파일명, Contract Field, 상태값은 차시 간 실행 연결을 위해 반복을 허용한다.
- 기술 앵커를 제외한 exact headline duplicate 0건, repeated narrative line 0건, final synthesis 밖 summary headline 0건을 확인했다.
- 유사 headline은 같은 차시의 탐색 표식(예: `Provider Adapter`, `Provider Adapter Test 명령`)만 진단 목록에 남기고 실패 조건으로 쓰지 않는다.
- PPTX 176장, PDF 176쪽, speaker notes 176개를 확인했다.
- package integrity, 16:9 geometry, font policy, heading fit, overflow 검사를 통과했다.
- Day 3 focused suite와 Day 1 회귀 suite를 통과했다. 최종 건수는 서비스 코드 확정 뒤 preflight report에 기록한다.
- 전체 Day 3 preflight는 `PASS`, `external_write=false` 상태다.

## 2026-09-05 · 코드 계약 재검증

- Multi-hunk Line Mapping, Context Allowlist, Evidence Grounding, Precision·Recall·F1을 수강생이 직접 작성하는 네 개 코드 셀을 추가했다.
- Human Review 기본값은 자동 승인 대신 `REVIEW_REQUIRED/HOLD`다. 6차시의 `REVIEW_DECISION`을 8차시 Workflow까지 전달하며 `reject`는 GitHub 단계도 `HOLD`로 끝낸다.
- Provider 결과에 `requested_model`, 실제 `model`, `schema_valid`, `fallback_reason`을 함께 표시한다. Fixture의 Rule Baseline 점수는 Live Candidate 평가를 대신하지 않는다.
- PPT 코드 예시의 실제 Test Evidence 필드를 `executed`, `command`, `exit_code`, `status` 계약으로 교정했다.
- 학생 ZIP은 명시적 Allowlist만 사용하며 실행 완료 Notebook, 강사용 교안, Output, `.env`, Token을 제외한다.
- 구조적 유사 제목은 진단 목록으로만 유지한다. 정본 경로·실행 명령처럼 필요한 기술 앵커를 제외한 설명 문장 중복은 0건을 기준으로 한다.
- 수강생 노출 문구의 `정상`, `경계`, `외부 쓰기`를 각각 `기본·허용`, `실패 조건·허용 범위`, `외부 서비스 변경`으로 풀어 썼다. 코드 계약의 `external_write` 필드명은 그대로 유지한다.
