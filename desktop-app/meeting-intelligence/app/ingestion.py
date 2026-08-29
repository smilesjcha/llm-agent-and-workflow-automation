"""Adapters for Google Meet/plain transcripts and ClovaNote text exports."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError

from .models import Participant, TranscriptSegment


MAX_TRANSCRIPT_BYTES = 2 * 1024 * 1024
MAX_CONTEXT_CHARS = 20_000
MAX_PARTICIPANTS = 50


class InputError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def safe_filename(filename: str | None, default: str) -> str:
    return Path(filename or default).name


def decode_transcript(data: bytes) -> str:
    if not data:
        raise InputError("EMPTY_TRANSCRIPT_FILE")
    if len(data) > MAX_TRANSCRIPT_BYTES:
        raise InputError("TRANSCRIPT_FILE_TOO_LARGE")
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise InputError("TRANSCRIPT_ENCODING_UNSUPPORTED")
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if "\x00" in text:
        raise InputError("TRANSCRIPT_BINARY_CONTENT")
    if not text:
        raise InputError("EMPTY_TRANSCRIPT_FILE")
    return text


def validate_context(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if len(cleaned) > MAX_CONTEXT_CHARS:
        raise InputError(f"{field_name.upper()}_TOO_LONG")
    return cleaned


def parse_participants(raw: str) -> list[Participant]:
    """Accept a JSON array/object or friendly `이름 | 역할 | 팀 | 이메일` lines."""

    cleaned = raw.strip()
    if not cleaned:
        return []
    if len(cleaned) > 32_000:
        raise InputError("PARTICIPANT_METADATA_TOO_LARGE")
    values: list[dict]
    if cleaned.startswith("[") or cleaned.startswith("{"):
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise InputError("PARTICIPANT_METADATA_INVALID") from exc
        if isinstance(payload, dict):
            payload = payload.get("participants")
        if not isinstance(payload, list):
            raise InputError("PARTICIPANT_METADATA_INVALID")
        values = []
        for value in payload:
            if isinstance(value, str):
                values.append({"name": value.strip()})
            elif isinstance(value, dict):
                values.append(value)
            else:
                raise InputError("PARTICIPANT_METADATA_INVALID")
    else:
        values = []
        for line in cleaned.splitlines():
            line = re.sub(r"^[\s*\-•]+", "", line).strip()
            if not line:
                continue
            pieces = [piece.strip() for piece in re.split(r"\s*[|\t,]\s*", line) if piece.strip()]
            if not pieces:
                continue
            value: dict[str, str] = {"name": pieces[0]}
            non_email = [piece for piece in pieces[1:] if "@" not in piece]
            email = next((piece for piece in pieces[1:] if "@" in piece), None)
            if non_email:
                value["role"] = non_email[0]
            if len(non_email) > 1:
                value["team"] = non_email[1]
            if email:
                value["email"] = email
            values.append(value)
    if not values or len(values) > MAX_PARTICIPANTS:
        raise InputError("PARTICIPANT_COUNT_INVALID")
    try:
        participants = [Participant.model_validate(value) for value in values]
    except ValidationError as exc:
        raise InputError("PARTICIPANT_METADATA_INVALID") from exc
    normalized_names = [participant.name.casefold() for participant in participants]
    if len(normalized_names) != len(set(normalized_names)):
        raise InputError("DUPLICATE_PARTICIPANT")
    return participants


_CLOCK = r"(?:\d{1,2}:)?\d{1,2}:\d{2}"
_BRACKET_LINE = re.compile(
    rf"^\[?(?P<time>{_CLOCK})\]?\s+(?P<speaker>[^:：\[\]]{{1,80}}?)\s*[:：]\s*(?P<text>.+)$"
)
_SPEAKER_TIME_TEXT = re.compile(
    rf"^(?P<speaker>[^:：\[\]]{{1,80}}?)\s+\[?(?P<time>{_CLOCK})\]?\s*[:：]\s*(?P<text>.+)$"
)
_HEADER = re.compile(
    rf"^(?P<speaker>(?:참석자|화자)\s*\d+|[^:：\[\]]{{1,80}}?)\s+\[?(?P<time>{_CLOCK})\]?$"
)
_SPEAKER_TEXT = re.compile(r"^(?P<speaker>[^:：]{1,80})\s*[:：]\s*(?P<text>.+)$")


def _seconds(value: str) -> float:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes * 60 + seconds)
    hours, minutes, seconds = parts
    return float(hours * 3600 + minutes * 60 + seconds)


def _speaker_name(raw: str, participants: list[Participant]) -> str:
    value = re.sub(r"\s+", " ", raw).strip(" []")
    numbered = re.fullmatch(r"(?:참석자|화자)\s*(\d+)", value)
    if numbered:
        index = int(numbered.group(1)) - 1
        if 0 <= index < len(participants):
            return participants[index].name
    return value[:80] or "화자 미상"


def _raw_turns(text: str, participants: list[Participant]) -> list[tuple[float | None, str, str]]:
    turns: list[tuple[float | None, str, str]] = []
    current_time: float | None = None
    current_speaker: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_time, current_speaker, current_text
        merged = " ".join(piece.strip() for piece in current_text if piece.strip()).strip()
        if current_speaker and merged:
            turns.append((current_time, current_speaker, merged))
        current_time, current_speaker, current_text = None, None, []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        matched = _BRACKET_LINE.match(line) or _SPEAKER_TIME_TEXT.match(line)
        if matched:
            flush()
            turns.append(
                (
                    _seconds(matched.group("time")),
                    _speaker_name(matched.group("speaker"), participants),
                    matched.group("text").strip(),
                )
            )
            continue
        header = _HEADER.match(line)
        if header:
            flush()
            current_time = _seconds(header.group("time"))
            current_speaker = _speaker_name(header.group("speaker"), participants)
            continue
        speaker_text = _SPEAKER_TEXT.match(line)
        if speaker_text and not re.match(r"^(일시|장소|제목|회의명|참석자|메모)$", speaker_text.group("speaker")):
            flush()
            turns.append(
                (
                    None,
                    _speaker_name(speaker_text.group("speaker"), participants),
                    speaker_text.group("text").strip(),
                )
            )
            continue
        if current_speaker:
            current_text.append(line)
        elif turns:
            prior_time, prior_speaker, prior_text = turns[-1]
            turns[-1] = (prior_time, prior_speaker, f"{prior_text} {line}".strip())
        elif len(line) >= 4:
            default_speaker = participants[0].name if len(participants) == 1 else "화자 미상"
            turns.append((None, default_speaker, line))
    flush()
    return turns


def parse_transcript(text: str, *, source: str, participants: list[Participant]) -> list[TranscriptSegment]:
    if source not in {"google_meet", "clova_note"}:
        raise InputError("UNKNOWN_TEXT_SOURCE")
    turns = _raw_turns(text, participants)
    if not turns:
        raise InputError("TRANSCRIPT_PARSE_FAILED")
    segments: list[TranscriptSegment] = []
    previous_start = 0.0
    for index, (provided_start, speaker, turn_text) in enumerate(turns, start=1):
        start = provided_start if provided_start is not None else (previous_start if index == 1 else previous_start + 5.0)
        if start < previous_start:
            raise InputError("TRANSCRIPT_TIME_ORDER_INVALID")
        previous_start = start
        next_time = turns[index][0] if index < len(turns) else None
        estimated_end = start + max(2.0, min(30.0, len(turn_text) / 7.0))
        end = max(start, min(estimated_end, next_time)) if next_time is not None and next_time >= start else estimated_end
        segments.append(
            TranscriptSegment(
                id=f"s{index:03d}",
                start=round(start, 3),
                end=round(end, 3),
                speaker=speaker,
                text=turn_text,
            )
        )
    return segments
