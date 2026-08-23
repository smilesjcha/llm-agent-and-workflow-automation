"""Build and execute the period 4-6 Ollama and Agent software lab notebook."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "materials/day1/04_ollama_agent_workflow.ipynb"
EXECUTED = ROOT / "materials/day1/04_ollama_agent_workflow.executed.ipynb"


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


def build_notebook():
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    }
    notebook["cells"] = [
        markdown(
            """
# 1일차 4-6차시 · Ollama로 이어지는 Agent 소프트웨어 실습

12시부터 한 notebook을 계속 사용합니다.

- **4차시**: Python·Git·Ollama 설치와 서버·모델 상태를 코드로 진단합니다.
- **5차시**: fixture와 Ollama가 제안한 Tool Call을 같은 안전 실행기로 검증합니다.
- **6차시**: 같은 회의 입력을 LangChain LCEL의 fixture/Ollama provider로 실행합니다.

Ollama가 없어도 notebook은 중단되지 않습니다. 설치된 사람은 실제 모델을 호출하고, 미설치·서버 중단·모델 없음은 `fallback_reason`을 남긴 뒤 같은 계약을 fixture로 실행합니다.
"""
        ),
        markdown(
            """
## 4차시 · 저장소와 Python 실행 위치 확인

notebook을 어느 폴더에서 열어도 상위 경로에서 저장소 루트를 찾습니다. 회사 경로·사용자 홈·secret은 출력하지 않습니다.
"""
        ),
        code(
            """
from pathlib import Path
import json, os, platform, sys

START = Path.cwd().resolve()
ROOT = next((p for p in (START, *START.parents) if (p / "src").exists()), None)
assert ROOT is not None, "현재 폴더의 상위 경로에서 src를 찾지 못했습니다."
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
print({"python": platform.python_version(), "repo_ready": (ROOT / "tests").exists()})
"""
        ),
        markdown(
            """
## 4차시 · Ollama 설치·서버·모델 진단

공식 안내:

- macOS 설치: https://docs.ollama.com/macos
- Quickstart: https://docs.ollama.com/quickstart
- 수업 모델: https://ollama.com/library/qwen3:4b

강의 전 설치한 뒤 터미널에서 확인합니다.

```bash
ollama --version
ollama run qwen3:4b
ollama list
```

`qwen3:4b`는 약 2.5GB이므로 수업 시작 후 전체가 다운로드를 기다리지 않습니다. 강사는 전날 준비하고, 수강생은 모델이 없으면 fixture 경로로 수업을 계속합니다.
"""
        ),
        code(
            """
from src.ollama_tool_agent import probe_ollama

ollama_status = probe_ollama()
print(json.dumps(ollama_status, ensure_ascii=False, indent=2))
"""
        ),
        markdown(
            """
### 환경 상태에 따른 진행 경로

| 상태 | 이번 수업에서 할 일 |
|---|---|
| CLI·서버·모델 준비 | `provider="ollama"`로 실제 모델 호출 |
| CLI만 설치·서버 중단 | Ollama 앱/서버를 시작한 뒤 다시 진단 |
| 서버 준비·모델 없음 | 강의 후 모델 설치, 수업은 fixture로 계속 |
| Ollama 미설치 | fixture로 모든 정책·Tool·Graph 실습 완료 |
"""
        ),
        code(
            """
import subprocess

narrow_test = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "tests/test_ollama_tool_agent.py"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
print(narrow_test.stdout.strip())
assert narrow_test.returncode == 0, narrow_test.stderr
"""
        ),
        markdown(
            """
## 5차시 · 모델의 제안과 코드의 실행 권한 분리

Ollama는 `read_public_text` 사용을 **제안**합니다. 실제 실행은 `SafeToolExecutor`가 tool name, arguments, workspace 경계를 다시 검사합니다.
"""
        ),
        code(
            """
from src.ollama_tool_agent import run_tool_agent

fixture_success = run_tool_agent(
    "data/meeting_sample_ko.txt를 읽어줘",
    workspace=ROOT,
    provider="fixture",
)
print(json.dumps({
    "provider": fixture_success["provider_used"],
    "tool_call": fixture_success["tool_call"],
    "status": fixture_success["status"],
    "error_code": fixture_success["tool_result"]["error_code"],
}, ensure_ascii=False, indent=2))
"""
        ),
        code(
            """
blocked = run_tool_agent(
    "../../private.txt를 읽어줘",
    workspace=ROOT,
    provider="fixture",
)
print(json.dumps({
    "status": blocked["status"],
    "error_code": blocked["tool_result"]["error_code"],
    "needs_human_review": blocked["needs_human_review"],
}, ensure_ascii=False, indent=2))
assert blocked["tool_result"]["error_code"] == "POLICY_BLOCKED"
"""
        ),
        markdown(
            """
