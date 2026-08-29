"""Deterministic and local live STT adapters."""

from __future__ import annotations

import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .models import TranscriptSegment


FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "meeting_transcript_ko.json"


class STTError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def fixture_transcribe() -> list[TranscriptSegment]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [TranscriptSegment.model_validate(item) for item in payload["segments"]]


@lru_cache(maxsize=2)
def _whisper_model(model_name: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise STTError("LIVE_STT_DEPENDENCY_MISSING") from exc

    try:
        return WhisperModel(model_name, device="cpu", compute_type="int8")
    except Exception as exc:  # Provider/model initialization is normalized at this boundary.
        raise STTError("LIVE_STT_MODEL_UNAVAILABLE") from exc


def live_transcribe(*, data: bytes, suffix: str) -> list[TranscriptSegment]:
    model_name = os.getenv("WHISPER_MODEL", "small")
    model = _whisper_model(model_name)
    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
            audio_file.write(data)
            temp_path = audio_file.name
        raw_segments, _ = model.transcribe(
            temp_path,
            language="ko",
            vad_filter=True,
            beam_size=5,
            condition_on_previous_text=False,
        )
        segments = [
            TranscriptSegment(
                id=f"s{index:03d}",
                start=round(float(segment.start), 3),
                end=round(float(segment.end), 3),
                speaker="화자 미상",
                text=str(segment.text).strip(),
            )
            for index, segment in enumerate(raw_segments, start=1)
            if str(segment.text).strip()
        ]
    except STTError:
        raise
    except Exception as exc:  # Runtime/codec failures share a stable public error.
        raise STTError("LIVE_STT_FAILED") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
    return segments


def quality_errors(segments: list[TranscriptSegment]) -> list[str]:
    errors: list[str] = []
    if not segments:
        return ["EMPTY_TRANSCRIPT"]
    if len("".join(segment.text for segment in segments)) < 30:
        errors.append("TRANSCRIPT_TOO_SHORT")
    ids = [segment.id for segment in segments]
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_SEGMENT_ID")
    for previous, current in zip(segments, segments[1:]):
        if current.start < previous.start:
            errors.append("NON_MONOTONIC_TIMESTAMPS")
            break
    return errors
