"""Generate eight-period runnable notebooks for Day 2-5."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
_cell_counter = 0


def next_cell_id(kind: str) -> str:
    global _cell_counter
    _cell_counter += 1
    return f"{kind}-{_cell_counter:04d}"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": next_cell_id("md"),
        "metadata": {},
        "source": dedent(source).strip().splitlines(True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "id": next_cell_id("code"),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(True),
    }


def notebook(title: str, day: int, cells: list[dict]) -> dict:
    installation_cell = (
        """
        # Run All은 설치가 끝난 환경에서 network 호출 없이 실행합니다.
        # 처음 한 번만 아래 flag를 True로 바꿔 현재 Notebook Kernel에 설치합니다.
        INSTALL_CORE_DEPENDENCIES = False

        dependency_groups = {
            "core": (["pydantic", "pytest", "langchain_core", "langgraph"], ROOT / "requirements-day1.txt"),
        }
        install_flags = {
            "core": INSTALL_CORE_DEPENDENCIES,
        }
        dependency_status = {}
        for group, (modules, requirements_path) in dependency_groups.items():
            missing = [name for name in modules if importlib.util.find_spec(name) is None]
            if missing and install_flags[group]:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_path)],
                    check=True,
                )
                missing = [name for name in modules if importlib.util.find_spec(name) is None]
            dependency_status[group] = {
                "ready": not missing,
                "missing": missing,
                "install_command": f"python -m pip install -r {requirements_path.relative_to(ROOT)}",
                "network_used_by_run_all": bool(install_flags[group]),
            }

        assert dependency_status["core"]["ready"], (
            "CORE_DEPENDENCIES_MISSING: 위 INSTALL_CORE_DEPENDENCIES를 True로 바꾸고 이 셀만 먼저 실행하세요."
        )
        print(json.dumps(dependency_status, ensure_ascii=False, indent=2))

        # faster-whisper model과 공개 음성 다운로드는 2차시 opt-in 셀에서만 실행합니다.
        """
        if day == 2
        else """
        # 최초 1회. 없는 핵심 library가 있을 때만 현재 Notebook Kernel에 설치합니다.
        required = ["pydantic", "pytest", "langchain_core", "langgraph"]
        missing = [name for name in required if importlib.util.find_spec(name) is None]
        if missing:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements-day1.txt")],
                check=True,
            )
        print({"missing_before_install": missing, "environment_ready": True})

        # 실제 STT를 실행할 사람만 requirements-stt-optional.txt를 별도로 설치합니다.
        """
    )
    return {
        "cells": [
            markdown(
                f"""
                # {title}

                하나의 입력을 8개 차시 동안 확장합니다. 웹사이트 확인이 아니라 코드·명령·test·결과 파일을 직접 다루며, 외부 서비스 저장·게시·발송은 dry-run과 사람 승인을 먼저 거칩니다.
                """
            ),
            code(
                """
                from pathlib import Path
                from datetime import datetime, timezone
                import importlib.util, json, os, subprocess, sys

                def find_workspace(start):
                    for candidate in [start, *start.parents]:
                        if (candidate / "requirements-day1.txt").exists() and (candidate / "src").exists():
                            return candidate
                    raise RuntimeError("WORKSPACE_ROOT_NOT_FOUND")

                ROOT = find_workspace(Path.cwd().resolve())
                if str(ROOT) not in sys.path:
                    sys.path.insert(0, str(ROOT))
                print({"workspace": ROOT.name, "python": sys.version.split()[0]})
                """
            ),
            code(installation_cell),
            code(
                f"""
                REFERENCE_OUT = ROOT / {('"output/course-labs/day2-v2"' if day == 2 else f'"output/course-labs/day{day}"')}
                OUT = {('REFERENCE_OUT / "student-run"' if day == 2 else 'REFERENCE_OUT')}
                OUT.mkdir(parents=True, exist_ok=True)

                TRACK_RUN_MANIFEST = {str(day == 2)}
                RUN_STARTED_AT_UTC = datetime.now(timezone.utc).isoformat()
                RUN_RESULT_FILES = []
                RUN_TEST_EVIDENCE = []

                def write_run_manifest():
                    live_opt_ins = {{
                        "openai": os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1",
                        "ollama": os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1",
                        "faster_whisper": os.getenv("FASTER_WHISPER_LIVE_OPT_IN", "0") == "1",
                    }}
                    completed_periods = sorted({{
                        name.split("_", 1)[0]
                        for name in RUN_RESULT_FILES
                        if len(name) >= 3 and name[:2].isdigit() and name[2] == "_"
                    }})
                    manifest = {{
                        "run_started_at_utc": RUN_STARTED_AT_UTC,
                        "python_version": sys.version.split()[0],
                        "reference_outputs_read_only": str(REFERENCE_OUT.relative_to(ROOT)),
                        "student_run_directory": str(OUT.relative_to(ROOT)),
                        "completed_periods": completed_periods,
                        "result_files": [str((OUT / name).relative_to(ROOT)) for name in RUN_RESULT_FILES],
                        "tests": RUN_TEST_EVIDENCE,
                        "safety": {{
                            "default_lane_network_free": True,
                            "this_run_network_free": not any(live_opt_ins.values()),
                            "live_opt_ins": live_opt_ins,
                            "external_write": False,
                            "automatic_email_send": False,
                        }},
                    }}
                    path = OUT / "run_manifest.json"
                    path.write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n",
                        encoding="utf-8",
                    )
                    return path

                def record_test_evidence(name, result):
                    evidence = {{
                        "name": name,
                        "command": result["command"],
                        "return_code": result["returncode"],
                        "status": "PASS" if result["returncode"] == 0 else "FAIL",
                    }}
                    RUN_TEST_EVIDENCE[:] = [
                        item for item in RUN_TEST_EVIDENCE if item["name"] != name
                    ]
                    RUN_TEST_EVIDENCE.append(evidence)
                    if TRACK_RUN_MANIFEST:
                        write_run_manifest()
                    return evidence

                def save_json(name, payload):
                    path = OUT / name
                    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
                    if TRACK_RUN_MANIFEST:
                        if name not in RUN_RESULT_FILES:
                            RUN_RESULT_FILES.append(name)
                        write_run_manifest()
                    print({{"saved": str(path.relative_to(ROOT))}})
                    return path

                def save_text(name, text):
                    path = OUT / name
                    path.write_text(text.rstrip() + "\\n", encoding="utf-8")
                    if TRACK_RUN_MANIFEST:
                        if name not in RUN_RESULT_FILES:
                            RUN_RESULT_FILES.append(name)
                        write_run_manifest()
                    print({{"saved": str(path.relative_to(ROOT))}})
                    return path

                if TRACK_RUN_MANIFEST:
                    write_run_manifest()

                def run_command(*args, cwd=ROOT):
                    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
                    display_args = list(args)
                    if display_args and display_args[0] == sys.executable:
                        display_args[0] = "python"
                    result = {{
                        "command": " ".join(display_args),
                        "returncode": completed.returncode,
                        "stdout_tail": completed.stdout.strip().splitlines()[-5:],
                        "stderr_tail": completed.stderr.strip().splitlines()[-5:],
                    }}
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                """
            ),
            *cells,
            markdown(
                f"""
                ## 완료 확인

                - Day {day}의 1~8차시 결과 파일을 확인했습니다.
                - 정상 경로와 가장 중요한 실패 경로를 모두 실행했습니다.
                - 외부 서비스 저장·게시·발송과 자동 메일이 기본값 `false`임을 확인했습니다.
                - Codex·Claude Code 결과는 test와 diff를 사람이 검토한 뒤에만 반영합니다.
                """
            ),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
            "course_day": day,
            "period_count": 8,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = {
    3: notebook(
        "Day 3 · 코드 리뷰 Agent",
        3,
        [
            markdown("""
            ## 1차시 · Review Rubric과 Severity

            finding은 문체가 아니라 사용자 영향·재현 조건·변경 라인·가장 작은 교정으로 작성합니다.
            """),
            code("""
            review_rubric = {
                "required_fields": ["path", "line", "severity", "title", "body", "evidence", "suggestion", "confidence", "rule_id"],
                "severity": {"P0": "즉시 악용·데이터 손실", "P1": "외부 상태·핵심 기능 위험", "P2": "복구·운영 품질 저하", "P3": "국소적 개선"},
                "excluded": ["style_only", "unrelated_file", "invented_runtime_result"],
            }
            save_json("01_review_rubric.json", review_rubric)
            review_rubric
            """),
            markdown("""
            ## 2차시 · Unified Diff와 Line Mapping

            `+++` target과 `@@` hunk를 읽고 추가된 new line만 복원합니다.
            """),
            code("""
            from src.course_services.review_service import parse_unified_diff

            diff_path = ROOT / "data/day3_review_cases/unsafe_pr.diff"
            diff_text = diff_path.read_text(encoding="utf-8")
            parsed = parse_unified_diff(diff_text)
            parsed_result = {
                "changed_paths": parsed.changed_paths,
                "added_lines": [{"path": line.path, "line": line.line, "text": line.text} for line in parsed.added_lines],
            }
            save_json("02_parsed_hunks.json", parsed_result)
            [(line.line, line.text) for line in parsed.added_lines]
            """),
            markdown("""
            ## 3차시 · Review Context Pack

            전체 저장소가 아니라 변경 path·관련 test 후보·검토 초점만 모델에 전달합니다.
            """),
            code("""
            from src.course_services.review_service import build_context_pack

            context_pack = build_context_pack(parsed)
            assert "style_only" in context_pack["excluded_focus"]
            save_json("03_context_pack.json", context_pack)
            context_pack
            """),
            markdown("""
            ## 4차시 · ReviewFinding Contract

            line·severity·confidence·자동 게시 금지를 Pydantic 계약으로 검증합니다.
            """),
            code("""
            from pydantic import ValidationError
            from src.course_services.contracts import ReviewReport
            from src.course_services.review_service import run_review_service

            review_report = run_review_service(diff_text)
            validated_report = ReviewReport.model_validate(review_report)
            try:
                ReviewReport(status="SUCCESS", automatic_publish=True)
                contract_boundary = {"status": "UNEXPECTED_SUCCESS"}
            except ValidationError as exc:
                contract_boundary = {"status": "EXPECTED_FAILURE", "error_code": str(exc).splitlines()[0]}
            save_json("04_review_contract.json", {"normal": validated_report.model_dump(mode="json"), "boundary": contract_boundary})
            {"finding_count": len(validated_report.findings), "boundary": contract_boundary}
            """),
            markdown("""
            ## 5차시 · Deterministic Baseline

            LLM 전에 재현 가능한 세 규칙으로 eval·외부 쓰기·broad exception을 찾습니다.
            """),
            code("""
            baseline = run_review_service(diff_text)
            rule_ids = [finding["rule_id"] for finding in baseline["findings"]]
            empty_diff = run_review_service("")
            assert len(rule_ids) == 3
            assert empty_diff["error_code"] == "EMPTY_DIFF"
            save_json("05_baseline_review.json", {"normal": baseline, "boundary": empty_diff})
            rule_ids
            """),
            markdown("""
            ## 6차시 · Static·Test·LLM Hybrid Review

            결정론 finding과 실제 test 증거를 먼저 묶고, LLM 의견은 선택 adapter로 분리합니다.
            """),
            code("""
            test_evidence = run_command(sys.executable, "-m", "pytest", "-q", "tests/test_course_services.py", "-k", "unified_diff or maps_findings")
            hybrid_review = {
                "static_findings": baseline["findings"],
                "test_evidence": test_evidence,
                "llm_adapter": {"requested": False, "reason": "DETERMINISTIC_BASELINE_FIRST"},
                "ready_for_evaluation": test_evidence["returncode"] == 0,
            }
            assert hybrid_review["ready_for_evaluation"] is True
            save_json("06_hybrid_review.json", hybrid_review)
            {"finding_count": len(hybrid_review["static_findings"]), "test_returncode": test_evidence["returncode"]}
            """),
            markdown("""
            ## 7차시 · Precision·Recall·F1

            Golden finding과 현재 결과를 path·line·rule ID로 비교합니다.
            """),
            code("""
            from src.course_services.eval_service import evaluate_review_findings, release_gate

            expected = json.loads((ROOT / "data/day5_eval/golden_review_findings.json").read_text(encoding="utf-8"))
            review_metrics = evaluate_review_findings(baseline["findings"], expected)
            review_gate = release_gate(review_metrics=review_metrics, safety_passed=True, latency_seconds=0.2)
            assert review_gate["decision"] == "READY"
            save_json("07_review_eval.json", {"metrics": review_metrics, "release_gate": review_gate})
            {"precision": review_metrics["precision"], "recall": review_metrics["recall"], "f1": review_metrics["f1"]}
            """),
            markdown("""
            ## 8차시 · Codex Harness와 회귀 방지

            Codex 작업을 목표·허용 경로·test·금지 행동으로 제한하고, scope·test·diff·secret을 사람 merge 전에 검사합니다.
            """),
            code("""
            from src.course_services.codex_harness import CodexTaskSpec, assess_codex_run, render_codex_task
            from src.course_services.course_demo import build_course_demo

            spec = CodexTaskSpec(
                objective="review rule 하나와 정상·실패 test를 추가한다.",
                allowed_paths=("src/course_services", "tests"),
                acceptance_tests=("python -m pytest -q tests/test_course_services.py",),
            )
            ready_assessment = assess_codex_run(
                spec,
                changed_paths=["src/course_services/review_service.py", "tests/test_course_services.py"],
                executed_tests={"python -m pytest -q tests/test_course_services.py": True},
                diff_reviewed=True, secrets_detected=False,
            )
            hold_assessment = assess_codex_run(
                spec, changed_paths=[".env"], executed_tests={}, diff_reviewed=False, secrets_detected=True,
            )
            scorecard = build_course_demo(3, workspace_root=ROOT)
            day3_result = {
                "codex_task": render_codex_task(spec), "ready_assessment": ready_assessment,
                "hold_assessment": hold_assessment, "scorecard": scorecard,
            }
            assert ready_assessment["decision"] == "READY_FOR_HUMAN_MERGE"
            assert hold_assessment["decision"] == "HOLD"
            save_json("08_day3_report.json", day3_result)
            {"decision": scorecard["decision"], "metrics": scorecard["metrics"]}
            """),
        ],
    ),
    4: notebook(
        "Day 4 · GitHub·LangGraph 승인 Workflow",
        4,
        [
            markdown("""
            ## 1차시 · PR Target과 Fixture

            repository·PR number·head SHA를 고정해 잘못된 대상에 게시하는 위험을 먼저 차단합니다.
            """),
            code("""
            from src.course_services.github_service import load_pr_fixture

            fixture = load_pr_fixture(ROOT / "data/day4_github/pr_fixture.json", workspace_root=ROOT)
            target = {key: fixture[key] for key in ("repository", "number", "head_sha")}
            save_json("01_pr_target.json", target)
            target
            """),
            markdown("""
            ## 2차시 · GitHub 인증과 최소 권한

            token 값은 읽거나 출력하지 않습니다. `.env` 제외 여부와 key 설정 유무만 확인합니다.
            """),
            code("""
            import os

            ignore_check = run_command("git", "check-ignore", "-v", ".env")
            auth_status = {
                "env_ignored": ignore_check["returncode"] == 0,
                "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
                "token_value_printed": False,
                "recommended_scope": "read-only until explicit sandbox approval",
            }
            save_json("02_auth_status.json", auth_status)
            auth_status
            """),
            markdown("""
            ## 3차시 · REST 상태 코드와 복구 계약

            401·403·404·422는 멈추고 원인을 고치며, 429만 제한된 횟수 안에서 재시도합니다.
            """),
            code("""
            from src.course_services.github_service import classify_github_response

            response_contracts = {
                str(status): classify_github_response(status, retry_after_seconds=3)
                for status in (200, 401, 403, 404, 422, 429, 500)
            }
            assert response_contracts["429"]["retryable"] is True
            assert all(not response_contracts[str(status)]["retryable"] for status in (401, 403, 404, 422, 500))
            save_json("03_github_response_contracts.json", response_contracts)
            response_contracts
            """),
            markdown("""
            ## 4차시 · LangGraph State와 분기

            approve·edit·reject가 같은 thread에서 서로 다른 terminal state로 끝나는지 실행합니다.
            """),
            code("""
            from src.langchain_lab import fixture_payload
            from src.langgraph_lab import run_langgraph_lab

            draft = fixture_payload()
            graph_results = {
                decision: run_langgraph_lab(draft, decision=decision, request_id=f"day4-{decision}")
                for decision in ("approve", "edit", "reject")
            }
            terminal_states = {key: value["final_state"]["status"] for key, value in graph_results.items()}
            assert terminal_states["reject"] == "REJECTED"
            save_json("04_graph_states.json", graph_results)
            terminal_states
            """),
            markdown("""
            ## 5차시 · Checkpoint와 Idempotency

            같은 target·SHA·comment body를 두 번 실행해 fake publisher가 한 번만 호출되는지 확인합니다.
            """),
            code("""
            from src.course_services.github_service import InMemoryIdempotencyStore, prepare_review_comment, publish_review_comment
            from src.course_services.review_service import run_review_service

            diff_text = (ROOT / fixture["diff"]).read_text(encoding="utf-8")
            report = run_review_service(diff_text)
            approval_plan = prepare_review_comment(report=report, target=target, dry_run=False)
            store = InMemoryIdempotencyStore()
            calls = []
            def fake_publisher(pr_target, body):
                calls.append({"target": pr_target.model_dump(), "body_length": len(body)})
                return {"id": 101, "url": "https://example.invalid/reviews/101"}
            first = publish_review_comment(plan=approval_plan, human_approved=True, publisher=fake_publisher, store=store)
            second = publish_review_comment(plan=approval_plan, human_approved=True, publisher=fake_publisher, store=store)
            idempotency_result = {"first": first, "second": second, "call_count": len(calls)}
            assert len(calls) == 1 and second["remote_result"]["reused"] is True
            save_json("05_idempotency.json", idempotency_result)
            {"call_count": len(calls), "duplicate_reused": second["remote_result"]["reused"]}
            """),
            markdown("""
            ## 6차시 · Human Approval과 Interrupt

            사람 거절은 외부 쓰기 없이 BLOCKED로 끝나고, 승인도 target·근거·초안을 본 뒤에만 재개합니다.
            """),
            code("""
            rejected = publish_review_comment(
                plan=approval_plan, human_approved=False, publisher=fake_publisher, store=InMemoryIdempotencyStore(),
            )
            human_decisions = {
                "approve": {"status": first["status"], "external_write": first["external_write"], "publisher_mode": "fake"},
                "reject": rejected,
            }
            assert rejected["error_code"] == "HUMAN_APPROVAL_REQUIRED"
            save_json("06_review_decision.json", human_decisions)
            human_decisions
            """),
            markdown("""
            ## 7차시 · Dry-run Comment Payload

            실제 API와 같은 body·target·idempotency key를 만들되 publisher는 호출하지 않습니다.
            """),
            code("""
            dry_run_plan = prepare_review_comment(report=report, target=target, dry_run=True)
            blocked_dry_run = publish_review_comment(
                plan=dry_run_plan, human_approved=True, publisher=fake_publisher, store=InMemoryIdempotencyStore(),
            )
            assert dry_run_plan["external_write"] is False
            assert blocked_dry_run["error_code"] == "DRY_RUN_CANNOT_PUBLISH"
            save_json("07_review_comment_plan.json", {"plan": dry_run_plan, "publish_attempt": blocked_dry_run})
            {"status": dry_run_plan["status"], "publish_attempt": blocked_dry_run["error_code"]}
            """),
            markdown("""
            ## 8차시 · Sandbox 게시 전 Audit

            수업 기본 경로는 fake publisher입니다. 실제 GitHub 게시에는 본인 sandbox·최소 권한·한 건 제한·rollback이 추가로 필요합니다.
            """),
            code("""
            from src.course_services.course_demo import build_course_demo

            day4_audit = build_course_demo(4, workspace_root=ROOT)
            focused_test = run_command(sys.executable, "-m", "pytest", "-q", "tests/test_course_services.py", "-k", "github or dry_run or idempotent")
            day4_audit["focused_test"] = focused_test
            assert day4_audit["external_write"] is False
            assert focused_test["returncode"] == 0
            save_json("08_day4_audit_record.json", day4_audit)
            {"decision": day4_audit["decision"], "metrics": day4_audit["metrics"]}
            """),
        ],
    ),
    5: notebook(
        "Day 5 · 관측·평가·배포 운영",
        5,
        [
            markdown("""
            ## 1차시 · Meeting·Review Service Router

            모델이 업무 종류와 권한을 추측하지 않도록 호출자가 `input_kind`를 명시합니다.
            """),
            code("""
            from src.course_services.service_router import route_service_request

            meeting = route_service_request(
                input_kind="meeting_transcript", source_path=ROOT / "data/meeting_sample_ko.txt", workspace_root=ROOT,
            )
            review = route_service_request(
                input_kind="code_diff", source_path=ROOT / "data/day3_review_cases/unsafe_pr.diff", workspace_root=ROOT,
            )
            unknown = route_service_request(
                input_kind="unknown", source_path=ROOT / "data/meeting_sample_ko.txt", workspace_root=ROOT,
            )
            router_result = {"meeting": meeting, "review": review, "boundary": unknown}
            assert unknown["error_code"] == "UNSUPPORTED_INPUT_KIND"
            save_json("01_unified_service_result.json", router_result)
            {"meeting": meeting["service"], "review": review["service"], "boundary": unknown["error_code"]}
            """),
            markdown("""
            ## 2차시 · Local Trace와 LangSmith 선택 Upload

            기본은 local JSON입니다. synthetic·deidentified 결과 요약만 사람 선택 뒤 LangSmith에 올립니다.
            """),
            code("""
            from src.observability_lab import LocalTraceRecorder

            trace_recorder = LocalTraceRecorder(
                run_name="day5-agent-operations",
                metadata={"data_classification": "synthetic", "external_write": False},
            )
            with trace_recorder.span("route_meeting", inputs={"input_kind": "meeting_transcript"}):
                assert meeting["status"] == "SUCCESS"
            with trace_recorder.span("route_code_review", inputs={"input_kind": "code_diff"}):
                assert review["status"] == "SUCCESS"
            trace = trace_recorder.to_dict()
            trace["langsmith_upload"] = {"requested": False, "reason": "LOCAL_FIRST"}
            save_json("02_trace.json", trace)
            [(span["name"], span["status"]) for span in trace["spans"]]
            """),
            markdown("""
            ## 3차시 · 운영 Metadata와 Monitoring

            평균 하나가 아니라 provider·status·latency·fallback·READY/HOLD를 함께 봅니다.
            """),
            code("""
            monitoring_view = {
                "run_name": trace["run_name"],
                "status_counts": {
                    "SUCCESS": sum(span["status"] == "SUCCESS" for span in trace["spans"]),
                    "ERROR": sum(span["status"] == "ERROR" for span in trace["spans"]),
                },
                "latency_ms": {span["name"]: span["latency_ms"] for span in trace["spans"]},
                "filters": ["provider_used", "error_code", "fallback_reason", "decision"],
                "raw_content_uploaded": False,
            }
            save_json("03_monitoring_view.json", monitoring_view)
            monitoring_view
            """),
            markdown("""
            ## 4차시 · Dataset Experiment와 Release Gate

            같은 Golden Set으로 baseline과 candidate를 비교하고 threshold 아래면 HOLD합니다.
            """),
            code("""
            from src.course_services.eval_service import evaluate_review_findings, release_gate

            expected = json.loads((ROOT / "data/day5_eval/golden_review_findings.json").read_text(encoding="utf-8"))
            experiment_metrics = evaluate_review_findings(review["result"]["findings"], expected)
            ready_gate = release_gate(review_metrics=experiment_metrics, safety_passed=True, latency_seconds=0.2)
            hold_gate = release_gate(review_metrics={"precision": 0.7, "recall": 0.6}, safety_passed=False, latency_seconds=42.0)
            assert ready_gate["decision"] == "READY" and hold_gate["decision"] == "HOLD"
            save_json("04_experiment_result.json", {"metrics": experiment_metrics, "normal": ready_gate, "boundary": hold_gate})
            {"metrics": experiment_metrics, "normal": ready_gate["decision"], "boundary": hold_gate["decision"]}
            """),
            markdown("""
            ## 5차시 · Human Feedback과 Annotation

            좋아요 한 개가 아니라 approve·edit·reject와 판단 이유를 구조화합니다.
            """),
            code("""
            feedback = [
                {"run_id": "synthetic-001", "decision": "approve", "reason": "EVIDENCE_CONFIRMED", "reviewer": "human"},
                {"run_id": "synthetic-002", "decision": "edit", "reason": "OWNER_CORRECTED", "reviewer": "human"},
                {"run_id": "synthetic-003", "decision": "reject", "reason": "UNKNOWN_EVIDENCE", "reviewer": "human"},
            ]
            feedback_path = OUT / "05_human_feedback.jsonl"
            feedback_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\\n" for row in feedback), encoding="utf-8")
            print({"saved": str(feedback_path.relative_to(ROOT)), "rows": len(feedback)})
            feedback
            """),
            markdown("""
            ## 6차시 · PII·Retention·Incident 운영

            외부 trace 전에 이메일·전화번호·token 형태를 가리고, raw content를 업로드하지 않습니다.
            """),
            code("""
            from src.observability_lab import redact_observability_text

            sample_sensitive = "담당자 test@example.com 010-1234-5678 sk-exampletoken123456789"
            redaction = redact_observability_text(sample_sensitive)
            ops_checklist = {
                "classification": "synthetic", "redaction": redaction, "retention_days": 7,
                "raw_content_upload": False, "incident_owner_required": True,
            }
            assert redaction["redacted"] is True
            assert "test@example.com" not in redaction["text"]
            save_json("06_ops_checklist.json", ops_checklist)
            ops_checklist
            """),
            markdown("""
            ## 7차시 · Release Candidate와 Local Web Demo

            Python 결과와 브라우저 Demo가 같은 JSON을 사용하도록 먼저 Demo data를 생성하고, Node가 있으면 local build를 실행합니다.
            """),
            code("""
            import shutil
            from src.course_services.course_demo import write_course_demo

            release_data = {
                day: write_course_demo(day, workspace_root=ROOT, output_dir=ROOT / f"output/course-demos/day{day}")
                for day in (2, 3, 4, 5)
            }
            node = shutil.which("node")
            web_build = run_command(node, "build.mjs", cwd=ROOT / "web-demo") if node else {
                "command": "node build.mjs", "returncode": 2, "error_code": "NODE_NOT_AVAILABLE"
            }
            release_candidate = {
                "demo_decisions": {str(day): result["decision"] for day, result in release_data.items()},
                "web_build": web_build,
                "schema_source": "output/course-demos/dayN/demo_result.json",
            }
            save_json("07_release_candidate.json", release_candidate)
            release_candidate
            """),
            markdown("""
            ## 8차시 · 최종 Demo와 Scorecard

            정상 한 건과 대표 HOLD 한 건, 사람 승인, 평가 수치를 함께 보여주고 전체 test로 마무리합니다.
            """),
            code("""
            from src.course_services.course_demo import build_course_demo

            final_scorecard = build_course_demo(5, workspace_root=ROOT)
            focused_test = run_command(sys.executable, "-m", "pytest", "-q", "tests/test_course_services.py", "tests/test_observability_workflow.py")
            final_scorecard["focused_test"] = focused_test
            final_scorecard["web_build"] = web_build
            assert final_scorecard["decision"] == "READY"
            assert final_scorecard["boundary_case"]["status"] == "HOLD"
            assert focused_test["returncode"] == 0
            save_json("08_release_scorecard.json", final_scorecard)
            {"decision": final_scorecard["decision"], "boundary": final_scorecard["boundary_case"], "metrics": final_scorecard["metrics"]}
            """),
        ],
    ),
}


# Day 2 uses three real input scenarios and one shared workflow contract.
NOTEBOOKS[2] = notebook(
    "Day 2 · 한국어 회의 Workflow와 Agent",
    2,
    [
        markdown("""
        ## 1차시 · Meeting Agent Architecture

        일반 사용자의 말로 시작해도 구현에서는 입력·맥락·변환·검증·승인·초안을 분리합니다. LLM은 한 단계의 판단 도구이고, Agent는 요청에 따라 정보원과 Workflow를 고르는 상위 실행 구조입니다.
        """),
        code("""
        from src.course_services.day2_meeting_workflow import (
            DEFAULT_OPENAI_MODEL, DomainContext, MCPRetrievalPolicy, MeetingRecord,
            SourceInput, TranscriptEnvelope, build_mcp_retrieval_plan,
            build_interruptible_meeting_graph,
            compact_workflow_result, compare_execution_strategies,
            diagnose_provider_options, normalize_source, render_email_draft,
            external_action_approval_gate, run_optional_local_stt_smoke,
            resume_interruptible_meeting_review, route_execution_strategy,
            run_meeting_workflow, start_interruptible_meeting_review,
            run_optional_cli_prompt, run_optional_openai_prompt, run_optional_openai_record,
            source_mixing_error_example,
            validate_model_record_output, validate_record_evidence,
        )

        architecture = {
            "user_request": "회의를 이해하고 근거 있는 기록·할 일·인사이트 초안을 만들어 줘",
            "layers": [
                {"order": 1, "name": "policy", "question": "읽어도 되는 정보와 하면 안 되는 행동은?"},
                {"order": 2, "name": "input_adapter", "question": "Meet·ClovaNote·음성 중 어떤 한 입력인가?"},
                {"order": 3, "name": "domain_context", "question": "산업 용어와 이전 결정은 무엇인가?"},
                {"order": 4, "name": "workflow", "question": "정규화→STT→구조화→근거 검증 순서는?"},
                {"order": 5, "name": "human_review", "question": "누가 승인·수정·거절하는가?"},
                {"order": 6, "name": "draft_export", "question": "MD·이메일 초안을 어디까지 만들 것인가?"},
            ],
            "two_meanings_of_agent": {
                "user_view": "여러 단계를 알아서 이어 주는 서비스",
                "engineering_view": "상태·도구·정책·오류·승인을 가진 실행 시스템",
            },
            "fixed_graph": [
                "policy", "input_normalize", "stt_optional", "structure",
                "evidence", "human_review", "export_draft",
            ],
            "invariants": {
                "source_count": 1,
                "human_review_required": True,
                "external_write": False,
                "run_all_network_calls": 0,
            },
        }
        route_cases = {
            "single_llm": route_execution_strategy(
                requested_actions=["rewrite_as_podcast_script"]
            ),
            "deterministic_workflow": route_execution_strategy(
                requested_actions=["normalize", "summarize", "todos", "draft"]
            ),
            "agent_router": route_execution_strategy(
                requested_actions=["summarize", "todos"],
                external_context_sources=["notion", "slack"],
            ),
        }
        external_action_gate = {
            "without_human_approval": external_action_approval_gate(
                "send_meeting_email", human_approved=False
            ),
            "approved_dry_run": external_action_approval_gate(
                "send_meeting_email", human_approved=True
            ),
        }
        architecture["three_route_cases"] = route_cases
        architecture["external_action_approval_gate"] = external_action_gate
        assert architecture["invariants"]["external_write"] is False
        assert {item["strategy"] for item in route_cases.values()} == {
            "single_llm", "deterministic_workflow", "agent_router",
        }
        assert external_action_gate["without_human_approval"]["error_code"] == (
            "EXTERNAL_ACTION_HUMAN_APPROVAL_REQUIRED"
        )
        assert external_action_gate["approved_dry_run"]["executed"] is False
        save_json("01_architecture.json", architecture)
        architecture
        """),
        markdown("""
        ## 2차시 · Input Route · STT

        Google Meet 텍스트, ClovaNote TXT, 로컬 음성은 출발점만 다릅니다. 텍스트가 이미 있으면 STT를 건너뛰고, 음성만 있을 때 로컬 STT를 실행합니다. 한 요청에 입력을 섞지 않고 모두 `TranscriptEnvelope`로 바꾼 뒤 같은 Workflow에 넣습니다.
        """),
        code("""
        import os
        from src.meeting_demo import parse_transcript
        from scripts.day2_public_audio import load_catalog, resolve, select_source

        meet_text = "\\n".join([
            "[00:00] 민지: 오늘은 배송 지연 회의 기록 자동화 범위를 확정하겠습니다.",
            "[00:18] 준호: WISMO 문의를 우선 처리하고 환불 자동화는 보류하는 것이 좋겠습니다.",
            "[00:37] 서연: 제가 9월 2일까지 고객 안내 문구를 정리해 공유하겠습니다.",
            "[00:55] 민지: 최근 야근 부담이 있으니 이번 범위를 더 늘리지 않겠습니다.",
        ])
        clova_text = "\\n".join([
            "화자 1 00:00", "배송 지연 원인 분류를 1차 범위로 확정합니다.",
            "화자 2 00:24", "제가 9월 3일까지 분류 기준을 작성하겠습니다.",
            "화자 1 00:46", "운영팀 부담을 확인한 뒤 다음 범위를 결정하겠습니다.",
        ])
        audio_path = ROOT / "data/meeting_sample_ko_12min.wav"

        sources = {
            "google_meet_text": SourceInput(
                source_mode="google_meet_text", source_ref="meet://fixture/delivery-001",
                meet_transcript=meet_text,
                speaker_metadata={
                    "민지": {"display_name": "민지", "role": "PM"},
                    "준호": {"display_name": "준호", "role": "Engineer"},
                    "서연": {"display_name": "서연", "role": "Operations"},
                },
                history_metadata={"prior_decisions": ["고객 자동 발송 금지"]},
            ),
            "clovanote_txt": SourceInput(
                source_mode="clovanote_txt", source_ref="clovanote-export-001.txt",
                clovanote_text=clova_text,
                speaker_metadata={
                    "화자 1": {"display_name": "민지", "role": "PM"},
                    "화자 2": {"display_name": "준호", "role": "Engineer"},
                },
            ),
            "audio_stt": SourceInput(
                source_mode="audio_stt", source_ref="synthetic-12min-audio",
                audio_path=str(audio_path),
            ),
        }

        def reviewed_fixture_stt(path):
            assert path.resolve() == audio_path.resolve()
            text = (ROOT / "data/meeting_sample_ko_12min.txt").read_text(encoding="utf-8")
            segments = parse_transcript(text)
            return text, segments, {
                "provider": "reviewed_transcript_fixture", "language": "ko",
                "lane": "deterministic_run_all_not_live_stt",
                "review_status": "instructor_reviewed_audio_transcript_pair",
                "network_used": False, "matched_audio_transcript_pair": True,
            }

        envelopes = {
            "google_meet_text": normalize_source(sources["google_meet_text"]),
            "clovanote_txt": normalize_source(sources["clovanote_txt"]),
            "audio_stt": normalize_source(
                sources["audio_stt"], transcriber=reviewed_fixture_stt
            ),
        }
        public_audio_catalog = load_catalog()
        public_audio_source = select_source(public_audio_catalog, None)
        public_audio_resolution = resolve(public_audio_catalog, public_audio_source)
        resolved_public_audio = ROOT / public_audio_resolution["path"]
        faster_whisper_live_opt_in = (
            os.getenv("FASTER_WHISPER_LIVE_OPT_IN", "0") == "1"
        )
        local_stt_smoke = run_optional_local_stt_smoke(
            resolved_public_audio,
            workspace_root=ROOT,
            live_opt_in=faster_whisper_live_opt_in,
            model_size=os.getenv("FASTER_WHISPER_MODEL", "small"),
        )
        input_result = {
            "reviewed_fixture_lane": {
                "label": "검토 완료 Transcript Fixture · 기본 Run All",
                "audio_path": str(audio_path.relative_to(ROOT)),
                "transcript_path": "data/meeting_sample_ko_12min.txt",
                "live_stt": False,
                "silent_transcript_substitution": False,
            },
            "optional_local_faster_whisper_smoke": {
                "opt_in_environment": "FASTER_WHISPER_LIVE_OPT_IN=1",
                "resolved_public_audio": public_audio_resolution,
                "result": local_stt_smoke,
            },
            "contracts": {
                name: {
                    "source_mode": envelope.source_mode,
                    "source_count": envelope.source_count,
                    "segment_count": len(envelope.segments),
                    "first_segment": envelope.segments[0].model_dump(mode="json"),
                    "stt_metadata": envelope.stt_metadata,
                }
                for name, envelope in envelopes.items()
            },
            "boundary": source_mixing_error_example(),
        }
        assert {item["source_count"] for item in input_result["contracts"].values()} == {1}
        assert input_result["boundary"]["error_code"] == "SOURCE_MODE_MIXING_FORBIDDEN"
        assert envelopes["audio_stt"].stt_metadata["provider"] == "reviewed_transcript_fixture"
        assert local_stt_smoke["transcript_substituted"] is False
        if not faster_whisper_live_opt_in:
            assert local_stt_smoke["error_code"] == "LOCAL_STT_LIVE_OPT_IN_REQUIRED"
        save_json("02_inputs.json", input_result)
        input_result
        """),
        markdown("""
        ## 3차시 · Domain Context · MCP Policy

        회의에서 말한 사실과 사용자가 제공한 업무 맥락을 분리합니다. Notion·Confluence·Slack이 필요해 보여도 자동으로 읽지 않고, 허용된 범위와 기간을 가진 MCP 읽기 계획만 먼저 만듭니다.
        """),
        code("""
        domain_context = DomainContext(
            industry="이커머스 고객경험",
            organization_context="배송 지연 문의가 증가해 상담 부담과 고객 불편이 함께 커진 상태",
            meeting_objective="배송 지연 회의 기록 자동화 범위 확정",
            glossary={"WISMO": "배송 위치 문의", "SLA": "약속한 응답 시간"},
            prior_decisions=["외부 발송은 사람 승인 뒤에만 진행", "환불 자동화는 이번 범위에서 제외"],
            desired_outcomes=["근거가 있는 담당자별 To Do", "단기·중기·장기 인사이트"],
            confidentiality="internal",
        )
        retrieval_policy = MCPRetrievalPolicy(
            allowed_connectors=["notion", "confluence", "slack"],
            explicit_user_authorization=True,
            lookback_days=14,
            allowed_scopes={
                "notion": ["CX PoC"], "confluence": ["CX 정책"], "slack": ["#delivery-poc"],
            },
            participant_match_required=True,
            max_items_per_connector=5,
        )
        mcp_plan = build_mcp_retrieval_plan(
            envelope=envelopes["google_meet_text"],
            domain=domain_context,
            policy=retrieval_policy,
        )
        context_prompt_fields = {
            "industry": domain_context.industry,
            "organization_context": domain_context.organization_context,
            "meeting_objective": domain_context.meeting_objective,
            "glossary": domain_context.glossary,
            "prior_decisions": domain_context.prior_decisions,
            "desired_outputs": domain_context.desired_outcomes,
            "evidence_rule": "회의 발화의 사실 주장에는 s01 같은 evidence ID 필수",
        }
        context_result = {
            "domain_context": domain_context.model_dump(mode="json"),
            "context_prompt_fields": context_prompt_fields,
            "mcp_retrieval_plan": mcp_plan,
        }
        assert mcp_plan["executed"] is False and mcp_plan["external_write"] is False
        save_json("03_domain_context.json", context_result)
        context_result
        """),
        markdown("""
        ## 4차시 · MeetingRecord Schema

        먼저 모든 실행 방식이 반환해야 할 `MeetingRecord`를 고정합니다. 그 다음 한 번의 생성이면 단일 LLM, 고정 순서면 Workflow, 정보원과 다음 행동이 요청마다 달라지면 Agent Router를 선택합니다. 알려진 경로를 고르는 데 LLM을 쓰지 않으면 비용과 오작동 지점을 줄일 수 있습니다.
        """),
        code("""
        from pydantic import ValidationError

        record_contract_run = run_meeting_workflow(
            sources["google_meet_text"],
            domain_context,
            review_decision="approve",
            retrieval_policy=retrieval_policy,
        )
        actual_record = MeetingRecord.model_validate(record_contract_run["record"])
        actual_envelope = TranscriptEnvelope.model_validate(record_contract_run["envelope"])
        actual_schema = MeetingRecord.model_json_schema()
        routing_cases = {
            "fixed_meeting_record": route_execution_strategy(
                requested_actions=["normalize", "summarize", "perspectives", "todos", "insights", "draft"]
            ),
            "context_retrieval_needed": route_execution_strategy(
                requested_actions=["summarize", "todos"],
                external_context_sources=["notion", "confluence", "slack"],
            ),
            "one_off_unmodeled_request": route_execution_strategy(
                requested_actions=["rewrite_as_podcast_script"]
            ),
        }
        unknown_evidence_payload = actual_record.model_dump(mode="json")
        unknown_evidence_payload["todos"][0]["evidence_ids"] = ["s999"]
        unknown_evidence_errors = validate_record_evidence(
            MeetingRecord.model_validate(unknown_evidence_payload), actual_envelope
        )

        owner_due_run = run_meeting_workflow(
            SourceInput(
                source_mode="google_meet_text",
                source_ref="meet://boundary/owner-due-unknown",
                meet_transcript="민지: 다음 회의에서 후속 조치를 논의해 봅시다.",
            ),
            domain_context,
            review_decision="approve",
        )
        owner_due_todo = owner_due_run["record"]["todos"][0]

        invalid_due_payload = actual_record.model_dump(mode="json")
        invalid_due_payload["todos"][0]["due_date"] = "2026-02-30"
        try:
            MeetingRecord.model_validate(invalid_due_payload)
            invalid_due_boundary = {"status": "UNEXPECTED_SUCCESS"}
        except ValidationError:
            invalid_due_boundary = {
                "status": "EXPECTED_FAILURE",
                "error_code": "TODO_DUE_DATE_INVALID",
            }

        additional_field_payload = actual_record.model_dump(mode="json")
        additional_field_payload["automatic_send"] = True
        try:
            MeetingRecord.model_validate(additional_field_payload)
            additional_field_boundary = {"status": "UNEXPECTED_SUCCESS"}
        except ValidationError:
            additional_field_boundary = {
                "status": "EXPECTED_FAILURE",
                "error_code": "MEETING_RECORD_ADDITIONAL_FIELD_FORBIDDEN",
            }
        record_contract_result = {
            "schema": {
                "name": "MeetingRecord",
                "field_names": list(MeetingRecord.model_fields),
                "required_fields": actual_schema.get("required", []),
                "properties": actual_schema["properties"],
            },
            "actual_record": actual_record.model_dump(mode="json"),
            "evidence_validation": {
                "known_segment_ids": [segment.id for segment in actual_envelope.segments],
                "errors": validate_record_evidence(actual_record, actual_envelope),
            },
            "execution_strategy_comparison": compare_execution_strategies(),
            "rule_router_examples": routing_cases,
            "boundary_evidence": {
                "unknown_evidence_s999": unknown_evidence_errors,
                "owner_due_not_in_source": {
                    "owner": owner_due_todo["owner"],
                    "due_date": owner_due_todo["due_date"],
                    "rule": "원문에 없으면 null 유지",
                },
                "invalid_due_date": invalid_due_boundary,
                "additional_field": additional_field_boundary,
            },
            "delivery_policy": {
                "human_review_required": actual_record.human_review_required,
                "external_write": actual_record.external_write,
                "draft_status": record_contract_run["exports"]["status"],
            },
        }
        assert set(record_contract_result["actual_record"]) == set(MeetingRecord.model_fields)
        assert record_contract_result["evidence_validation"]["errors"] == []
        assert record_contract_result["delivery_policy"]["external_write"] is False
        assert unknown_evidence_errors == ["TODO_1_UNKNOWN_EVIDENCE:s999"]
        assert owner_due_todo["owner"] is None and owner_due_todo["due_date"] is None
        assert invalid_due_boundary["error_code"] == "TODO_DUE_DATE_INVALID"
        assert additional_field_boundary["error_code"] == (
            "MEETING_RECORD_ADDITIONAL_FIELD_FORBIDDEN"
        )
        assert routing_cases["fixed_meeting_record"]["strategy"] == "deterministic_workflow"
        assert routing_cases["context_retrieval_needed"]["strategy"] == "agent_router"
        assert routing_cases["one_off_unmodeled_request"]["strategy"] == "single_llm"
        save_json("04_meeting_record_contract.json", record_contract_result)
        record_contract_result
        """),
        markdown("""
        ## 5차시 · Coding Agent Workflow

        Codex나 Claude Code에는 곧바로 “Agent를 만들어 줘”라고 하지 않습니다. 세 입력 시나리오, 공통 결과 계약, 금지 행동, 정상·실패 Test를 먼저 합의한 뒤 구현을 요청합니다. 아래 실행 결과가 대화형 코딩 Agent에게 전달할 인수 기준입니다.
        """),
        code("""
        coding_agent_brief = {
            "scenarios": ["google_meet_text", "clovanote_txt", "audio_stt"],
            "implementation_request": (
                "세 입력을 하나의 MeetingRecord로 정규화하고, 근거 검증과 사람 승인 뒤 "
                "Markdown·이메일 초안까지만 만드는 코드를 구현해 주세요."
            ),
            "must_not": ["입력 자동 혼합", "근거 없는 담당자 추정", "승인 전 외부 저장·발송"],
            "acceptance_tests": [
                "세 입력 모두 같은 결과 계약", "존재하지 않는 evidence ID 차단",
                "승인·수정·거절 상태 분리", "모든 기본 실행에서 external_write=false",
            ],
            "conversation_guide": "materials/day2/Codex_Claude_대화_시나리오.md",
        }
        workflow_runs = {
            "google_meet_text": run_meeting_workflow(
                sources["google_meet_text"], domain_context,
                review_decision="approve", retrieval_policy=retrieval_policy,
            ),
            "clovanote_txt": run_meeting_workflow(
                sources["clovanote_txt"], domain_context,
                review_decision="approve",
            ),
            "audio_stt": run_meeting_workflow(
                sources["audio_stt"], domain_context,
                review_decision="edit",
                review_edits={
                    "meeting_summary": "고객 문의 자동화 PoC의 범위·금지 행동·담당자별 후속 조치를 근거와 함께 정리했습니다."
                },
                transcriber=reviewed_fixture_stt,
            ),
        }
        workflow_result = {
            "coding_agent_brief": coding_agent_brief,
            "scenarios": {
                name: compact_workflow_result(result)
                for name, result in workflow_runs.items()
            },
            "full_records": {
                name: result["record"] for name, result in workflow_runs.items()
            },
        }
        expected_nodes = [
            "policy", "input_normalize", "stt_optional", "structure",
            "evidence", "human_review", "export_draft",
        ]
        assert all(
            [event["node"] for event in item["trace"]] == expected_nodes
            for item in workflow_result["scenarios"].values()
        )
        assert all(item["status"] == "DRAFT_READY" for item in workflow_result["scenarios"].values())
        assert all(item["external_write"] is False for item in workflow_result["scenarios"].values())
        save_json("05_workflow_runs.json", workflow_result)
        workflow_result["scenarios"]
        """),
        markdown("""
        ## 6차시 · LLM Provider · Cost Guardrail

        기본 `Run All`은 API와 CLI를 호출하지 않습니다. `.env`를 읽되 OpenAI는 `OPENAI_LIVE_OPT_IN=1`, Ollama는 `OLLAMA_LIVE_OPT_IN=1`일 때만 실행합니다. OpenAI 모델 접근 불가를 fixture 성공으로 위장하지 않고, Ollama 출력도 Schema와 evidence를 통과해야 성공입니다.
        """),
        code("""
        from types import SimpleNamespace
        from dotenv import load_dotenv

        dotenv_loaded = load_dotenv(dotenv_path=ROOT / ".env", override=False)
        openai_live_opt_in = os.getenv("OPENAI_LIVE_OPT_IN", "0") == "1"
        ollama_live_opt_in = os.getenv("OLLAMA_LIVE_OPT_IN", "0") == "1"

        provider_options = diagnose_provider_options()
        cli_dry_runs = {
            name: run_optional_cli_prompt(name, "현재 회의 기록을 검토해 주세요.")
            for name in ("ollama", "codex", "claude_code")
        }
        openai_result = run_optional_openai_record(
            envelopes["google_meet_text"], domain_context,
            env=os.environ if openai_live_opt_in else {},
            model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            allow_fixture_fallback=True,
        )

        ollama_prompt = "\\n".join([
            "다음 MeetingRecord JSON Schema에 맞는 JSON object만 반환하세요.",
            "원문에 없는 owner와 due_date는 null, evidence ID는 제공된 값만 사용하세요.",
            "evidence_ids의 각 값은 ALLOWED_EVIDENCE_IDS의 문자열과 정확히 같아야 합니다.",
            "human_review_required=true, external_write=false를 유지하세요.",
            "ALLOWED_EVIDENCE_IDS=" + json.dumps(
                [item.id for item in envelopes["google_meet_text"].segments],
                ensure_ascii=False,
            ),
            "SCHEMA=" + json.dumps(MeetingRecord.model_json_schema(), ensure_ascii=False),
            "TRANSCRIPT=" + envelopes["google_meet_text"].transcript_text,
        ])
        ollama_call = run_optional_cli_prompt(
            "ollama",
            ollama_prompt,
            live_opt_in=ollama_live_opt_in,
            model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        )
        if ollama_call["status"] == "SUCCESS":
            ollama_validation = {
                "provider_status": "SUCCESS",
                **validate_model_record_output(
                    ollama_call["output_text"], envelopes["google_meet_text"]
                ),
            }
        else:
            ollama_validation = {
                "status": ollama_call["status"],
                "provider_status": ollama_call["status"],
                "error_code": (
                    "OLLAMA_LIVE_OPT_IN_REQUIRED"
                    if ollama_call["error_code"] == "CLI_LIVE_OPT_IN_REQUIRED"
                    else ollama_call["error_code"]
                ),
                "command_executed": ollama_call["command_executed"],
                "schema_valid": False,
                "evidence_valid": False,
                "fallback_used": False,
                "external_write": False,
            }

        class LocalModelNotFound(Exception):
            status_code = 404

        class FakeResponses:
            @staticmethod
            def create(**_kwargs):
                raise LocalModelNotFound("requested model does not exist")

        model_boundary = run_optional_openai_prompt(
            "모델 가용성 경계 테스트",
            env={"OPENAI_LIVE_OPT_IN": "1"},
            client=SimpleNamespace(responses=FakeResponses()),
            model=DEFAULT_OPENAI_MODEL,
        )
        provider_result = {
            "options": provider_options,
            "cli_default_run_all": cli_dry_runs,
            "openai_default_run_all": openai_result,
            "ollama_optional_schema_evidence_validation": ollama_validation,
            "model_not_available_boundary": model_boundary,
            "dotenv": {
                "loaded_without_override": bool(dotenv_loaded),
                "credential_values_exposed": False,
            },
            "live_flags": {
                "openai": openai_live_opt_in,
                "ollama": ollama_live_opt_in,
                "faster_whisper": faster_whisper_live_opt_in,
                "codex_cli": False, "claude_code_cli": False,
            },
        }
        if not openai_live_opt_in:
            assert openai_result["provider_used"] == "fixture"
            assert openai_result["fallback_reason"] == "OPENAI_LIVE_OPT_IN_REQUIRED"
            assert openai_result["schema_valid"] is True
        if not ollama_live_opt_in:
            assert ollama_validation["error_code"] == "OLLAMA_LIVE_OPT_IN_REQUIRED"
            assert ollama_validation["command_executed"] is False
        assert model_boundary["fallback_reason"] == "MODEL_NOT_AVAILABLE"
        assert all(item["error_code"] == "CLI_LIVE_OPT_IN_REQUIRED" for item in cli_dry_runs.values())
        assert all(
            item.get("command_executed", False) is False
            for item in provider_options.values()
            if isinstance(item, dict)
        )
        save_json("06_provider_diagnostics.json", provider_result)
        provider_result
        """),
        markdown("""
        ## 7차시 · LangGraph · Human Review

        먼저 `interrupt()`에서 멈춘 상태를 확인하고, 수강생이 결정값을 정한 뒤 같은 thread를 `Command(resume=...)`로 재개합니다. 마지막 자동 회귀 검증은 승인·수정·거절 세 경로가 계속 안전한지 별도로 확인합니다.
        """),
        code("""
        # 1단계 · interrupt 시작: 아직 승인 결정도, 초안 export도 없습니다.
        learner_graph = build_interruptible_meeting_graph()
        learner_thread_id = "day2-learner-review"
        learner_start = start_interruptible_meeting_review(
            learner_graph,
            sources["google_meet_text"],
            domain_context,
            thread_id=learner_thread_id,
            retrieval_policy=retrieval_policy,
        )
        assert learner_start["status"] == "WAITING_FOR_HUMAN_REVIEW"
        assert "exports" not in learner_start

        # 2단계 · 수강생 결정/재개: 아래 두 값을 바꾼 뒤 이 셀을 다시 실행합니다.
        LEARNER_REVIEW_DECISION = "edit"  # approve | edit | reject
        LEARNER_REVIEW_EDITS = {
            "meeting_summary": "사람이 근거를 확인하고 배송 지연 기록 범위를 수정했습니다.",
            "todo_updates": {"0": {"owner": "민지", "due_date": "2026-09-05"}},
        }
        learner_resume = resume_interruptible_meeting_review(
            learner_graph,
            thread_id=learner_thread_id,
            decision=LEARNER_REVIEW_DECISION,
            edits=LEARNER_REVIEW_EDITS if LEARNER_REVIEW_DECISION == "edit" else {},
        )
        assert learner_resume["external_write"] is False

        # 3단계 · 자동 회귀 evidence: 학습자 선택과 별도로 세 경로를 모두 검사합니다.
        review_inputs = {
            "approve": {},
            "edit": {
                "meeting_summary": "사람이 근거를 확인하고 배송 지연 기록 범위를 수정했습니다.",
                "todo_updates": {"0": {"owner": "민지", "due_date": "2026-09-05"}},
            },
            "reject": {},
        }
        regression_runs = {}
        for decision, edits in review_inputs.items():
            regression_graph = build_interruptible_meeting_graph()
            regression_thread_id = f"day2-regression-{decision}"
            regression_start = start_interruptible_meeting_review(
                regression_graph,
                sources["google_meet_text"],
                domain_context,
                thread_id=regression_thread_id,
                retrieval_policy=retrieval_policy,
            )
            regression_resume = resume_interruptible_meeting_review(
                regression_graph,
                thread_id=regression_thread_id,
                decision=decision,
                edits=edits,
            )
            regression_runs[decision] = {
                "start": {
                    "status": regression_start["status"],
                    "thread_id": regression_start["thread_id"],
                    "checkpointer": regression_start["checkpointer"],
                    "interrupt": regression_start["interrupts"][0],
                    "external_write": regression_start["external_write"],
                },
                "resume": {
                    "status": regression_resume["status"],
                    "review": regression_resume["review"],
                    "export_status": regression_resume["exports"]["status"],
                    "trace": regression_resume["trace"],
                    "external_write": regression_resume["external_write"],
                },
            }

        human_review_result = {
            "graph": {
                "framework": "LangGraph",
                "checkpointer": "InMemorySaver",
                "pause": "interrupt()",
                "resume": "Command(resume=...)",
                "conditional_routes": [
                    "evidence → human_review | evidence_hold",
                    "human_review → export_draft | review_rejected",
                ],
            },
            "learner_interrupt_start": {
                "status": learner_start["status"],
                "thread_id": learner_start["thread_id"],
                "interrupt": learner_start["interrupts"][0],
                "external_write": learner_start["external_write"],
            },
            "learner_decision_resume": {
                "decision": LEARNER_REVIEW_DECISION,
                "status": learner_resume["status"],
                "review": learner_resume["review"],
                "export_status": learner_resume["exports"]["status"],
                "external_write": learner_resume["external_write"],
            },
            "automated_regression_evidence": regression_runs,
            "unknown_evidence_boundary_from_4th_period": (
                record_contract_result["boundary_evidence"]["unknown_evidence_s999"]
            ),
        }
        assert all(
            item["start"]["status"] == "WAITING_FOR_HUMAN_REVIEW"
            for item in regression_runs.values()
        )
        assert regression_runs["approve"]["resume"]["status"] == "DRAFT_READY"
        assert regression_runs["edit"]["resume"]["status"] == "DRAFT_READY"
        assert regression_runs["reject"]["resume"]["status"] == "REJECTED"
        assert regression_runs["reject"]["resume"]["export_status"] == "SKIPPED_NOT_APPROVED"
        assert all(
            item["resume"]["external_write"] is False
            for item in regression_runs.values()
        )
        assert human_review_result["unknown_evidence_boundary_from_4th_period"] == [
            "TODO_1_UNKNOWN_EVIDENCE:s999"
        ]
        save_json("07_human_review.json", human_review_result)
        human_review_result
        """),
        markdown("""
        ## 8차시 · Localhost App · 선택 Package

        세 시나리오의 결과를 로컬 Markdown과 이메일 초안으로 만들고 같은 핵심 기능을 localhost UI에서 실제 실행합니다. 수강생 기본 경로는 Python 환경을 재사용하는 localhost이며, unsigned EXE·PKG는 Docker가 준비된 강사 PC의 선택 시연입니다.
        """),
        code("""
        markdown_files = {}
        email_drafts = {}
        for name, result in workflow_runs.items():
            record = MeetingRecord.model_validate(result["record"])
            markdown_text = result["exports"]["markdown"]
            markdown_path = save_text(f"08_{name}_meeting.md", markdown_text)
            markdown_files[name] = str(markdown_path.relative_to(ROOT))
            email_drafts[name] = render_email_draft(record, audience="internal")

        save_json("08_email_drafts.json", email_drafts)
        localhost_report_path = OUT / "08_localhost_launch.json"
        localhost_smoke = run_command(
            sys.executable,
            "scripts/run_day2_local_app.py",
            "--smoke-and-exit",
            "--port",
            "0",
            "--report",
            str(localhost_report_path.relative_to(ROOT)),
        )
        assert localhost_smoke["returncode"] == 0
        localhost_report = json.loads(localhost_report_path.read_text(encoding="utf-8"))
        save_json("08_localhost_launch.json", localhost_report)
        desktop_delivery = {
            "primary_run": "python scripts/run_day2_local_app.py",
            "macos_double_click": "desktop-app/meeting-intelligence/scripts/run-local.command",
            "windows_double_click": "desktop-app\\\\meeting-intelligence\\\\scripts\\\\run-local.cmd",
            "port_recovery": "python scripts/run_day2_local_app.py --port 0",
            "minimum_install": "python -m pip install -r desktop-app/meeting-intelligence/requirements-localhost.txt",
            "browser": "http://127.0.0.1:8766",
            "optional_package": {
                "windows_exe": "desktop-app/meeting-intelligence/dist/MeetingIntelligence-Windows.exe",
                "macos_pkg": "desktop-app/meeting-intelligence/dist/MeetingIntelligence-macOS.pkg",
                "docker_required": True,
                "signed": False,
                "role": "instructor_optional_demo",
            },
            "human_review_required": True,
            "external_write": False,
        }
        focused_test = run_command(
            sys.executable, "-m", "pytest", "-q", "tests/test_day2_meeting_workflow.py"
        )
        day1_suite = run_command(
            sys.executable, "-m", "pytest", "-q",
            "tests/test_day1_agent.py",
            "tests/test_langchain_langgraph_lab.py",
            "tests/test_meeting_agent_workflow.py",
            "tests/test_openai_provider.py",
            "tests/test_ollama_tool_agent.py",
        )
        focused_test_evidence = record_test_evidence("day2_focused", focused_test)
        day1_test_evidence = record_test_evidence("day1_regression", day1_suite)
        localhost_test_evidence = record_test_evidence("localhost_http_smoke", localhost_smoke)
        export_result = {
            "markdown_files": markdown_files,
            "email_drafts": email_drafts,
            "desktop_delivery": desktop_delivery,
            "localhost_launch": localhost_report,
            "test_evidence": [focused_test_evidence, day1_test_evidence, localhost_test_evidence],
            "checks": {
                "all_emails_unsent": all(item["send"] is False for item in email_drafts.values()),
                "all_external_write_false": all(item["external_write"] is False for item in email_drafts.values()),
                "focused_test_returncode": focused_test["returncode"],
                "day1_suite_returncode": day1_suite["returncode"],
                "localhost_smoke_returncode": localhost_smoke["returncode"],
                "localhost_smoke_status": localhost_report["status"],
                "localhost_external_write_false": localhost_report["external_write"] is False,
            },
        }
        assert export_result["checks"] == {
            "all_emails_unsent": True,
            "all_external_write_false": True,
            "focused_test_returncode": 0,
            "day1_suite_returncode": 0,
            "localhost_smoke_returncode": 0,
            "localhost_smoke_status": "PASS",
            "localhost_external_write_false": True,
        }
        save_json("08_export_drafts.json", export_result)
        export_result
        """),
    ],
)
NOTEBOOKS = {2: NOTEBOOKS[2], **NOTEBOOKS}


def write_notebook(day: int, payload: dict) -> Path:
    """Write one generated notebook and return its path."""

    folder = ROOT / f"materials/day{day}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"day{day}_service_lab.ipynb"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def execute_notebook(path: Path, *, timeout_seconds: int = 900) -> Path:
    """Execute a generated notebook from the repository root and save a separate copy."""

    import nbformat
    from nbclient import NotebookClient

    payload = nbformat.read(path, as_version=4)
    client = NotebookClient(
        payload,
        timeout=timeout_seconds,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    executed_path = path.with_name(f"{path.stem}.executed.ipynb")
    nbformat.write(payload, executed_path)
    return executed_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, choices=sorted(NOTEBOOKS))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    selected = {args.day: NOTEBOOKS[args.day]} if args.day else NOTEBOOKS
    for day, payload in selected.items():
        path = write_notebook(day, payload)
        print(path.relative_to(ROOT))
        if args.execute:
            executed = execute_notebook(path, timeout_seconds=args.timeout_seconds)
            print(executed.relative_to(ROOT))


if __name__ == "__main__":
    main()
