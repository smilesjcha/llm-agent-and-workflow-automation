"""Build a multi-speaker Korean WAV from the synthetic meeting transcript."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import tempfile
import wave


LINE_PATTERN = re.compile(r"^\[(?P<time>\d{2}:\d{2})\]\s*(?P<speaker>[^:]+):\s*(?P<text>.+)$")
VOICE_BY_SPEAKER = {
    "민지": "Yuna",
    "서연": "Flo (한국어(한국))",
    "준호": "Reed (한국어(한국))",
    "현우": "Eddy (한국어(한국))",
}


def parse_turns(transcript_path: Path) -> list[tuple[str, str]]:
    turns: list[tuple[str, str]] = []
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        match = LINE_PATTERN.match(line.strip())
        if not match:
            continue
        turns.append((match.group("speaker").strip(), match.group("text").strip()))
    if not turns:
        raise ValueError(f"No timestamped turns found in {transcript_path}")
    return turns


def build_audio(
    transcript_path: Path,
    output_path: Path,
    *,
    speech_rate: int = 145,
    silence_seconds: float = 0.45,
) -> float:
    turns = parse_turns(transcript_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="meeting-tts-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        segment_paths: list[Path] = []
        for index, (speaker, text) in enumerate(turns, start=1):
            voice = VOICE_BY_SPEAKER.get(speaker, "Yuna")
            aiff_path = temp_dir / f"{index:03d}.aiff"
            wav_path = temp_dir / f"{index:03d}.wav"
            subprocess.run(
                ["say", "-v", voice, "-r", str(speech_rate), "-o", str(aiff_path), text],
                check=True,
            )
            subprocess.run(
                [
                    "afconvert",
                    "-f",
                    "WAVE",
                    "-d",
                    "LEI16@22050",
                    str(aiff_path),
                    str(wav_path),
                ],
                check=True,
            )
            segment_paths.append(wav_path)

        with wave.open(str(segment_paths[0]), "rb") as first:
            channels = first.getnchannels()
            sample_width = first.getsampwidth()
            frame_rate = first.getframerate()

        silence_frames = int(frame_rate * silence_seconds)
        silence = b"\x00" * silence_frames * channels * sample_width
        total_frames = 0
        with wave.open(str(output_path), "wb") as target:
            target.setnchannels(channels)
            target.setsampwidth(sample_width)
            target.setframerate(frame_rate)
            for segment_path in segment_paths:
                with wave.open(str(segment_path), "rb") as source:
                    params = (source.getnchannels(), source.getsampwidth(), source.getframerate())
                    if params != (channels, sample_width, frame_rate):
                        raise ValueError(f"Audio format mismatch: {segment_path}")
                    frames = source.readframes(source.getnframes())
                    target.writeframes(frames)
                    target.writeframes(silence)
                    total_frames += source.getnframes() + silence_frames

    return total_frames / frame_rate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transcript",
        type=Path,
        default=Path("data/meeting_sample_ko_12min.txt"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/meeting_sample_ko_12min.wav"),
    )
    parser.add_argument("--rate", type=int, default=145)
    parser.add_argument("--silence", type=float, default=0.45)
    parser.add_argument(
        "--preview-output",
        type=Path,
        default=Path("data/demo_meeting.wav"),
    )
    parser.add_argument(
        "--preview-transcript",
        type=Path,
        default=Path("data/demo_meeting_transcript.txt"),
    )
    parser.add_argument("--preview-rate", type=int, default=190)
    args = parser.parse_args()
    duration = build_audio(
        args.transcript,
        args.output,
        speech_rate=args.rate,
        silence_seconds=args.silence,
    )
    print(f"Wrote {args.output} ({duration:.1f} seconds, {duration / 60:.2f} minutes)")
    if duration < 600:
        raise SystemExit("Generated audio is under 10 minutes; lower --rate and rebuild.")
    preview_duration = build_audio(
        args.preview_transcript,
        args.preview_output,
        speech_rate=args.preview_rate,
        silence_seconds=0.25,
    )
    print(f"Wrote {args.preview_output} ({preview_duration:.1f} seconds preview)")


if __name__ == "__main__":
    main()
