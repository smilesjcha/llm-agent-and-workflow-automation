"""Day 1 instructor demo: audio or transcript -> meeting result JSON.

The demo prefers a local faster-whisper transcription when an audio file is
present. If the model, package, or audio fails, it immediately falls back to
the supplied Korean transcript fixture so class flow never depends on a live
download or network connection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from src.day1_agent import build_day1_summary


TIMESTAMP_LINE = re.compile(
    r"^\[(?P<minute>\d{2}):(?P<second>\d{2})\]\s*(?P<speaker>[^:]+):\s*(?P<text>.+)$"
)


def parse_transcript(text: str) -> list[dict[str, Any]]:
    """Convert the classroom timestamp format into evidence-ready segments."""

    segments: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = TIMESTAMP_LINE.match(line)
        if match:
            start = int(match.group("minute")) * 60 + int(match.group("second"))
            speaker = match.group("speaker").strip()
            body = match.group("text").strip()
        else:
            start = None
            speaker = None
            body = line
        segments.append(
            {
                "id": f"s{index:02d}",
                "start": start,
                "speaker": speaker,
                "text": body,
                "quality_flags": [],
            }
        )
    return segments


def transcribe_with_faster_whisper(
    audio_path: Path,
    *,
    model_size: str,
    device: str,
    compute_type: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Run local STT. Import is delayed so the core Day 1 demo stays optional."""

    from faster_whisper import WhisperModel  # type: ignore[import-not-found]

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    raw_segments, info = model.transcribe(
        str(audio_path),
        language="ko",
        vad_filter=True,
        beam_size=5,
    )
    segments: list[dict[str, Any]] = []
    lines: list[str] = []
    for index, segment in enumerate(raw_segments, start=1):
        body = segment.text.strip()
        segments.append(
            {
                "id": f"s{index:02d}",
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "speaker": None,
                "text": body,
                "quality_flags": [],
            }
        )
        lines.append(f"[{segment.start:06.2f}] {body}")
    metadata = {
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
    }
    return "\n".join(lines), [{"metadata": metadata}, *segments]


def run_demo(
    *,
    audio_path: Path,
    transcript_path: Path,
    output_dir: Path,
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "int8",
) -> dict[str, Any]:
    """Run the live path when possible and always keep a deterministic fallback."""

    mode = "fixture"
    fallback_reason: str | None = None
    if audio_path.exists():
        try:
            transcript_text, segments = transcribe_with_faster_whisper(
                audio_path,
                model_size=model_size,
                device=device,
                compute_type=compute_type,
            )
            mode = "local_stt"
        except Exception as exc:  # classroom fallback boundary
            fallback_reason = f"{type(exc).__name__}: {exc}"
            transcript_text = transcript_path.read_text(encoding="utf-8")
            segments = parse_transcript(transcript_text)
    else:
        fallback_reason = f"audio_not_found: {audio_path}"
        transcript_text = transcript_path.read_text(encoding="utf-8")
        segments = parse_transcript(transcript_text)

    summary = build_day1_summary(transcript_text)
    evidence_ids = [segment["id"] for segment in segments if "id" in segment]
    for index, action in enumerate(summary["action_items"]):
        evidence_index = min(index + 3, len(evidence_ids) - 1)
        action["evidence_ids"] = [evidence_ids[evidence_index]] if evidence_ids else []

    result = {
        "status": "SUCCESS",
        "mode": mode,
        "fallback_reason": fallback_reason,
        "input": {
            "audio": str(audio_path),
            "transcript_fixture": str(transcript_path),
        },
        "policy": {
            "automatic_email": False,
            "requires_human_approval": True,
        },
        "segments": segments,
        "meeting_result": summary,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcript.json").write_text(
        json.dumps({"mode": mode, "segments": segments}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "meeting_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path, default=Path("data/demo_meeting.wav"))
    parser.add_argument("--transcript", type=Path, default=Path("data/demo_meeting_transcript.txt"))
    parser.add_argument("--out", type=Path, default=Path("output/day1-demo"))
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()
    result = run_demo(
        audio_path=args.audio,
        transcript_path=args.transcript,
        output_dir=args.out,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "mode": result["mode"],
                "fallback_reason": result["fallback_reason"],
                "outputs": [
                    str(args.out / "transcript.json"),
                    str(args.out / "meeting_result.json"),
                ],
                "automatic_email": result["policy"]["automatic_email"],
                "requires_human_approval": result["policy"]["requires_human_approval"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
