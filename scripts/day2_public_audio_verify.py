#!/usr/bin/env python3
"""Verify the Day 2 public-audio catalog, checksums, and optional live source."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import day2_public_audio as audio


def verify_hashes() -> list[dict[str, str]]:
    if not audio.HASH_PATH.is_file():
        raise audio.PublicAudioError("SHA256_MANIFEST_NOT_FOUND")
    results: list[dict[str, str]] = []
    for line_number, line in enumerate(
        audio.HASH_PATH.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise audio.PublicAudioError(f"SHA256_MANIFEST_INVALID: line={line_number}")
        expected, relative = parts
        path = audio._repo_path(relative.strip())
        if not path.is_file():
            raise audio.PublicAudioError(f"CHECKSUM_TARGET_MISSING: {relative.strip()}")
        observed = audio.sha256_file(path)
        if observed != expected:
            raise audio.PublicAudioError(f"CHECKSUM_MISMATCH: {relative.strip()}")
        results.append({"path": relative.strip(), "status": "MATCH"})
    if not results:
        raise audio.PublicAudioError("SHA256_MANIFEST_EMPTY")
    return results


def verify_catalog_paths(catalog: dict, source: dict) -> dict[str, str]:
    fallback = audio._repo_path(catalog["fallback_audio"])
    output = audio._repo_path(source["excerpt"]["output"])
    expected_parent = (audio.REPO_ROOT / "data" / "day2_public_audio").resolve()
    if output.parent != expected_parent:
        raise audio.PublicAudioError("EXCERPT_OUTPUT_DIRECTORY_INVALID")
    if not fallback.is_file():
        raise audio.PublicAudioError("FALLBACK_AUDIO_NOT_FOUND")
    return {
        "fallback": fallback.relative_to(audio.REPO_ROOT).as_posix(),
        "excerpt": output.relative_to(audio.REPO_ROOT).as_posix(),
        "excerpt_status": "AVAILABLE" if output.is_file() else "NOT_BUILT",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="also query Wikimedia Commons and revalidate license, author, SHA-1, and size",
    )
    parser.add_argument("--source", help="source id from sources.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        catalog = audio.load_catalog()
        source = audio.select_source(catalog, args.source)
        result = {
            "status": "VERIFIED",
            "mode": "LIVE" if args.live else "OFFLINE",
            "paths": verify_catalog_paths(catalog, source),
            "checksums": verify_hashes(),
            "resolved": audio.resolve(catalog, source),
            "source": (
                audio.validate_source(source, audio.commons_imageinfo(source))
                if args.live
                else {"status": "SKIPPED_OFFLINE"}
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except audio.PublicAudioError as exc:
        print(json.dumps({"status": "EXPECTED_FAILURE", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
