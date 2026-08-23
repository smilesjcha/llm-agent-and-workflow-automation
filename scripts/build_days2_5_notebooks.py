"""Generate runnable Day 2-5 notebooks with install and recovery cells."""

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
            markdown(f"""
            # {title}

            화면을 따라 실행하되, 결과를 자동 게시하지 않습니다. 모든 외부 쓰기는 dry-run과 사람 승인을 먼저 거칩니다.
            """),
            code(f"""
            # 최초 1회 설치. 이미 설치했다면 빠르게 완료됩니다.
            %pip install -q -r ../../requirements-day1.txt
            # STT 실습을 실제 음성으로 실행할 때만 다음 줄의 주석을 해제합니다.
            # %pip install -q -r ../../requirements-stt-optional.txt
            """),
            code("""
            from pathlib import Path
            import json, sys

            ROOT = Path.cwd().resolve().parents[1]
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            print({"workspace": str(ROOT), "python": sys.version.split()[0]})
            """),
            *cells,
            markdown(f"""
            ## 완료 확인

            - Day {day} 결과 JSON을 확인했습니다.
            - 실패 경로가 traceback 대신 `error_code`로 남는지 확인했습니다.
            - 외부 쓰기와 자동 메일이 발생하지 않았음을 확인했습니다.
            - 변경한 코드는 diff와 test 결과를 사람이 검토합니다.
            """),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
            "course_day": day,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = {
    2: notebook(
        "Day 2 · 한국어 회의 음성을 근거가 남는 결과로 바꾸기",
        2,
        [
            markdown("""
            ## 1. 오디오와 정답 전사문을 먼저 확인합니다

            `RUN_STT_LIVE=False`가 기본값입니다. 수업 흐름은 fixture로 먼저 검증한 뒤, 모델이 준비된 컴퓨터만 실제 STT를 실행합니다.
            """),
            code("""
            import wave

            audio_path = ROOT / "data/demo_meeting.wav"
            transcript_path = ROOT / "data/demo_meeting_transcript.txt"
            with wave.open(str(audio_path), "rb") as wav:
                audio_meta = {
                    "seconds": round(wav.getnframes() / wav.getframerate(), 2),
                    "sample_rate": wav.getframerate(),
                    "channels": wav.getnchannels(),
                }
            print(audio_meta)
            print(transcript_path.read_text(encoding="utf-8")[:500])
            """),
            markdown("## 2. 발화 단위로 나눈 뒤 chunk와 evidence ID를 보존합니다"),
            code("""
            from src.course_services.meeting_service import prepare_transcript_for_summary

            transcript = transcript_path.read_text(encoding="utf-8")
            prepared = prepare_transcript_for_summary(transcript, max_chars=500)
            print(json.dumps({
                "status": prepared["status"],
                "segment_count": len(prepared["segments"]),
                "chunks": [c["segment_ids"] for c in prepared["chunks"]],
            }, ensure_ascii=False, indent=2))
            """),
            markdown("## 3. 선택적으로 faster-whisper를 실행하고 품질 gate를 확인합니다"),
            code("""
            from src.meeting_demo import run_demo

            RUN_STT_LIVE = False
            if RUN_STT_LIVE:
                stt_result = run_demo(
                    audio_path=audio_path,
                    transcript_path=transcript_path,
                    output_dir=ROOT / "output/day2-stt-lab",
                    model_size="small",
                    device="cpu",
                    compute_type="int8",
                    local_files_only=True,
                )
                print(json.dumps(stt_result["quality_gate"], ensure_ascii=False, indent=2))
            else:
                print("STT_LIVE_SKIPPED: fixture 기반 chunk·schema 실습을 계속합니다.")
            """),
        ],
    ),
    3: notebook(
        "Day 3 · 변경 라인에 근거를 남기는 코드 리뷰 Agent",
        3,
        [
            markdown("## 1. unified diff를 읽고 추가 라인 번호를 복원합니다"),
            code("""
            from src.course_services.review_service import parse_unified_diff, run_review_service

            diff_path = ROOT / "data/day3_review_cases/unsafe_pr.diff"
            diff_text = diff_path.read_text(encoding="utf-8")
            parsed = parse_unified_diff(diff_text)
            print(parsed.changed_paths)
            print([(line.line, line.text) for line in parsed.added_lines])
            """),
            markdown("## 2. 결정론적 baseline으로 고위험 finding을 만듭니다"),
            code("""
            review = run_review_service(diff_text)
            print(json.dumps(review, ensure_ascii=False, indent=2))
            assert all(finding["line"] in {line.line for line in parsed.added_lines} for finding in review["findings"])
            assert review["automatic_publish"] is False
            """),
            markdown("## 3. Codex에게 맡길 작업도 scope와 test 계약부터 씁니다"),
            code("""
            from src.course_services.codex_harness import CodexTaskSpec, render_codex_task

            spec = CodexTaskSpec(
                objective="새 review rule 하나와 정상·실패 test를 추가한다.",
                allowed_paths=("src/course_services", "tests"),
                acceptance_tests=("python -m pytest -q tests/test_course_services.py",),
            )
            print(render_codex_task(spec))
            """),
        ],
    ),
    4: notebook(
        "Day 4 · GitHub PR 리뷰를 dry-run과 사람 승인으로 보호하기",
        4,
        [
            markdown("## 1. synthetic PR fixture를 읽고 target을 고정합니다"),
            code("""
            from src.course_services.github_service import (
                InMemoryIdempotencyStore, load_pr_fixture,
                prepare_review_comment, publish_review_comment,
            )
            from src.course_services.review_service import run_review_service

            fixture = load_pr_fixture(ROOT / "data/day4_github/pr_fixture.json", workspace_root=ROOT)
            diff_text = (ROOT / fixture["diff"]).read_text(encoding="utf-8")
            report = run_review_service(diff_text)
            target = {key: fixture[key] for key in ("repository", "number", "head_sha")}
            print(target)
            """),
            markdown("## 2. 첫 실행은 무조건 dry-run payload입니다"),
            code("""
            dry_run_plan = prepare_review_comment(report=report, target=target, dry_run=True)
            print(json.dumps(dry_run_plan, ensure_ascii=False, indent=2))
            assert dry_run_plan["external_write"] is False
            """),
            markdown("## 3. 수업에서는 fake publisher로 승인과 중복 방지를 검증합니다"),
            code("""
            approval_plan = prepare_review_comment(report=report, target=target, dry_run=False)
            store = InMemoryIdempotencyStore()
            calls = []

            def fake_publisher(pr_target, body):
                calls.append({"target": pr_target.model_dump(), "body": body})
                return {"id": 101, "url": "https://example.invalid/reviews/101"}

            first = publish_review_comment(
                plan=approval_plan, human_approved=True, publisher=fake_publisher, store=store,
            )
            second = publish_review_comment(
                plan=approval_plan, human_approved=True, publisher=fake_publisher, store=store,
            )
            print(json.dumps({"first": first, "second": second, "call_count": len(calls)}, ensure_ascii=False, indent=2))
            assert len(calls) == 1
            """),
        ],
    ),
    5: notebook(
        "Day 5 · 두 서비스를 라우팅하고 평가로 배포를 결정하기",
        5,
        [
            markdown("## 1. 입력 종류를 명시해 회의와 코드 리뷰 서비스로 라우팅합니다"),
            code("""
            from src.course_services.service_router import route_service_request

            meeting = route_service_request(
                input_kind="meeting_transcript",
                source_path=ROOT / "data/meeting_sample_ko.txt",
                workspace_root=ROOT,
            )
            review = route_service_request(
                input_kind="code_diff",
                source_path=ROOT / "data/day3_review_cases/unsafe_pr.diff",
                workspace_root=ROOT,
            )
            print(json.dumps({"meeting": meeting["service"], "review": review["service"]}, ensure_ascii=False, indent=2))
            """),
            markdown("## 2. Golden finding과 현재 결과를 같은 key로 비교합니다"),
            code("""
            from src.course_services.eval_service import evaluate_review_findings, release_gate

            expected = json.loads((ROOT / "data/day5_eval/golden_review_findings.json").read_text(encoding="utf-8"))
            metrics = evaluate_review_findings(review["result"]["findings"], expected)
            gate = release_gate(review_metrics=metrics, safety_passed=True, latency_seconds=0.2)
            print(json.dumps({"metrics": metrics, "release_gate": gate}, ensure_ascii=False, indent=2))
            """),
            markdown("## 3. HOLD를 일부러 만들어 운영 판단을 연습합니다"),
            code("""
            hold = release_gate(
                review_metrics={"precision": 0.7, "recall": 0.6},
                safety_passed=False,
                latency_seconds=42.0,
            )
            print(json.dumps(hold, ensure_ascii=False, indent=2))
            assert hold["decision"] == "HOLD"
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
