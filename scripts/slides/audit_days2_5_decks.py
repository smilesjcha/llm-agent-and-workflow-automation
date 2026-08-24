"""Audit Day 2-5 inspect NDJSON against the lecture content harness."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
GENERIC_TITLES = {
    "문제와 필요성",
    "차시 목표",
    "핵심 용어 4가지",
    "입력·처리·결과·검증",
    "5단계 실행 흐름",
    "성공·실패 계약",
    "저장소 파일 지도",
    "개념과 코드 연결",
    "역할과 선택 기준",
    "대표 실패",
    "복구 경로",
    "Codex 검증 루프",
    "Codex 작업 명세",
    "실행 명령",
    "완료 기준",
    "서비스 운영 점검",
}
INTERNAL_META = ("KEY POINT", "QUALITY VALIDATION", "장표 리듬", "제작 기준", "중복률")
CONTRACT_MARKERS = (
    "test",
    "READY",
    "HOLD",
    "error_code",
    "external_write",
    "status",
    "provider",
    "fixture",
    "schema",
    "evidence",
    "사람 승인",
    "실행 command",
    "반환",
    "차단",
    "validate",
    "validation",
    "line",
    "segment",
    "chunk",
    "diff",
    "WAV",
    "STT",
    "PII",
    "LLM",
    "JSON",
    "PR ",
    "token",
    "retry",
    "publish",
    "upload",
    "reused",
    "precision",
    "recall",
    "confidence",
    "workspace",
    "max_chars",
    "ACTION_",
    "absolute path",
    "hunk",
    "finding",
    "eval",
    "cache",
    ".env",
    "429",
    "approve",
    "reject",
    "terminal state",
    "head SHA",
    "payload",
    "repo",
    "unknown kind",
    "비밀키",
    "자동 외부 쓰기",
    "재현할 수 있다",
    "게시 후보",
)
PATH_MARKERS = ("/", ".py", ".json", ".jsonl", ".ipynb", ".wav", "python -m", "https://")


def normalize(text: str) -> str:
    return " ".join(text.split())


def is_narrative(text: str, titles: set[str]) -> bool:
    if len(text) < 24:
        return False
    if text in titles:
        return False
    if text.startswith("DAY ") or re.fullmatch(r"\d{3}", text):
        return False
    if any(marker in text for marker in PATH_MARKERS + CONTRACT_MARKERS):
        return False
    return bool(re.search(r"[가-힣]", text)) and text.endswith(("다.", "니다."))


def is_contract(text: str, titles: set[str]) -> bool:
    if len(text) < 18 or text in titles or text.startswith("DAY "):
        return False
    if any(marker in text for marker in PATH_MARKERS):
        return False
    return any(marker in text for marker in CONTRACT_MARKERS)


def audit(day: int) -> dict:
    inspect_path = ROOT / f"slides/IPA_LLM_Agent_업무자동화_Day{day}_DRAFT_240p.pptx.inspect.ndjson"
    records = [json.loads(line) for line in inspect_path.read_text(encoding="utf-8").splitlines()]
    titles = [normalize(row.get("title", "")) for row in records if row["kind"] == "slide"]
    title_set = set(titles)
    title_counts = Counter(titles)
    exact_duplicates = {title: count for title, count in title_counts.items() if count > 1}
    generic_hits = sorted({title for title in titles if title in GENERIC_TITLES})

    text_slides: defaultdict[str, list[int]] = defaultdict(list)
    contract_slides: defaultdict[str, list[int]] = defaultdict(list)
    internal_hits: list[dict] = []
    for row in records:
        if row["kind"] != "textbox":
            continue
        text = normalize(row.get("text", ""))
        if is_narrative(text, title_set):
            text_slides[text].append(row["slide"])
        if is_contract(text, title_set):
            contract_slides[text].append(row["slide"])
        if any(marker in text.upper() for marker in INTERNAL_META):
            internal_hits.append({"slide": row["slide"], "text": text})

    repeated_narrative = [
        {"text": text, "slides": slides}
        for text, slides in sorted(text_slides.items())
        if len(set(slides)) > 1
    ]
    contract_overuse = [
        {"text": text, "slides": slides}
        for text, slides in sorted(contract_slides.items())
        if len(set(slides)) > 4
    ]
    return {
        "day": day,
        "slide_count": len(titles),
        "exact_title_duplicates": exact_duplicates,
        "generic_title_hits": generic_hits,
        "repeated_narrative": repeated_narrative,
        "contract_overuse": contract_overuse,
        "internal_meta_hits": internal_hits,
        "passed": len(titles) == 240
        and not exact_duplicates
        and not generic_hits
        and not repeated_narrative
        and not contract_overuse
        and not internal_hits,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "output/course-quality/deck_content_audit.json")
    args = parser.parse_args()
    report = {"days": [audit(day) for day in (2, 3, 4, 5)]}
    report["passed"] = all(day["passed"] for day in report["days"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
