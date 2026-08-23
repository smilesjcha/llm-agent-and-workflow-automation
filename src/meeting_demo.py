"""Day 1 instructor demo: audio or transcript -> meeting result JSON.

The demo prefers a local faster-whisper transcription when an audio file is
present. If the model, package, or audio fails, it immediately falls back to
the supplied Korean transcript fixture so class flow never depends on a live
download or network connection.
"""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from typing import Any, Callable

from src.day1_agent import build_day1_summary


TIMESTAMP_LINE = re.compile(
    r"^\[(?P<minute>\d{2}):(?P<second>\d{2})\]\s*(?P<speaker>[^:]+):\s*(?P<text>.+)$"
)


def _rounded_float(value: Any, digits: int = 4) -> float | None:
    """Normalize NumPy/CT2 scalar values for JSON and LangGraph checkpoints."""

    return round(float(value), digits) if value is not None else None


def ensure_workspace_path(path: Path, workspace_root: Path) -> Path:
    """Resolve a classroom file path and block access outside the workspace."""

    resolved = path.resolve()
    root = workspace_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"WORKSPACE_PATH_BLOCKED: {path}")
    return resolved


def normalize_transcript_for_comparison(text: str) -> str:
    """Remove timestamps and speaker labels before comparing synthetic fixtures."""

    bodies: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"^(?:\[s\d+\])?(?:\[\d{2}:\d{2}\])?\s*", "", raw_line.strip())
        if ":" in line:
            line = line.split(":", 1)[1]
        bodies.append(line)
    return re.sub(r"[^0-9A-Za-z가-힣]", "", "".join(bodies)).lower()


def transcript_reference_similarity(actual: str, reference: str) -> float:
    """Return a deterministic 0..1 similarity for the synthetic audio exercise."""

    normalized_actual = normalize_transcript_for_comparison(actual)
    normalized_reference = normalize_transcript_for_comparison(reference)
    if not normalized_actual or not normalized_reference:
        return 0.0
    return round(SequenceMatcher(None, normalized_actual, normalized_reference).ratio(), 3)


def detect_quality_flags(
    text: str,
    *,
    average_log_probability: float | None = None,
    no_speech_probability: float | None = None,
    compression_ratio: float | None = None,
    average_word_probability: float | None = None,
) -> list[str]:
    """Return machine-checkable STT warnings that require human review."""

    flags: list[str] = []
    if not text.strip():
        flags.append("EMPTY_TEXT")
    if "\ufffd" in text:
        flags.append("REPLACEMENT_CHARACTER")
    if average_log_probability is not None and average_log_probability < -1.0:
        flags.append("LOW_AVERAGE_LOG_PROBABILITY")
    # Whisper treats a segment as silence only when both thresholds fail.
    if (
        no_speech_probability is not None
        and no_speech_probability > 0.6
        and (average_log_probability is None or average_log_probability < -1.0)
    ):
        flags.append("HIGH_NO_SPEECH_PROBABILITY")
    if compression_ratio is not None and compression_ratio > 2.4:
        flags.append("HIGH_COMPRESSION_RATIO")
    if average_word_probability is not None and average_word_probability < 0.45:
        flags.append("LOW_WORD_PROBABILITY")
    return flags


def mark_repeated_segments(segments: list[dict[str, Any]]) -> None:
    """Flag the third and later consecutive copy of the same STT text."""

    previous = ""
    consecutive_count = 0
    for segment in segments:
        normalized = re.sub(r"\W+", "", str(segment.get("text", ""))).lower()
        if normalized and normalized == previous:
            consecutive_count += 1
        else:
            previous = normalized
            consecutive_count = 1 if normalized else 0
        if consecutive_count >= 3:
            segment.setdefault("quality_flags", []).append("REPEATED_TEXT")


