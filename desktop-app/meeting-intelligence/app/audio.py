"""Audio upload validation without persisting the original meeting."""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import Optional

from .models import AudioMetadata


MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}


class AudioValidationError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def inspect_audio(*, filename: str, content_type: Optional[str], data: bytes) -> AudioMetadata:
    """Validate the upload and return metadata; never trusts the supplied path."""

    safe_name = Path(filename or "upload").name
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AudioValidationError("UNSUPPORTED_AUDIO_TYPE")
    if not data:
        raise AudioValidationError("EMPTY_AUDIO")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AudioValidationError("AUDIO_TOO_LARGE")

    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    if extension == ".wav":
        try:
            with wave.open(io.BytesIO(data), "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                frame_count = wav_file.getnframes()
                duration = round(frame_count / sample_rate, 3) if sample_rate else None
        except (wave.Error, EOFError):
            raise AudioValidationError("INVALID_WAV") from None
    else:
        duration, sample_rate, channels = _inspect_compressed_audio(data)

    return AudioMetadata(
        filename=safe_name,
        content_type=content_type,
        size_bytes=len(data),
        format=extension.removeprefix("."),
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
    )


def _inspect_compressed_audio(data: bytes) -> tuple[Optional[float], Optional[int], Optional[int]]:
    """Read compressed-audio metadata through PyAV without decoding the full meeting."""

    try:
        import av
    except ImportError as exc:
        raise AudioValidationError("AUDIO_METADATA_DEPENDENCY_MISSING") from exc

    try:
        with av.open(io.BytesIO(data), mode="r") as container:
            stream = next((candidate for candidate in container.streams if candidate.type == "audio"), None)
            if stream is None:
                raise AudioValidationError("INVALID_AUDIO")
            codec_context = stream.codec_context
            sample_rate_value = getattr(codec_context, "sample_rate", None) or getattr(stream, "rate", None)
            channel_value = getattr(codec_context, "channels", None)
            if not channel_value and getattr(stream, "layout", None):
                channel_value = len(stream.layout.channels)

            duration_value: Optional[float] = None
            if stream.duration is not None and stream.time_base is not None:
                duration_value = float(stream.duration * stream.time_base)
            elif container.duration is not None:
                duration_value = float(container.duration / av.time_base)
            if duration_value is None or duration_value <= 0:
                raise AudioValidationError("INVALID_AUDIO")
            return (
                round(duration_value, 3),
                int(sample_rate_value) if sample_rate_value else None,
                int(channel_value) if channel_value else None,
            )
    except AudioValidationError:
        raise
    except Exception as exc:  # Codec/container errors are normalized at this input boundary.
        raise AudioValidationError("INVALID_AUDIO") from exc
