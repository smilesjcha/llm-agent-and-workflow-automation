"""Build the Day 3 Review Intelligence student and executed notebooks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "materials/day3/day3_review_intelligence_lab.ipynb"

_counter = 0


def _id(kind: str) -> str:
    global _counter
    _counter += 1
    return f"day3-{kind}-{_counter:03d}"


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": _id("md"),
        "metadata": {},
        "source": dedent(source).strip().splitlines(True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "id": _id("code"),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(True),
    }


def build_notebook() -> dict:
    global _counter
    _counter = 0
    cells = [
        md(
            """
            # 3일차 · Review Intelligence Service

            실제 Pull Request의 `diff`를 입력으로 받아 **Review Contract → Diff Parser → Context Pack → Provider Adapter → Hybrid Review → Human Review → Golden Evaluation → GitHub Dry-run**을 완성합니다.

            - 기본 `Run All`: fixture 기반, 네트워크 0회, 외부 서비스 변경 0회
            - 선택 확장: Ollama 또는 OpenAI adapter, localhost UI, GitHub Draft PR
            - 최종 산출물: 차시별 JSON 8개, 검토 Markdown, 실행 manifest
            """
        ),
        md(
            """
            ## 오늘의 서비스 구조

            ```text
            PR diff
              └─ parse → allowed context → rule + optional LLM
                                     └─ evidence grounding
                                            └─ Human Review
                                                   ├─ golden evaluation
                                                   └─ GitHub dry-run
            ```

            LLM은 후보를 제안할 수 있지만, 실제 diff에 없는 파일·라인은 제거합니다. Push·PR·comment·merge는 Notebook이 실행하지 않습니다.
            """
        ),
        code(
            """
            from pathlib import Path
            from datetime import datetime, timezone
            import importlib.util
            import json
            import os
            import subprocess
            import sys

            def find_workspace(start: Path) -> Path:
                for candidate in (start, *start.parents):
                    if (candidate / "requirements-day3.txt").exists() and (candidate / "labs/day3").exists():
                        return candidate
                raise RuntimeError("WORKSPACE_ROOT_NOT_FOUND")

            ROOT = find_workspace(Path.cwd().resolve())
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))

            print({
                "workspace": ROOT.name,
                "python": sys.version.split()[0],
                "branch": subprocess.run(
                    ["git", "branch", "--show-current"], cwd=ROOT, text=True,
                    capture_output=True, check=False,
                ).stdout.strip(),
            })
            """
        ),
        md(
            """
            ## 최초 1회 설치

            아래 `INSTALL_DAY3 = True`는 현재 Notebook Kernel에 필요한 library가 없을 때만 사용합니다. 설치 후 Kernel을 다시 시작하고 `False`로 되돌립니다.

            선택 provider는 별도 opt-in입니다. `.env`의 실제 값은 출력·캡처·Git commit하지 않습니다.
            """
        ),
        code(
            """
            INSTALL_DAY3 = False
            required_modules = ["pytest", "pydantic", "langchain_core", "langgraph", "dotenv"]
            missing = [name for name in required_modules if importlib.util.find_spec(name) is None]
            if missing and INSTALL_DAY3:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements-day3.txt")],
                    cwd=ROOT, check=True,
                )
                missing = [name for name in required_modules if importlib.util.find_spec(name) is None]
            assert not missing, (
                "DAY3_DEPENDENCIES_MISSING: INSTALL_DAY3를 True로 바꾸고 이 셀만 실행하세요. "
                f"missing={missing}"
            )
            print({
                "environment_ready": True,
                "install_command": "python -m pip install -r requirements-day3.txt",
                "network_used_by_run_all": False,
            })
            """
        ),
        code(
            """
            from dotenv import load_dotenv
            from labs.day3.review_copilot.errors import stable_error_code
            load_dotenv(dotenv_path=ROOT / ".env", override=False)

            REFERENCE_OUT = ROOT / "output/course-labs/day3-v2"
            OUT = REFERENCE_OUT / "student-run"
            OUT.mkdir(parents=True, exist_ok=True)
            RUN_STARTED_AT_UTC = datetime.now(timezone.utc).isoformat()
            result_files = []
            test_evidence = []
            MAIN_OUTPUTS = [
                "01_review_contract.json",
                "02_parsed_diff.json",
                "03_context_pack.json",
                "04_candidate_review.json",
                "05_hybrid_review.json",
                "06_human_review.json",
                "07_evaluation.json",
                "08_release_evidence.json",
            ]

            def save_json(name: str, payload: dict) -> Path:
                path = OUT / name
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
                if name not in result_files:
                    result_files.append(name)
                print({"saved": str(path.relative_to(ROOT))})
                return path

            def save_text(name: str, payload: str) -> Path:
                path = OUT / name
                path.write_text(payload.rstrip() + "\\n", encoding="utf-8")
                if name not in result_files:
                    result_files.append(name)
                print({"saved": str(path.relative_to(ROOT))})
                return path

            def run_command(*args: str) -> dict:
                completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
                display = list(args)
                if display and display[0] == sys.executable:
                    display[0] = "python"
                evidence = {
                    "command": " ".join(display),
                    "return_code": completed.returncode,
                    "stdout_tail": completed.stdout.strip().splitlines()[-6:],
                    "stderr_tail": completed.stderr.strip().splitlines()[-6:],
                }
                print(json.dumps(evidence, ensure_ascii=False, indent=2))
                return evidence

            def expected_error(action) -> str:
                try:
                    action()
                except (OSError, RuntimeError, TypeError, ValueError) as exc:
                    return stable_error_code(exc)
                raise AssertionError("EXPECTED_FAILURE_NOT_RAISED")

            print({
                "reference_outputs": str(REFERENCE_OUT.relative_to(ROOT)),
                "my_outputs": str(OUT.relative_to(ROOT)),
                "external_write": False,
            })
            """
        ),
        md(
            """
            # 1차시 · Review Contract

            **이론**: 좋은 리뷰는 취향이 아니라 재현 가능한 결함을 다룹니다. `P0~P3`, 변경 라인, 영향, 근거, 최소 교정을 한 계약으로 고정합니다.

            **코드 실습**: Review Policy와 Finding Schema를 생성하고, 잘못된 severity가 차단되는지 확인합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.contracts import ReviewFinding, ReviewPolicy

            policy = ReviewPolicy()
            contract = {
                "policy": policy.to_dict(),
                "required_finding_fields": [
                    "path", "line", "severity", "title", "impact",
                    "evidence", "correction", "rule_id", "source", "confidence",
                ],
                "severity_meaning": {
                    "P0": "즉시 차단 · 보안 또는 치명적 데이터 손실",
                    "P1": "merge 전 수정 · 주요 기능/권한 위험",
                    "P2": "가급적 수정 · 운영 안정성/관측성",
                    "P3": "낮은 위험 · 명확성/유지보수성",
                },
                "external_write": False,
            }
            save_json("01_review_contract.json", contract)
            contract
            """
        ),
        md(
            """
            ### 실패 조건 실험

            `P5`처럼 계약에 없는 severity는 조용히 통과시키지 않습니다. Error code가 일정해야 UI·test·CI가 같은 실패를 다룰 수 있습니다.
            """
        ),
        code(
            """
            invalid_severity_error = expected_error(lambda: ReviewFinding(
                path="src/demo.py", line=1, severity="P5", title="오류",
                impact="영향", evidence="근거", correction="교정", rule_id="demo",
            ))
            assert invalid_severity_error == "FINDING_SEVERITY_INVALID"
            print({"expected_failure": invalid_severity_error})
            """
        ),
        md(
            """
            **직접 수정 과제**

            1. `contract["severity_meaning"]`을 본인 팀의 기준으로 다시 적습니다.
            2. “문체 취향”이 P1이 될 수 없는 이유를 한 문장으로 설명합니다.
            3. 결과 파일 `01_review_contract.json`을 열어 schema를 확인합니다.
            """
        ),
        md(
            """
            # 2차시 · Unified Diff

            **이론**: 전체 저장소를 모델에 보내지 않고 변경된 파일과 추가 라인만 읽습니다. Review comment의 라인 번호는 추측하지 않고 hunk header에서 계산합니다.

            **코드 실습**: 실제 PR fixture를 parse하고, 절대 경로가 섞인 diff를 차단합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.diff_parser import parse_unified_diff
            from labs.day3.review_copilot.workspace import read_workspace_text

            DIFF_PATH = "labs/day3/review_copilot/fixtures/meeting_export_pr.diff"
            diff_text = read_workspace_text(DIFF_PATH, workspace_root=ROOT)
            parsed = parse_unified_diff(diff_text)
            parsed_payload = parsed.to_dict()
            save_json("02_parsed_diff.json", parsed_payload)
            print({
                "changed_paths": parsed_payload["changed_paths"],
                "added_line_count": len(parsed_payload["added_lines"]),
                "first_added_line": parsed_payload["added_lines"][0],
            })
            """
        ),
        code(
            """
            blocked_diff = "+++ /tmp/private.py\\n@@ -0,0 +1 @@\\n+token = 1"
            diff_path_error = expected_error(lambda: parse_unified_diff(blocked_diff))
            assert diff_path_error == "DIFF_PATH_BLOCKED"
            print({"expected_failure": diff_path_error})
            """
        ),
        md(
            """
            ### 직접 코딩 · Multi-hunk Line Mapping

            아래 함수는 완성된 서비스 함수를 호출하지 않고 hunk header의 새 파일 시작 번호를 직접 읽습니다. 두 hunk가 떨어져 있어도 추가 라인의 위치가 이어서 증가하지 않는다는 점을 확인합니다.
            """
        ),
        code(
            """
            import re

            LEARNING_MULTI_HUNK_DIFF = \"\"\"--- a/src/sample.py
            +++ b/src/sample.py
            @@ -1,2 +1,3 @@
             keep = True
            +first_added = 1
             keep_too = True
            @@ -10,2 +11,3 @@
             later = True
            +second_added = 2
             finish = True
            \"\"\"

            def learner_added_line_map(diff: str) -> list[tuple[str, int, str]]:
                current_path = ""
                new_line = None
                added = []
                for raw in diff.splitlines():
                    if raw.startswith("+++ b/"):
                        current_path = raw[6:]
                        continue
                    hunk = re.match(r"^@@ -\\d+(?:,\\d+)? \\+(\\d+)(?:,\\d+)? @@", raw)
                    if hunk:
                        new_line = int(hunk.group(1))
                        continue
                    if new_line is None:
                        continue
                    if raw.startswith("+") and not raw.startswith("+++"):
                        added.append((current_path, new_line, raw[1:]))
                        new_line += 1
                    elif raw.startswith(" "):
                        new_line += 1
                return added

            learner_mapping = learner_added_line_map(LEARNING_MULTI_HUNK_DIFF)
            assert [(path, line) for path, line, _ in learner_mapping] == [
                ("src/sample.py", 2),
                ("src/sample.py", 12),
            ]
            learner_mapping
            """
        ),
        md(
            """
            **직접 수정 과제**

            `fixtures/cases/08_safe_negative.diff`로 입력을 바꿔 실행합니다. 변경 라인 수와 finding 수가 같은 개념이 아닌 이유를 결과로 설명합니다.
            """
        ),
        md(
            """
            # 3차시 · Context Pack

            **이론**: 모델 성능보다 먼저 “무엇을 보여줄지”를 결정합니다. 코드 리뷰에 필요한 경로·변경 라인·품질 규칙만 포함하고 credential·환경값·무관한 파일은 제외합니다.

            **코드 실습**: allowlist 기반 context를 만들고 private field와 workspace 밖 파일이 제외되는지 확인합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.context_builder import build_context_pack
            from labs.day3.review_copilot.workspace import read_workspace_json

            project_context = read_workspace_json(
                "labs/day3/review_copilot/fixtures/project_context.json",
                workspace_root=ROOT,
            )
            project_context["private_customer_note"] = "이 값은 context에 들어가면 안 됩니다."
            context_pack = build_context_pack(
                parsed,
                policy=policy,
                project_context=project_context,
                workspace_root=ROOT,
            )
            assert "private_customer_note" not in context_pack["project_context"]
            assert "credentials" in context_pack["excluded_data"]
            save_json("03_context_pack.json", context_pack)
            context_pack
            """
        ),
        code(
            """
            from labs.day3.review_copilot.workspace import resolve_workspace_path

            workspace_error = expected_error(lambda: resolve_workspace_path(
                ROOT.parent / "outside.txt", workspace_root=ROOT, must_exist=False,
            ))
            context_budget_error = expected_error(lambda: build_context_pack(
                parsed, policy=policy, project_context=project_context,
                workspace_root=ROOT, max_bytes=20,
            ))
            assert workspace_error == "WORKSPACE_PATH_BLOCKED"
            assert context_budget_error == "CONTEXT_BUDGET_EXCEEDED"
            print({
                "workspace_expected_failure": workspace_error,
                "budget_expected_failure": context_budget_error,
            })
            """
        ),
        md(
            """
            ### 직접 코딩 · Context Allowlist

            Context Pack에 들어갈 업무 설명을 직접 고릅니다. 새 field가 생겼다는 이유만으로 자동 포함하지 않는 것이 기본 원칙입니다.
            """
        ),
        code(
            """
            PUBLIC_CONTEXT_FIELDS = {"service_name", "purpose", "runtime", "quality_rules"}

            def learner_public_context(raw: dict) -> dict:
                return {
                    key: raw[key]
                    for key in sorted(raw)
                    if key in PUBLIC_CONTEXT_FIELDS and not key.startswith("private_")
                }

            learner_context = learner_public_context(project_context)
            assert learner_context == context_pack["project_context"]
            assert "private_customer_note" not in learner_context
            print({"included": sorted(learner_context), "excluded": ["private_customer_note"]})
            """
        ),
        md(
            """
            **Codex Task · Context 축소**

            ```text
            목표: Context Pack에 runtime 필드는 유지하고 private_* 필드는 절대 포함하지 않는다.
            허용 파일: labs/day3/review_copilot/context_builder.py, tests/test_day3_review_copilot.py
            필수 test: 허용 field 1개, private field 차단 1개
            금지: repository 전체 읽기, .env 읽기, assertion 약화, commit/push
            완료: focused test와 git diff --check를 사람이 확인
            ```
            """
        ),
        md(
            """
            # 4차시 · Provider Adapter

            **이론**: Business logic이 특정 모델 SDK에 묶이지 않도록 `review(prompt)` 경계를 둡니다. Fixture 결과를 live 결과로 속이지 않고 `provider_requested`, `provider_used`, `fallback_reason`을 함께 기록합니다.

            **코드 실습**: fixture 응답과 연결 불가 provider의 fallback을 비교합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.providers import (
                FixtureReviewProvider,
                UnavailableReviewProvider,
                run_provider,
            )

            fixture_payload = read_workspace_json(
                "labs/day3/review_copilot/fixtures/provider_fixture.json",
                workspace_root=ROOT,
            )
            fixture = FixtureReviewProvider(fixture_payload["responses"])
            provider_prompt = {
                "case_id": fixture_payload["case_id"],
                "contract": "ReviewFinding",
                "context": context_pack,
                "added_lines": parsed_payload["added_lines"],
            }
            fixture_result = run_provider(
                requested=fixture, fallback=fixture, prompt=provider_prompt, allow_fallback=True,
            )
            fallback_result = run_provider(
                requested=UnavailableReviewProvider("openai", "OPENAI_NOT_CONFIGURED"),
                fallback=fixture, prompt=provider_prompt, allow_fallback=True,
            )
            assert fixture_result["model"] == "deterministic-review-fixture-v1"
            assert fixture_result["schema_valid"] is True
            assert fallback_result["provider_requested"] == "openai"
            assert fallback_result["provider_used"] == "fixture"
            assert fallback_result["model"] == "deterministic-review-fixture-v1"
            assert fallback_result["schema_valid"] is True
            assert fallback_result["fallback_reason"] == "OPENAI_NOT_CONFIGURED"
            save_json("04_candidate_review.json", fixture_result)
            print(json.dumps({
                "fixture": fixture_result,
                "fallback_provenance": {
                    key: fallback_result[key]
                    for key in (
                        "provider_requested", "provider_used", "requested_model",
                        "model", "schema_valid", "fallback_reason",
                    )
                },
            }, ensure_ascii=False, indent=2))
            """
        ),
        md(
            """
            ### 선택 실험 · Ollama / OpenAI

            기본값은 실행하지 않습니다. 본인 환경에서만 `.env`에 opt-in을 설정합니다.

            ```text
            DAY3_LIVE_PROVIDER=ollama 또는 openai
            OLLAMA_LIVE_OPT_IN=1 또는 OPENAI_LIVE_OPT_IN=1
            OLLAMA_MODEL=qwen3:4b
            OPENAI_MODEL=<본인 계정에서 사용 가능한 모델>
            ```

            최초 1회 설치: OpenAI는 `python -m pip install -r requirements-openai-optional.txt`, Ollama는 `python -m pip install -r requirements-local-llm-optional.txt`를 사용합니다.

            API key는 Notebook 출력·스크린샷·Git에 남기지 않습니다.
            """
        ),
        code(
            """
            RUN_OPTIONAL_LIVE_PROVIDER = False
            live_provider_summary = {
                "status": "SKIPPED",
                "reason": "LIVE_PROVIDER_OPT_IN_REQUIRED",
                "provider_requested": os.getenv("DAY3_LIVE_PROVIDER", "fixture"),
                "provider_used": None,
                "credential_value_printed": False,
            }

            if RUN_OPTIONAL_LIVE_PROVIDER:
                from labs.day3.review_copilot.providers import LangChainReviewProvider

                class JsonReviewRunnable:
                    def __init__(self, model):
                        self.model = model

                    def invoke(self, prompt):
                        system = (
                            "Return JSON only: {\\\"candidates\\\": [ReviewFinding candidates]}. "
                            "Use only supplied added lines; never invent runtime results."
                        )
                        return self.model.invoke([
                            ("system", system),
                            ("human", json.dumps(prompt, ensure_ascii=False)),
                        ])

                requested_name = os.getenv("DAY3_LIVE_PROVIDER", "").strip().lower()
                if requested_name == "ollama" and os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1":
                    from langchain_ollama import ChatOllama
                    model = ChatOllama(model=os.getenv("OLLAMA_MODEL", "qwen3:4b"), temperature=0)
                elif requested_name == "openai" and os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1":
                    from langchain_openai import ChatOpenAI
                    model = ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0, timeout=30)
                else:
                    raise RuntimeError("LIVE_PROVIDER_OPT_IN_REQUIRED")

                live_result = run_provider(
                    requested=LangChainReviewProvider(JsonReviewRunnable(model), name=requested_name),
                    fallback=fixture,
                    prompt=provider_prompt,
                    allow_fallback=True,
                )
                live_provider_summary = {
                    key: live_result.get(key)
                    for key in (
                        "status", "provider_requested", "provider_used", "requested_model",
                        "model", "schema_valid", "fallback_reason",
                    )
                }

            print(json.dumps(live_provider_summary, ensure_ascii=False, indent=2))
            """
        ),
        md(
            """
            # 5차시 · Hybrid Review

            **이론**: 정규식 rule은 빠르고 재현 가능하지만 맥락에 약합니다. LLM 후보는 맥락에 강하지만 근거를 발명할 수 있습니다. 두 결과를 합친 뒤 실제 추가 라인에 연결되지 않은 후보를 버립니다.

            **코드 실습**: rule baseline과 provider 후보를 결합하고 hallucinated line이 제거되는지 확인합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.review_engine import merge_grounded_candidates
            from labs.day3.review_copilot.test_evidence import collect_focused_test_evidence

            hybrid_draft = merge_grounded_candidates(parsed, fixture_result)
            hybrid_payload = hybrid_draft.to_dict()
            component_test_evidence = collect_focused_test_evidence(workspace_root=ROOT)
            assert hybrid_payload["status"] == "DRAFT"
            assert component_test_evidence["status"] == "PASSED"
            hybrid_payload["test_evidence"] = component_test_evidence
            assert all(
                any(
                    line["path"] == finding["path"] and line["line"] == finding["line"]
                    for line in parsed_payload["added_lines"]
                )
                for finding in hybrid_payload["findings"]
            )
            assert all(finding["line"] != 999 for finding in hybrid_payload["findings"])
            save_json("05_hybrid_review.json", hybrid_payload)
            hybrid_payload
            """
        ),
        md(
            """
            ### 직접 코딩 · Evidence Grounding

            LLM 후보의 path와 line이 실제 추가 라인 집합에 있을 때만 남기는 최소 Gate를 직접 작성합니다. 이 Gate가 없으면 자연스러운 문장도 PR의 엉뚱한 줄을 가리킬 수 있습니다.
            """
        ),
        code(
            """
            def learner_grounded_candidates(
                added_lines: list[dict], candidates: list[dict],
            ) -> list[dict]:
                allowed = {(item["path"], item["line"]) for item in added_lines}
                seen = set()
                grounded = []
                for candidate in candidates:
                    location = (candidate.get("path"), candidate.get("line"))
                    key = (*location, candidate.get("rule_id"))
                    if location in allowed and key not in seen:
                        grounded.append(candidate)
                        seen.add(key)
                return grounded

            learning_candidates = [
                fixture_result["candidates"][0],
                fixture_result["candidates"][0],
                {**fixture_result["candidates"][0], "line": 999},
            ]
            learner_grounded = learner_grounded_candidates(
                parsed_payload["added_lines"], learning_candidates,
            )
            assert len(learner_grounded) == 1
            assert learner_grounded[0]["line"] != 999
            learner_grounded
            """
        ),
        code(
            """
            rule_ids = {finding["rule_id"] for finding in hybrid_payload["findings"]}
            expected_rules = {
                "unsafe-dynamic-execution",
                "external-write-without-approval",
                "broad-exception-boundary",
            }
            assert expected_rules <= rule_ids
            print({
                "finding_count": len(hybrid_payload["findings"]),
                "rule_ids": sorted(rule_ids),
                "invented_line_removed": True,
            })
            """
        ),
        md(
            """
            **직접 수정 과제**

            `fixtures/cases/06_secret_logging.diff`를 parse한 뒤 deterministic rule 결과를 비교합니다. 새 rule을 추가할 때는 허용 case와 가장 위험한 실패 case를 한 쌍으로 작성합니다.
            """
        ),
        md(
            """
            # 6차시 · Human Review · LangGraph

            **이론**: 자동 리뷰는 초안입니다. 사람은 `approve`, `edit`, `reject` 중 하나를 선택하고 이유를 남깁니다. LangGraph `interrupt()`는 이 판단 직전에 workflow를 멈추고 같은 `thread_id`로 재개합니다.

            **코드 실습**: 먼저 순수 함수 계약을 확인하고, 다음 셀에서 실제 interrupt/resume을 실행합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.human_review import apply_human_review

            pending_review = apply_human_review(
                hybrid_draft,
                decision=None,
                reviewer=None,
                rationale=None,
            )
            pending_payload = pending_review.to_dict()
            assert pending_payload["status"] == "REVIEW_REQUIRED"
            assert pending_payload["human_reviewed"] is False
            assert pending_payload["external_write"] is False
            pending_payload
            """
        ),
        md(
            """
            ### LangGraph Start

            이 셀은 interrupt payload까지 실행합니다. Notebook을 직접 진행할 때 `__interrupt__`의 질문과 finding을 읽은 다음 아래 결정 셀로 이동합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.langgraph_review import build_review_graph

            review_graph = build_review_graph()
            REVIEW_THREAD_ID = "day3-learner-review-001"
            graph_config = {"configurable": {"thread_id": REVIEW_THREAD_ID}}
            graph_start = review_graph.invoke(
                {"draft": hybrid_payload, "status": "CREATED", "audit": [], "external_write": False},
                config=graph_config,
            )
            interrupt_items = graph_start.get("__interrupt__", ())
            assert interrupt_items
            print(json.dumps(interrupt_items[0].value, ensure_ascii=False, indent=2))
            """
        ),
        md(
            """
            ### LangGraph Resume

            `REVIEW_DECISION`을 `approve`, `edit`, `reject` 중 하나로 바꿉니다. 이 Notebook의 기본 실행은 `approve`이며 GitHub 쓰기는 여전히 발생하지 않습니다.
            """
        ),
        code(
            """
            from langgraph.types import Command

            REVIEW_DECISION = "approve"
            REVIEWER = "수강생"
            REVIEW_RATIONALE = "interrupt payload의 근거 라인을 확인했습니다."
            REVIEW_EDITED_FINDINGS = (
                hybrid_payload["findings"] if REVIEW_DECISION == "edit" else None
            )
            assert REVIEW_DECISION in {"approve", "edit", "reject"}
            resume_payload = {
                "decision": REVIEW_DECISION,
                "reviewer": REVIEWER,
                "rationale": REVIEW_RATIONALE,
            }
            if REVIEW_EDITED_FINDINGS is not None:
                resume_payload["edited_findings"] = REVIEW_EDITED_FINDINGS
            graph_final = review_graph.invoke(
                Command(resume=resume_payload),
                config=graph_config,
            )
            graph_final.pop("__interrupt__", None)
            assert graph_final["external_write"] is False
            reviewed = apply_human_review(
                hybrid_draft,
                decision=REVIEW_DECISION,
                reviewer=REVIEWER,
                rationale=REVIEW_RATIONALE,
                edited_findings=REVIEW_EDITED_FINDINGS,
            )
            reviewed_payload = reviewed.to_dict()
            expected_review_status = {
                "approve": "APPROVED", "edit": "EDITED", "reject": "REJECTED",
            }[REVIEW_DECISION]
            assert reviewed_payload["status"] == expected_review_status
            assert reviewed_payload["human_reviewed"] is True
            save_json("06_human_review.json", reviewed_payload)
            save_json("06_langgraph_transition.json", {
                "thread_id": REVIEW_THREAD_ID,
                "decision": REVIEW_DECISION,
                "final_state": graph_final,
                "external_write": False,
            })
            graph_final
            """
        ),
        md(
            """
            # 7차시 · Golden Evaluation

            **이론**: “그럴듯함” 대신 정답이 알려진 작은 case set으로 Precision, Recall, F1을 계산합니다. 안전한 negative case와 예상된 parser failure도 포함해야 false positive와 실패 계약을 볼 수 있습니다.

            **코드 실습**: 8개 synthetic diff를 일괄 평가하고 Release Gate를 확인합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.evaluation import evaluate_case_set

            evaluation = evaluate_case_set(
                workspace_root=ROOT,
                manifest_path="labs/day3/review_copilot/fixtures/cases.json",
                golden_path="labs/day3/review_copilot/fixtures/golden_findings.json",
            )
            assert evaluation["case_count"] == 8
            assert evaluation["expected_failure_cases"] >= 1
            assert evaluation["false_positive"] == 0
            assert evaluation["false_negative"] == 0
            assert evaluation["release_decision"] == "READY"
            save_json("07_evaluation.json", evaluation)
            print({
                key: evaluation[key]
                for key in (
                    "case_count", "case_passed", "precision", "recall", "f1",
                    "expected_failure_cases_passed", "release_decision",
                )
            })
            """
        ),
        md(
            """
            ### 직접 코딩 · Precision · Recall · F1

            평가 함수의 숫자를 그대로 믿기 전에 계산식을 직접 구현합니다. 놓친 결함은 false negative, 잘못 지적한 결함은 false positive입니다.
            """
        ),
        code(
            """
            def learner_review_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
                precision = tp / (tp + fp) if tp + fp else 1.0
                recall = tp / (tp + fn) if tp + fn else 1.0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
                return {"precision": precision, "recall": recall, "f1": f1}

            learner_metrics = learner_review_metrics(
                evaluation["true_positive"],
                evaluation["false_positive"],
                evaluation["false_negative"],
            )
            assert round(learner_metrics["f1"], 4) == evaluation["f1"]
            learner_metrics
            """
        ),
        md(
            """
            ### Error Analysis

            아래 표의 `FAIL`이 생기면 점수만 올리지 말고 case별 원인을 분류합니다.

            - False positive: 안전한 코드를 결함으로 잘못 지적
            - False negative: 실제 결함을 놓침
            - Contract failure: parser 또는 schema의 예상 오류 코드 불일치
            """
        ),
        code(
            """
            error_analysis = [item for item in evaluation["results"] if item["status"] != "PASS"]
            print({
                "release_decision": evaluation["release_decision"],
                "failed_cases": error_analysis,
                "next_action": "새 rule 또는 threshold 수정 후 8개 case 전체 재실행",
            })
            """
        ),
        md(
            """
            # 8차시 · Local Service · GitHub PR

            **이론**: Local 결과와 GitHub 외부 행동을 분리합니다. 서비스는 PR 제목·본문·명령을 dry-run으로 만들지만 실행하지 않습니다. 사람은 diff, test, target repository를 확인한 뒤 branch push와 Draft PR을 직접 수행합니다.

            **코드 실습**: 8단계 workflow, Markdown export, focused test, localhost 실행 준비를 완성합니다.
            """
        ),
        code(
            """
            from labs.day3.review_copilot.workflow import run_review_workflow
            from labs.day3.review_copilot.exports import render_review_markdown

            workflow_result = run_review_workflow(
                workspace_root=ROOT,
                diff_path=DIFF_PATH,
                project_context_path="labs/day3/review_copilot/fixtures/project_context.json",
                fixture_path="labs/day3/review_copilot/fixtures/provider_fixture.json",
                decision=REVIEW_DECISION,
                reviewer=REVIEWER,
                rationale=REVIEW_RATIONALE,
                edited_findings=REVIEW_EDITED_FINDINGS,
                repository="smilesjcha/llm-agent-and-workflow-automation",
                base="main",
                branch="codex/day3-review-intelligence",
                test_evidence=component_test_evidence,
            )
            assert workflow_result["status"] == "SUCCESS"
            assert workflow_result["completed_stage"] == 8
            assert workflow_result["external_write"] is False

            for stage_name, payload in workflow_result["stages"].items():
                save_json(f"{stage_name}.json", payload)
            save_text("review_report.md", render_review_markdown(workflow_result))

            release = workflow_result["stages"]["08_release_evidence"]
            assert release["github_dry_run"]["commands_executed"] == []
            assert release["github_dry_run"]["external_write"] is False
            expected_release = (
                "READY_FOR_MANUAL_GITHUB_STEP"
                if REVIEW_DECISION in {"approve", "edit"}
                else "HOLD"
            )
            assert release["decision"] == expected_release
            release
            """
        ),
        md(
            """
            ### Localhost UI

            Terminal에서 아래 명령을 실행한 뒤 `http://127.0.0.1:8765`를 엽니다.

            ```bash
            python -m labs.day3.review_copilot.web_app --port 8765
            ```

            확인 순서: diff 선택 → Review 실행 → finding 유지/수정/제외 → JSON/Markdown 내려받기. GitHub push·comment·merge 버튼은 제공하지 않습니다.
            """
        ),
        code(
            """
            RUN_LOCALHOST_SMOKE = False
            localhost_evidence = {
                "status": "SKIPPED",
                "reason": "별도 Terminal에서 UI를 실행하세요.",
                "url": "http://127.0.0.1:8765",
                "command": "python -m labs.day3.review_copilot.web_app --port 8765",
                "external_write": False,
            }
            if RUN_LOCALHOST_SMOKE:
                smoke = run_command(
                    sys.executable, "-m", "labs.day3.review_copilot.web_app",
                    "--smoke-and-exit", "--port", "0",
                )
                localhost_evidence = {
                    "status": "PASS" if smoke["return_code"] == 0 else "FAIL",
                    "command": smoke["command"],
                    "return_code": smoke["return_code"],
                    "external_write": False,
                }
            save_json("08_localhost_evidence.json", localhost_evidence)
            localhost_evidence
            """
        ),
        md(
            """
            ### Focused Test · GitHub 연결 전

            테스트가 통과해도 자동 승인·자동 merge가 아닙니다. PR 본문에는 직접 실행한 명령과 결과만 기록합니다.
            """
        ),
        code(
            """
            focused = run_command(
                sys.executable, "-m", "pytest", "-q",
                "tests/test_day3_review_copilot.py", "tests/test_day3_pr_guard.py",
            )
            test_evidence.append({
                "name": "day3_focused",
                "command": focused["command"],
                "return_code": focused["return_code"],
                "status": "PASS" if focused["return_code"] == 0 else "FAIL",
            })
            assert focused["return_code"] == 0
            """
        ),
        md(
            """
            ### GitHub · 사람 실행 구간

            ```bash
            git status --short
            git switch -c codex/day3-본인이니셜
            git diff --check
            git add <검토한 파일만>
            git diff --cached --stat
            git commit -m "feat(day3): add reviewed change"
            git push -u origin HEAD
            gh pr create --draft --base main --head codex/day3-본인이니셜
            ```

            PR에서 GitHub Actions 결과와 사람 리뷰를 확인합니다. Codex GitHub 연결이 완료된 저장소만 `@codex review`를 선택적으로 사용합니다. 최종 merge는 사람이 결정합니다.
            """
        ),
        md(
            """
            ## 최종 실행 증거

            아래 manifest는 내 실행 경로, 완료 파일, test, live opt-in 여부를 기록합니다. Credential 값은 기록하지 않습니다.
            """
        ),
        code(
            """
            live_opt_ins = {
                "openai": os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1" and RUN_OPTIONAL_LIVE_PROVIDER,
                "ollama": os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1" and RUN_OPTIONAL_LIVE_PROVIDER,
            }
            manifest = {
                "run_started_at_utc": RUN_STARTED_AT_UTC,
                "run_finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "python_version": sys.version.split()[0],
                "reference_outputs_read_only": str(REFERENCE_OUT.relative_to(ROOT)),
                "student_run_directory": str(OUT.relative_to(ROOT)),
                "completed_periods": [str(number) for number in range(1, 9)],
                "result_files": [str((OUT / name).relative_to(ROOT)) for name in result_files],
                "tests": test_evidence,
                "human_review_decision": REVIEW_DECISION,
                "safety": {
                    "default_lane_network_free": True,
                    "this_run_network_free": not any(live_opt_ins.values()),
                    "live_opt_ins": live_opt_ins,
                    "credential_value_recorded": False,
                    "external_write": False,
                    "automatic_pr_comment": False,
                    "automatic_merge": False,
                },
            }
            save_json("run_manifest.json", manifest)
            manifest
            """
        ),
        md(
            """
            ## 완료 기준

            - `01`~`08` JSON과 `review_report.md`, `run_manifest.json` 생성
            - 8개 golden case PASS 및 F1 확인
            - Human Review decision과 rationale 기록
            - GitHub dry-run의 `commands_executed=[]`, `external_write=false` 확인
            - focused test PASS
            - 선택: localhost UI 실행, Draft PR, CI, 사람 리뷰, `@codex review`

            실패한 경우 결과를 지우지 말고 **명령 → error code → 원인 → 최소 수정 → 재실행** 순서로 남깁니다.
            """
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
            "course_day": 3,
            "period_count": 8,
            "default_network_calls": 0,
            "external_write": False,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=NOTEBOOK_PATH)
    args = parser.parse_args()
    notebook = build_notebook()
    target = args.output if args.output.is_absolute() else ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print({"notebook": str(target.relative_to(ROOT)), "cells": len(notebook["cells"])})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