def build_quality_gate(
    segments: list[dict[str, Any]],
    *,
    mode: str,
    metadata: dict[str, Any] | None = None,
    expected_language: str = "ko",
    reference_similarity: float | None = None,
    minimum_reference_similarity: float = 0.80,
) -> dict[str, Any]:
    """Separate technical execution success from STT quality readiness."""

    metadata = metadata or {}
    mark_repeated_segments(segments)
    flagged = [segment for segment in segments if segment.get("quality_flags")]
    reasons = sorted(
        {
            flag
            for segment in flagged
            for flag in segment.get("quality_flags", [])
        }
    )
    if mode != "local_stt":
        reasons.insert(0, "STT_FALLBACK_USED")
    if not segments:
        reasons.append("NO_SPEECH_SEGMENTS")
    total_text_length = sum(len(str(segment.get("text", "")).strip()) for segment in segments)
    if total_text_length < 20:
        reasons.append("TRANSCRIPT_TOO_SHORT")
    detected_language = metadata.get("language")
    language_probability = metadata.get("language_probability")
    if detected_language and detected_language != expected_language:
        reasons.append("UNEXPECTED_LANGUAGE")
    if language_probability is not None and language_probability < 0.70:
        reasons.append("LOW_LANGUAGE_PROBABILITY")
    if (
        reference_similarity is not None
        and reference_similarity < minimum_reference_similarity
    ):
        reasons.append("LOW_REFERENCE_SIMILARITY")
    reasons = sorted(set(reasons))
    return {
        "decision": "HOLD" if reasons else "READY",
        "flagged_segment_count": len(flagged),
        "reasons": reasons,
        "human_decision_required": True,
        "detected_language": detected_language,
        "language_probability": language_probability,
        "segment_count": len(segments),
        "text_length": total_text_length,
        "reference_similarity": reference_similarity,
        "minimum_reference_similarity": minimum_reference_similarity
        if reference_similarity is not None
        else None,
    }


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
                "quality_flags": detect_quality_flags(body),
            }
        )
    return segments


