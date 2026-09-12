# LLM Agent & 업무자동화

5주 · 40시간 | 회의 기록 · 코드 리뷰 · 문서 자동화

개념을 익힌 뒤 Notebook에서 코드를 실행하고, 오류를 수정하고, 브라우저에서 서비스를 확인합니다. 아래에서 수업 자료를 고른 후 해당 주차의 실습 가이드 순서대로 진행하세요.

## 이번 수업 · 4주차 GitHub PR 자동 리뷰 · 문서 자동화

PR 리뷰와 테스트를 연결하고, 같은 업무 데이터를 Excel 일정표·채점표, Word 이력서, PPT 보고서로 만듭니다. 입력 변경, 코드 수정, 오류 처리, 실제 파일 확인까지 진행합니다.

**[실습 가이드][day4-guide]** · **[Notebook][day4-notebook]** · **[강의 PPT][day4-ppt]** · **[PDF][day4-pdf]** · **[코드 ZIP 다운로드][day4-zip]**

> 아래 실행 명령은 4주차 자료를 모은 `codex/day4-document-automation` 브랜치 기준입니다. 파일명에 `DRAFT`가 붙은 이전 초안은 사용하지 않습니다.

## 4주차 시작

1. [코드 ZIP][day4-zip]을 풀어 VS Code로 열거나, 아래 명령으로 **새 폴더**에 받습니다. 이전 주차에서 수정한 파일은 그대로 보존합니다.

   ```bash
   git clone --branch codex/day4-document-automation https://github.com/smilesjcha/llm-agent-and-workflow-automation.git llm-agent-week4
   cd llm-agent-week4
   ```

2. 기존 Python 가상환경에서 아래 명령을 실행합니다. 새 환경을 만드는 Mac·Windows 안내는 [실습 가이드][day4-guide]에 있습니다. `npm` 명령은 **7차시 PPT 생성**에 필요합니다.

   ```bash
   python -m pip install -r requirements-day4.txt
   npm install --prefix labs/day4/office_lab/presentations
   ```

3. [4주차 Notebook][day4-notebook]을 열고 설치한 가상환경의 **Kernel**을 선택합니다. 첫 셀부터 진행하고, 셀에 출력되는 **이번 실행 결과 폴더**를 사용합니다. 결과 비교에는 [실행 완료 Notebook][day4-executed]을 이용합니다.

기본 코드는 AI API key 없이 실행합니다. Codex·Claude와의 추가 대화는 선택 사항이며 계정 이용 조건을 따릅니다. 문서는 Excel·Word·PowerPoint 또는 LibreOffice에서 열어 확인합니다.

## 4주차 차시별 작업

| 차시 · 시간 | 내용 | 직접 확인할 결과 |
|---|---|---|
| **1차시 09:00–09:50** | PR·commit·diff 확인 | 대상 검사와 오류 재현 |
| **2차시 09:50–10:40** | 코드 수정·리뷰·사람 확인 | 테스트 결과와 HTML 리뷰 작업대 |
| **3차시 10:40–11:30** | CI·권한·중복 방지 | Actions 설정과 오래된 리뷰 차단 |
| **4차시 13:00–13:50** | WBS·Gantt 자동화 | 진행률을 바꾼 Excel 일정표 |
| **5차시 13:50–14:40** | 시험 채점 자동화 | 재채점·오류 표시·통계 비교 |
| **6차시 15:00–15:50** | 경력 사실·Word 스타일 | 개선 전후 DOCX와 과장 수치 검사 |
| **7차시 15:50–16:40** | WBS 기반 PPT 생성 | 수정한 입력을 반영한 7장 보고서 |
| **8차시 16:40–17:30** | 결과 검증·반복 실행 | 결과 목록과 다음 주 프로젝트 범위 |

쉬는 시간은 **11:30–12:00**, **14:40–15:00**, 마지막 **17:30–18:00 휴식·Q&A**입니다. 점심시간은 **12:00–13:00**입니다.

### 참고 파일

| Excel | Word | PPT |
|---|---|---|
| [WBS·Gantt][day4-wbs]<br>[합성 답안 채점표][day4-exam] | [개선 전][day4-word-before]<br>[개선 후][day4-word-after] | [프로젝트 보고서][day4-brief]<br>[보고서 PDF][day4-brief-pdf] |

제공 파일은 비교용입니다. 직접 실습에서는 자신의 입력으로 **새 파일을 생성**합니다. Excel 재계산, 한글 글꼴, 예상된 테스트 실패 등은 [문제 해결 안내][day4-guide]에서 확인하세요. 실제 성적·비공개 회사 자료는 사용하지 않습니다.

## 주차별 자료

