"""Generate eight-period runnable notebooks for Day 2-5."""

from __future__ import annotations

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
    return {
        "cells": [
            markdown(
                f"""
                # {title}

                하나의 입력을 8개 차시 동안 확장합니다. 웹사이트 확인이 아니라 코드·명령·test·결과 파일을 직접 다루며, 모든 외부 쓰기는 dry-run과 사람 승인을 먼저 거칩니다.
                """
            ),
            code(
                """
                from pathlib import Path
                import importlib.util, json, subprocess, sys

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
            code(
                """
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
            ),
            code(
                f"""
                OUT = ROOT / "output/course-labs/day{day}"
                OUT.mkdir(parents=True, exist_ok=True)

                def save_json(name, payload):
                    path = OUT / name
                    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
                    print({{"saved": str(path.relative_to(ROOT))}})
                    return path

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
                - 외부 쓰기와 자동 메일이 기본값 `false`임을 확인했습니다.
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
    2: notebook(
        "Day 2 · 한국어 회의 Agent",
        2,
        [
            markdown("""
            ## 1차시 · 오디오 계약과 Metadata

            모델을 실행하기 전에 파일 존재·길이·channel·sample rate를 확인합니다. 깨진 입력을 모델 오류로 오해하지 않는 첫 경계입니다.
            """),
            code("""
            import wave
            from src.meeting_demo import ensure_workspace_path

            audio_path = ensure_workspace_path(ROOT / "data/meeting_sample_ko_12min.wav", ROOT)
            with wave.open(str(audio_path), "rb") as wav:
                audio_metadata = {
                    "status": "SUCCESS",
                    "seconds": round(wav.getnframes() / wav.getframerate(), 2),
                    "sample_rate": wav.getframerate(),
                    "channels": wav.getnchannels(),
                    "sample_width": wav.getsampwidth(),
                }
            save_json("01_audio_metadata.json", audio_metadata)
            audio_metadata
            """),
            markdown("""
            ## 2차시 · STT Adapter와 Timestamp Segment

            `RUN_STT_LIVE=False`가 기본입니다. 모든 수강생은 reviewed fixture로 같은 segment 계약을 먼저 확인하고, 모델이 준비된 컴퓨터만 faster-whisper를 선택 실행합니다.
            """),
            code("""
            from src.meeting_demo import parse_transcript, run_demo

            transcript_path = ROOT / "data/meeting_sample_ko_12min.txt"
            transcript_text = transcript_path.read_text(encoding="utf-8")
            RUN_STT_LIVE = False
            if RUN_STT_LIVE:
                stt_run = run_demo(
                    audio_path=audio_path,
                    transcript_path=transcript_path,
                    output_dir=OUT / "live-stt",
                    model_size="small", device="cpu", compute_type="int8",
                    language="ko", local_files_only=True,
                )
                stt_segments = stt_run["segments"]
                stt_status = {"provider_used": stt_run["mode"], "fallback_reason": stt_run["fallback_reason"]}
            else:
                stt_segments = parse_transcript(transcript_text)
                stt_status = {"provider_used": "reviewed_fixture", "fallback_reason": "LIVE_STT_NOT_SELECTED"}
            transcript_result = {**stt_status, "segment_count": len(stt_segments), "segments": stt_segments}
            save_json("02_transcript.json", transcript_result)
            {"provider_used": stt_status["provider_used"], "segment_count": len(stt_segments)}
            """),
            markdown("""
            ## 3차시 · STT 품질 Gate

            문자가 생성됐다는 사실과 업무에 사용 가능한 상태를 분리합니다. 정상 fixture는 READY, 빈 전사는 HOLD가 되어야 합니다.
            """),
            code("""
            from src.meeting_demo import build_quality_gate

            ready_gate = build_quality_gate(
                stt_segments, mode="local_stt",
                metadata={"language": "ko", "language_probability": 0.99},
                reference_similarity=1.0,
            )
            hold_gate = build_quality_gate([], mode="fixture", metadata={"language": "ko"})
            quality_result = {"normal": ready_gate, "boundary": hold_gate}
            assert ready_gate["decision"] == "READY"
            assert hold_gate["decision"] == "HOLD"
            save_json("03_quality_gate.json", quality_result)
            quality_result
            """),
            markdown("""
            ## 4차시 · MeetingBrief Schema

            자연스러운 문장보다 필수 field·날짜 형식·evidence ID·사람 승인 정책을 먼저 고정합니다.
            """),
            code("""
            from pydantic import ValidationError
            from src.langchain_lab import ActionItem, MeetingBrief, fixture_payload

            meeting_brief = MeetingBrief.model_validate(fixture_payload())
            try:
                ActionItem(task="근거 없는 할 일", owner="미정", due_date="2026-08-30", evidence_ids=[])
                schema_boundary = {"status": "UNEXPECTED_SUCCESS"}
            except ValidationError as exc:
                schema_boundary = {"status": "EXPECTED_FAILURE", "error_code": exc.errors()[0]["type"]}
            schema_result = {"normal": meeting_brief.model_dump(mode="json"), "boundary": schema_boundary}
            save_json("04_meeting_schema.json", schema_result)
            {"title": meeting_brief.title, "boundary": schema_boundary}
            """),
            markdown("""
            ## 5차시 · Evidence-preserving Chunk

            글자 수로 자르더라도 발화 ID와 overlap을 보존합니다. 너무 작은 chunk 설정은 명시적으로 실패시킵니다.
            """),
            code("""
            from src.course_services.meeting_service import chunk_transcript_segments

            chunks = chunk_transcript_segments(stt_segments, max_chars=900, overlap_segments=1)
            try:
                chunk_transcript_segments(stt_segments, max_chars=20)
                chunk_boundary = {"status": "UNEXPECTED_SUCCESS"}
            except ValueError as exc:
                chunk_boundary = {"status": "EXPECTED_FAILURE", "error_code": str(exc)}
            chunk_result = {"chunks": chunks, "boundary": chunk_boundary}
            save_json("05_meeting_chunks.json", chunk_result)
            {"chunk_count": len(chunks), "boundary": chunk_boundary}
            """),
            markdown("""
            ## 6차시 · LangChain MeetingBrief Pipeline

            fixture·Ollama·OpenAI가 같은 `MeetingBrief` 계약을 반환하도록 Prompt·Adapter·Parser·Policy를 분리합니다.
            """),
            code("""
            from src.langchain_lab import run_langchain_lab

            RUN_OLLAMA_LIVE = False
            provider = "ollama" if RUN_OLLAMA_LIVE else "fixture"
            chain_result = run_langchain_lab(transcript_text, provider=provider, allow_fallback=True)
            assert chain_result["checks"]["schema_valid"] is True
            assert chain_result["result"]["automatic_email"] is False
            save_json("06_meeting_brief.json", chain_result)
            {key: chain_result[key] for key in ("provider_requested", "provider_used", "fallback_reason")}
            """),
            markdown("""
            ## 7차시 · Action Item 근거 검증

            LLM이 만든 Action Item의 evidence ID가 실제 transcript에 없으면 HOLD합니다.
            """),
            code("""
            from src.course_services.meeting_service import validate_action_evidence

            known_ids = {segment["id"] for segment in stt_segments}
            normal_errors = validate_action_evidence(chain_result["result"]["action_items"], known_segment_ids=known_ids)
            boundary_errors = validate_action_evidence(
                [{"task": "근거 없는 발행", "evidence_ids": ["s999"]}],
                known_segment_ids=known_ids,
            )
            evidence_result = {"normal_errors": normal_errors, "boundary_errors": boundary_errors}
            assert normal_errors == []
            assert boundary_errors == ["ACTION_1_UNKNOWN_EVIDENCE:s999"]
            save_json("07_evidence_validation.json", evidence_result)
            evidence_result
            """),
            markdown("""
            ## 8차시 · Golden Set과 Day 2 Scorecard

            하루 결과를 현재 코드로 다시 생성하고 focused test를 실행합니다.
            """),
            code("""
            from src.course_services.course_demo import build_course_demo

            day2_scorecard = build_course_demo(2, workspace_root=ROOT)
            focused_test = run_command(sys.executable, "-m", "pytest", "-q", "tests/test_meeting_agent_workflow.py", "tests/test_course_services.py")
            day2_scorecard["focused_test"] = focused_test
            assert day2_scorecard["decision"] == "READY"
            assert focused_test["returncode"] == 0
            save_json("08_day2_scorecard.json", day2_scorecard)
            {"decision": day2_scorecard["decision"], "metrics": day2_scorecard["metrics"]}
            """),
        ],
    ),
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


def main() -> None:
    for day, payload in NOTEBOOKS.items():
        folder = ROOT / f"materials/day{day}"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"day{day}_service_lab.ipynb"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