def transcribe_with_faster_whisper(
    audio_path: Path,
    *,
    model_size: str,
    device: str,
    compute_type: str,
    language: str = "ko",
    beam_size: int = 5,
    hotwords: str | None = None,
    local_files_only: bool = False,
    compare_reference: bool = True,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Run local STT. Import is delayed so the core Day 1 demo stays optional."""

    from faster_whisper import WhisperModel  # type: ignore[import-not-found]

    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        local_files_only=local_files_only,
    )
    raw_segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=beam_size,
        word_timestamps=True,
        condition_on_previous_text=False,
        hotwords=hotwords,
    )
    segments: list[dict[str, Any]] = []
    lines: list[str] = []
    for index, segment in enumerate(raw_segments, start=1):
        body = segment.text.strip()
        average_log_probability = _rounded_float(getattr(segment, "avg_logprob", None))
        no_speech_probability = _rounded_float(getattr(segment, "no_speech_prob", None))
        compression_ratio = _rounded_float(getattr(segment, "compression_ratio", None))
        words = [
            {
                "start": _rounded_float(word.start, 2),
                "end": _rounded_float(word.end, 2),
                "word": word.word,
                "probability": _rounded_float(word.probability),
            }
            for word in (getattr(segment, "words", None) or [])
        ]
        average_word_probability = (
            sum(word["probability"] for word in words) / len(words) if words else None
        )
        segments.append(
            {
                "id": f"s{index:02d}",
                "start": _rounded_float(segment.start, 2),
                "end": _rounded_float(segment.end, 2),
                "speaker": None,
                "text": body,
                "average_log_probability": average_log_probability,
                "no_speech_probability": no_speech_probability,
                "compression_ratio": compression_ratio,
                "average_word_probability": _rounded_float(average_word_probability),
                "words": words,
                "quality_flags": detect_quality_flags(
                    body,
                    average_log_probability=average_log_probability,
                    no_speech_probability=no_speech_probability,
                    compression_ratio=compression_ratio,
                    average_word_probability=average_word_probability,
                ),
            }
        )
        minute, second = divmod(int(segment.start), 60)
        lines.append(f"[s{index:02d}][{minute:02d}:{second:02d}] 화자미상: {body}")
    metadata = {
        "language": info.language,
        "language_probability": _rounded_float(info.language_probability),
        "duration_seconds": _rounded_float(info.duration, 2),
        "duration_after_vad_seconds": _rounded_float(info.duration_after_vad, 2),
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "beam_size": beam_size,
        "vad_filter": True,
        "word_timestamps": True,
        "condition_on_previous_text": False,
    }
    return "\n".join(lines), segments, metadata


def run_demo(
    *,
    audio_path: Path,
    transcript_path: Path,
    output_dir: Path,
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "int8",
    language: str = "ko",
    beam_size: int = 5,
    hotwords: str | None = None,
    local_files_only: bool = False,
    compare_reference: bool = True,
    transcriber: Callable[..., tuple[str, list[dict[str, Any]], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Run the live path when possible and always keep a deterministic fallback."""

    mode = "fixture"
    fallback_reason: str | None = None
    reference_text = transcript_path.read_text(encoding="utf-8")
    transcription_metadata: dict[str, Any] = {
        "language": language,
        "language_probability": None,
        "model": model_size,
    }
    if audio_path.exists():
        try:
            selected_transcriber = transcriber or transcribe_with_faster_whisper
            transcript_text, segments, transcription_metadata = selected_transcriber(
                audio_path,
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                language=language,
                beam_size=beam_size,
                hotwords=hotwords,
                local_files_only=local_files_only,
            )
            mode = "local_stt"
        except Exception as exc:  # classroom fallback boundary
            fallback_reason = f"STT_EXECUTION_FAILED: {type(exc).__name__}"
            transcript_text = reference_text
            segments = parse_transcript(transcript_text)
    else:
        fallback_reason = f"audio_not_found: {audio_path}"
        transcript_text = reference_text
        segments = parse_transcript(transcript_text)

    summary = build_day1_summary(transcript_text)
    reference_similarity = (
        transcript_reference_similarity(transcript_text, reference_text)
        if compare_reference
        else None
    )
    quality_gate = build_quality_gate(
        segments,
        mode=mode,
        metadata=transcription_metadata,
        expected_language=language,
        reference_similarity=reference_similarity,
    )
    evidence_ids = [segment["id"] for segment in segments if "id" in segment]
    for index, action in enumerate(summary["action_items"]):
        evidence_index = min(index + 3, len(evidence_ids) - 1)
        action["evidence_ids"] = [evidence_ids[evidence_index]] if evidence_ids else []

    result = {
        "status": "SUCCESS",
        "mode": mode,
        "fallback_reason": fallback_reason,
        "transcription_metadata": transcription_metadata,
        "input": {
            "audio": str(audio_path),
            "transcript_fixture": str(transcript_path),
        },
        "policy": {
            "automatic_email": False,
            "requires_human_approval": True,
        },
        "quality_gate": quality_gate,
        "segments": segments,
        "meeting_result": summary,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcript.txt").write_text(transcript_text, encoding="utf-8")
    (output_dir / "transcript.json").write_text(
        json.dumps(
            {
                "mode": mode,
                "fallback_reason": fallback_reason,
                "metadata": transcription_metadata,
                "quality_gate": quality_gate,
                "segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
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
    parser.add_argument("--language", default="ko")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--hotwords")
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Use a model already cached on this computer; never download during class.",
    )
    parser.add_argument(
        "--skip-reference-check",
        action="store_true",
        help="Skip fixture similarity when no reviewed reference transcript exists.",
    )
    args = parser.parse_args()
    workspace_root = Path.cwd().resolve()
    audio_path = ensure_workspace_path(args.audio, workspace_root)
    transcript_path = ensure_workspace_path(args.transcript, workspace_root)
    output_dir = ensure_workspace_path(args.out, workspace_root)
    result = run_demo(
        audio_path=audio_path,
        transcript_path=transcript_path,
        output_dir=output_dir,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
        hotwords=args.hotwords,
        local_files_only=args.local_files_only,
        compare_reference=not args.skip_reference_check,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "mode": result["mode"],
                "fallback_reason": result["fallback_reason"],
                "outputs": [
                    str(output_dir / "transcript.txt"),
                    str(output_dir / "transcript.json"),
                    str(output_dir / "meeting_result.json"),
                ],
                "automatic_email": result["policy"]["automatic_email"],
                "requires_human_approval": result["policy"]["requires_human_approval"],
                "quality_gate": result["quality_gate"]["decision"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