| 주차 | 주요 내용 | 실습 자료 | 강의 자료 |
|:---:|---|---|---|
| 1주차 | Agent 기본 · Tool Calling · 회의 자동화 | [가이드][day1-guide] · [차시별 실행 파일][day1-map] | [PDF][day1-pdf] · [PPT][day1-ppt] |
| 2주차 | 음성·텍스트 입력 · 회의 기록 서비스 | [가이드][day2-guide] · [Notebook][day2-notebook] | [PDF][day2-pdf] · [PPT][day2-ppt] |
| 3주차 | 코드 리뷰 · 테스트 · LangGraph 승인 흐름 | [가이드][day3-guide] · [Notebook][day3-notebook] | [PDF][day3-pdf] · [PPT][day3-ppt] |
| 4주차 | GitHub PR 자동 리뷰 · Excel·Word·PPT 자동화 | [가이드][day4-guide] · [Notebook][day4-notebook] | [PPT][day4-ppt] · [PDF][day4-pdf] |
| 5주차 | Workflow 통합·운영 · 개인 미니 프로젝트 | [사전 안내][day5-project] · [개선 기록][day5-record] | 준비 중 |

5주차 마지막 시간은 **15:00–17:30 개인 제작**, **17:30–18:00 휴식·Q&A**입니다. [사전 안내][day5-project]에서 주제와 준비물을 확인하세요. 발표는 필수가 아닙니다. 전체 연결 과정은 [운영안][roadmap]을 참고하며, 저장소의 `DRAFT` 파일은 확정 교안이 아닙니다.

<details>
<summary><strong>3주차 복습 · 코드 받기와 실행 안내</strong></summary>

## 3주차 시작

3주차 복습은 아래의 `codex/day3-review-intelligence` 브랜치와 전용 설치 명령을 사용합니다. 이번 4주차 실습은 위 안내를 따르세요.

### 1. 준비물

- **Python 3.12 권장**, Git, VS Code의 Python·Jupyter 확장
- 실제 AI 리뷰에 사용할 **Codex CLI와 로그인된 계정** — [설치·로그인 안내][day3-setup]
- 인터넷 연결과 실습 파일을 저장할 개인 폴더

3주차에는 Ollama나 별도 OpenAI API key가 필수가 아닙니다. 제공된 예제 리뷰는 모델 호출 없이 재현할 수 있고, 실제 Codex 리뷰에는 계정 이용 권한·한도가 적용됩니다.

### 2. 코드 받기

터미널에서 다음 명령을 실행합니다. 기존에 수정한 파일이 있다면 덮어쓰지 말고 **다른 새 폴더에서** 시작하세요.

```bash
git clone --branch codex/day3-review-intelligence https://github.com/smilesjcha/llm-agent-and-workflow-automation.git
cd llm-agent-and-workflow-automation
```

Git으로 받기 어렵다면 [코드 ZIP][day3-zip]을 풀고 해당 폴더를 VS Code로 여세요. ZIP에는 **3주차 실행 코드·Notebook·실습 데이터·테스트**가 들어 있습니다. 다른 주차 자료와 PPT·PDF는 위 표에서 별도로 받습니다. ZIP을 사용해도 2차시의 Git 실습을 위해 Git 설치는 필요합니다.

### 3. 실행 환경

아래에서 본인 운영체제를 선택하세요. 명령은 `requirements-day3.txt`가 있는 프로젝트 폴더에서 실행합니다.

<details>
<summary><strong>macOS</strong></summary>

```bash
python3.12 --version
git --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-day3.txt
python scripts/run_day3_preflight.py --code-only
python -m jupyter lab materials/day3/day3_review_intelligence_lab.ipynb
```

`python3.12` 명령을 찾지 못하면 Python 3.12 설치를 먼저 확인하세요. 새 터미널에서는 `source .venv/bin/activate`로 가상환경을 다시 활성화합니다.

</details>

<details>
<summary><strong>Windows · PowerShell</strong></summary>

```powershell
py -3.12 --version
git --version
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-day3.txt
.venv\Scripts\python.exe scripts/run_day3_preflight.py --code-only
.venv\Scripts\python.exe -m jupyter lab materials/day3/day3_review_intelligence_lab.ipynb
```

가상환경 Python을 직접 사용하므로 PowerShell 실행 정책을 변경할 필요가 없습니다. `py -3.12` 명령을 찾지 못하면 Python 3.12 설치를 확인하세요.

</details>

### 4. Notebook 실행

VS Code에서 실행한다면 `day3_review_intelligence_lab.ipynb`를 열고 오른쪽 위 **Kernel → 방금 만든 `.venv`의 Python**을 선택하세요. 셀은 위에서 아래로 진행합니다.

| 선택 | 설정·진행 방법 |
|---|---|
| 제공된 예제 흐름 확인 | 기본값 `RUN_CODEX_LIVE=False` 유지 — 저장된 예제 리뷰 사용 |
| Codex의 실제 코드 리뷰 | 로그인 확인 후 `RUN_CODEX_LIVE=True` — 실제 모델 호출 |
| 내 손으로 코드 수정 | 수정 단계 전 `APPLY_LEARNER_FIX=False` — 출력된 `starter/checkout.py` 경로의 코드 직접 편집 |
| 웹 화면에서 결과 확인 | 마지막 단계에 출력되는 `--exercise-dir` 포함 서버 명령 실행 |