## 5차시 · Ollama 실제 Tool Call 제안

아래 셀은 항상 `provider="ollama"`를 요청합니다. 준비된 컴퓨터에서는 실제 `qwen3:4b` 응답을 사용하고, 현재 컴퓨터처럼 미설치 상태이면 fixture로 복구한 이유가 결과에 남습니다.
"""
        ),
        code(
            """
MODEL = "qwen3:4b"
ollama_tool_result = run_tool_agent(
    "data/meeting_sample_ko.txt를 읽어줘",
    workspace=ROOT,
    provider="ollama",
    model=MODEL,
    allow_fallback=True,
)
print(json.dumps({
    "provider_requested": ollama_tool_result["provider_requested"],
    "provider_used": ollama_tool_result["provider_used"],
    "fallback_reason": ollama_tool_result["fallback_reason"],
    "tool_call": ollama_tool_result["tool_call"],
    "tool_status": ollama_tool_result["status"],
    "automatic_email": ollama_tool_result["automatic_email"],
}, ensure_ascii=False, indent=2))
"""
        ),
        code(
            """
OUTPUT = ROOT / "output/notebook-ollama"
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "ollama_tool_result.json").write_text(
    json.dumps(ollama_tool_result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("saved:", OUTPUT / "ollama_tool_result.json")
"""
        ),
        markdown(
            """
### 5차시 · 점심 전 전체 회귀 test

새로 만든 Ollama 경로뿐 아니라 기존 Agent·LangChain·LangGraph·STT 계약이 함께 유지되는지 전체 Day 1 test를 실행합니다. 실패하면 마지막 줄보다 **첫 번째 오류**부터 복구합니다.
"""
        ),
        code(
            """
full_test = subprocess.run(
    [sys.executable, "-m", "pytest", "-q"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)
print(full_test.stdout.strip())
assert full_test.returncode == 0, full_test.stderr
"""
        ),
        markdown(
            """
## 6차시 · LangChain LCEL Provider 교체

같은 transcript와 Pydantic schema를 유지하고 provider만 바꿉니다.

`Prompt → fixture/Ollama → Pydantic Parser → Policy Validator`

Ollama용 선택 패키지는 다음과 같이 설치합니다.

```bash
python -m pip install -r requirements-local-llm-optional.txt
```
"""
        ),
        code(
            """
from src.langchain_lab import run_langchain_lab

transcript = (ROOT / "data/meeting_sample_ko_12min.txt").read_text(encoding="utf-8")
fixture_chain = run_langchain_lab(transcript, provider="fixture")
print(json.dumps({
    "provider_used": fixture_chain["provider_used"],
    "pipeline": fixture_chain["pipeline"],
    "checks": fixture_chain["checks"],
}, ensure_ascii=False, indent=2))
"""
        ),
        code(
            """
ollama_chain = run_langchain_lab(
    transcript,
    provider="ollama",
    model=MODEL,
    allow_fallback=True,
)
print(json.dumps({
    "provider_requested": ollama_chain["provider_requested"],
    "provider_used": ollama_chain["provider_used"],
    "fallback_reason": ollama_chain["fallback_reason"],
    "checks": ollama_chain["checks"],
}, ensure_ascii=False, indent=2))
"""
        ),
        markdown(
            """
## 6차시 완료 확인

- [ ] Ollama 설치·서버·모델 상태가 JSON으로 출력됐다.
- [ ] `tests/test_ollama_tool_agent.py` 4개가 통과했다.
- [ ] 정상 파일은 읽고 workspace 밖 경로는 `POLICY_BLOCKED`로 멈췄다.
- [ ] Ollama 요청과 실제 사용 provider가 결과에 따로 남았다.
- [ ] 전체 Day 1 test가 `23 passed`로 끝났다.
- [ ] LCEL은 fixture/Ollama 어느 경로에서도 같은 typed schema와 정책 검사를 유지했다.

다음에는 `07_langchain_langgraph_workflow.ipynb`를 열어 이 결과를 LangGraph 사람 승인 State로 넘깁니다.
"""
        ),
    ]
    return notebook


def main() -> None:
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    nbf.write(notebook, NOTEBOOK)

    executed = nbf.from_dict(notebook)
    processor = ExecutePreprocessor(timeout=180, kernel_name="python3")
    processor.preprocess(executed, {"metadata": {"path": str(ROOT)}})
    nbf.write(executed, EXECUTED)
    print(f"wrote {NOTEBOOK.relative_to(ROOT)}")
    print(f"wrote {EXECUTED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
