# 5주차 · 업무 자동화 서비스

[강의 PPT](../../slides/IPA_LLM_Agent_업무자동화_Day5_FINALE_240p_v02.pptx) · [PDF](../../output/pdf/IPA_LLM_Agent_업무자동화_Day5_FINALE_240p_v02.pdf) · [복습 Notebook](day5_finale_recap.ipynb)

## 배포 범위

- 240장 교안: 지난 수업의 핵심 원리, 새로운 업무 사례, 개인 프로젝트 과정
- Notebook: 1–4차시의 핵심 코드 복습과 5차시 프로젝트 명세 작성
- 6–7차시: 자신의 프로젝트에서 기능 제작, 실행 확인, 사용 안내 작성

강사의 별도 검색 서비스 시연 기획서·소스코드·데이터는 포함하지 않습니다. PPT에 등장하는 해당 시연 코드와 파일 경로는 이 Notebook의 실행 대상이 아닙니다. 강의의 21개 서비스는 응용 설계 예시이며 모두 구현 완료된 제품을 제공한다는 의미는 아닙니다.

## 새 폴더에서 시작

Python **3.12**, Git, VS Code의 Python·Jupyter 확장을 준비합니다. 기존 실습을 수정했다면 그 폴더는 보존합니다.

```sh
git clone --branch main https://github.com/smilesjcha/llm-agent-and-workflow-automation.git llm-agent-week5
cd llm-agent-week5
```

macOS:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install jupyterlab ipykernel
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install jupyterlab ipykernel
```

VS Code에서 `materials/day5/day5_finale_recap.ipynb`를 열고 `.venv`의 Python을 Kernel로 선택합니다. 맨 위부터 실행합니다. 상단 `%pip` 셀이 pydantic, pytest, openpyxl을 현재 Kernel에 설치합니다. 가상환경을 활성화한 터미널에서는 다음 명령으로 Jupyter Lab을 열 수도 있습니다.

```sh
python -m jupyter lab materials/day5/day5_finale_recap.ipynb
```

기본 복습은 외부 LLM 호출 없이 실행합니다. Codex·Claude를 이용한 개인 제작에는 각자의 계정과 이용 조건이 적용됩니다.

## 차시별 직접 진행

| 시간 | 활동 | 사용할 파일·입력 | 확인할 결과 |
|---|---|---|---|
| 09:00–09:50 | 1차시 · 입력 종류 변경 | Notebook 1차시<br>`data/meeting_sample_ko.txt` | 회의 처리와 지원하지 않는 입력의 오류 |
| 09:50–10:40 | 2차시 · 근거 번호 검사 | Notebook 2차시<br>합성 발화 s01·s02 | 존재하는 근거와 없는 근거의 구분 |
| 10:40–11:30 | 3차시 · 변경 위치 검토 | Notebook 3차시<br>`data/day3_review_cases/unsafe_pr.diff` | 규칙 기반 검토 의견과 빈 입력 오류 |
| 11:30–12:00 | 쉬는 시간 | 실행 상태 저장 | 질문 정리 |
| 12:00–13:00 | 점심시간 | 12:55 복귀 | — |
| 13:00–13:50 | 4차시 · 일정 상태 변경 | Notebook 4차시<br>`labs/day4/office_lab/sheets/wbs_tasks.json` | 진행률 변경과 잘못된 값의 오류 |
| 13:50–14:40 | 5차시 · 프로젝트 명세 작성 | Notebook 5차시<br>자신의 합성 입력 예시 | 사용자·입력·결과·실패 두 건 |
| 14:40–15:00 | 쉬는 시간 | 개인 제작 환경 확인 | — |
| 15:00–16:40 | 6–7차시 · 개인 프로젝트 | 자신의 프로젝트 폴더<br>기존 주차 코드 중 한 기능 | 실제 실행 결과와 다음 개선 |
| 16:40–17:00 | 실행 복구·Q&A | 원할 경우 결과 공유 | 발표 필수 아님 |

5차시는 명세 작성 단계입니다. 명세의 필수값을 확인했다고 서비스 구현이 끝난 것은 아닙니다. 6–7차시에는 파일을 읽는 코드나 계산 기능을 바꾸고, 정상 입력과 실패 입력을 실행해 실제 결과를 확인합니다.

## 실행 검사

Notebook과 같은 Python 환경의 저장소 루트에서 실행합니다.

```sh
python -m pytest -q tests/test_day1_agent.py tests/test_course_services.py tests/test_day4_excel_lab.py
```

3차시의 짧은 복습 코드는 규칙 기반 검사입니다. 모델이 직접 검토하는 과정은 [3주차 Notebook](../day3/day3_review_intelligence_lab.ipynb)을 사용합니다. 4차시는 날짜와 진행률 계산의 복습이며, 실제 Excel·Word·PPT 파일 제작은 [4주차 Notebook](../day4/day4_pr_document_automation.ipynb)에서 이어갑니다.

## 문제 해결

| 상황 | 확인할 내용 |
|---|---|
| 모듈을 찾을 수 없음 | 상단 설치 셀 실행, Python Kernel 확인 |
| 저장소 루트를 찾을 수 없음 | Notebook만 따로 받지 말고 저장소 전체를 내려받아 실행 |
| 앞의 변수를 찾을 수 없음 | Kernel 재시작 후 첫 셀부터 순서대로 실행 |
| 입력을 바꾸니 assertion 실패 | 정상 입력의 기대값도 함께 확인하고, 오류 재현 후 원래 입력으로 복구 |
| 검색 서비스 파일이 없음 | 강사 별도 시연 자료는 배포 대상이 아님. 자신의 프로젝트로 진행 |

실제 고객 정보, 비공개 회의, 학생 성적, API key를 업로드하지 않습니다. 외부 게시·메일 발송·배포는 사람의 별도 확인 후 진행합니다.