`APPLY_LEARNER_FIX=True`는 참고 수정안을 단계별로 적용하는 기본 설정입니다. 직접 수정하는 실습에서는 `False`로 바꿉니다. Notebook을 새로 실행하면 실습 폴더도 새로 생성되므로 **셀에 출력된 이번 실행 경로**를 사용하세요.

## 막혔을 때

| 상황 | 먼저 확인할 것 |
|---|---|
| `ModuleNotFoundError` · 패키지를 찾을 수 없음 | 설치에 사용한 Python과 Notebook Kernel이 같은 `.venv`인지 확인 |
| 시작부터 테스트 실패 | 1차시는 결함 재현 단계입니다. 초안의 9개 테스트 중 7개 실패는 예상 결과입니다. 이후 수정 단계에서 다시 검사합니다. |
| Codex 명령·로그인 오류 | [설치·로그인 안내][day3-setup] 확인. 예제 모드로 후속 흐름 확인 가능 |
| 화면이 내가 수정한 코드와 다름 | Notebook이 출력한 `--exercise-dir` 포함 명령으로 서버를 시작했는지 확인 |
| 설치 없이 출력부터 확인 | [실행 완료 Notebook][day3-executed] 열기 — 예제 리뷰 기반 참고본 |

</details>

## 실습 파일과 공유 범위

- 수업에서 제공한 합성·공개 예제를 사용합니다. 실제 고객 데이터나 비공개 회의 기록은 올리지 않습니다.
- API key·토큰·`.env`는 GitHub에 올리거나 화면으로 공유하지 않습니다.
- GitHub 게시·PR 생성은 **본인 저장소와 변경 내용을 확인한 뒤** 진행합니다. AI 리뷰와 테스트 통과가 자동 병합 승인을 뜻하지는 않습니다.

---

강사용 시간 배분과 시연 순서는 [4주차 강사 운영안][day4-instructor], 기존 자료 제작·검증 명령은 [강사용 자료·저장소 관리][instructor]에 정리되어 있습니다.

[day1-guide]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day1/수강생용_4-8차시_실습패키지_가이드.md
[day1-map]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day1/실행파일_차시별_맵.md
[day1-pdf]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/output/pdf/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_PARTS_270p.pdf
[day1-ppt]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_PARTS_270p.pptx
[day2-guide]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day2/2026_Day2_수강생_실습가이드.md
[day2-notebook]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day2/day2_service_lab.ipynb
[day2-pdf]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/output/pdf/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pdf
[day2-ppt]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/slides/IPA_LLM_Agent_업무자동화_Day2_2026_STUDENT_READY_176p.pptx
[day3-guide]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day3/2026_Day3_수강생_실습가이드.md
[day3-setup]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day3/2026_Day3_수강생_실습가이드.md#설치로그인
[day3-notebook]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day3/day3_review_intelligence_lab.ipynb
[day3-executed]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day3/day3_review_intelligence_lab.executed.ipynb
[day3-pdf]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/output/pdf/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pdf
[day3-ppt]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx
[day3-zip]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/raw/refs/heads/codex/day3-review-intelligence/dist/day3-student-code-bundle.zip
[day4-guide]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day4/2026_Day4_수강생_실습가이드.md
[day4-instructor]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day4/2026_Day4_설계_및_강사운영안.md
[day4-notebook]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day4/day4_pr_document_automation.ipynb
[day4-executed]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day4/day4_pr_document_automation.executed.ipynb
[day4-ppt]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/slides/IPA_LLM_Agent_업무자동화_Day4_2026_PR_DOCUMENT.pptx
[day4-pdf]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/output/pdf/IPA_LLM_Agent_업무자동화_Day4_2026_PR_DOCUMENT.pdf
[day4-zip]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/raw/refs/heads/codex/day4-document-automation/dist/day4-student-code-bundle.zip
[day4-wbs]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/WBS_Gantt.xlsx
[day4-exam]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/Exam_Grading.xlsx
[day4-word-before]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/Resume_Before.docx
[day4-word-after]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/Resume_After.docx
[day4-brief]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/Project_Brief.pptx
[day4-brief-pdf]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/outputs/day4-document-automation/Project_Brief.pdf
[day5-project]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day5/미니프로젝트_사전안내.md
[day5-record]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day4-document-automation/materials/day5/개선기록_템플릿.md
[roadmap]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/materials/day3/4·5주차_운영안_및_미니프로젝트.md
[instructor]: https://github.com/smilesjcha/llm-agent-and-workflow-automation/blob/codex/day3-review-intelligence/docs/INSTRUCTOR_GUIDE.md
