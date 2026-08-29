#!/usr/bin/env python3
"""Build or resolve the licensed Korean meeting audio used in the Day 2 lab.

The public source is validated through the Wikimedia Commons API before ffmpeg
is allowed to create an excerpt. The large source video is never saved in the
repository. When the excerpt has not been built, ``resolve`` returns the
repository's synthetic, non-identifying meeting sample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "day2_public_audio"
CATALOG_PATH = DATA_DIR / "sources.json"
HASH_PATH = DATA_DIR / "SHA256SUMS"
USER_AGENT = "IPA-Day2-public-audio/1.0 (educational reproducibility)"


class PublicAudioError(RuntimeError):
    """Stable, expected failure for source, policy, or local-tool problems."""


def _under_repo(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise PublicAudioError(f"WORKSPACE_PATH_BLOCKED: {path}") from exc
    return resolved


def _repo_path(relative_path: str) -> Path:
    candidate = _under_repo(REPO_ROOT / relative_path)
    if candidate == REPO_ROOT:
        raise PublicAudioError("WORKSPACE_PATH_BLOCKED: repository root is not a file")
    return candidate


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    if catalog.get("schema_version") != "1.0":
        raise PublicAudioError("CATALOG_SCHEMA_UNSUPPORTED")
    if not catalog.get("sources"):
        raise PublicAudioError("CATALOG_SOURCE_MISSING")
    return catalog


def select_source(catalog: dict[str, Any], source_id: str | None) -> dict[str, Any]:
    wanted = source_id or catalog["default_source_id"]
    for source in catalog["sources"]:
        if source.get("id") == wanted:
            if source.get("status") != "enabled":
                raise PublicAudioError(f"SOURCE_DISABLED: {wanted}")
            return source
    raise PublicAudioError(f"SOURCE_UNKNOWN: {wanted}")


def commons_imageinfo(source: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
    params = {
        "action": "query",
        "format": "json",
        "prop": "videoinfo",
        "viprop": "url|size|sha1|mime|extmetadata|derivatives",
        "titles": source["mediawiki_title"],
    }
    api_url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except Exception as exc:
        raise PublicAudioError(f"SOURCE_METADATA_UNAVAILABLE: {type(exc).__name__}") from exc

    pages = payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    imageinfo = page.get("videoinfo", [])
    if not imageinfo:
        raise PublicAudioError("SOURCE_MEDIA_NOT_FOUND")
    return imageinfo[0]


def validate_source(source: dict[str, Any], imageinfo: dict[str, Any]) -> dict[str, Any]:
    expected = source["expected_original"]
    metadata = imageinfo.get("extmetadata", {})

    derivatives = imageinfo.get("derivatives", [])
    preferred_transcodekey = source["excerpt"]["preferred_transcodekey"]
    teaching_derivative = next(
        (
            item
            for item in derivatives
            if item.get("transcodekey") == preferred_transcodekey
            and str(item.get("src", "")).startswith("https://upload.wikimedia.org/")
        ),
        None,
    )
    observed = {
        "mime": imageinfo.get("mime"),
        "bytes": imageinfo.get("size"),
        "sha1": imageinfo.get("sha1"),
        "duration_seconds": imageinfo.get("duration"),
        "license": metadata.get("License", {}).get("value"),
        "license_url": metadata.get("LicenseUrl", {}).get("value"),
        "attribution": metadata.get("Attribution", {}).get("value"),
        "original_media_url": imageinfo.get("url"),
        "media_url": teaching_derivative.get("src") if teaching_derivative else None,
    }
    checks = {
        "mime": observed["mime"] == expected["mime"],
        "bytes": observed["bytes"] == expected["bytes"],
        "sha1": observed["sha1"] == expected["sha1"],
        "duration": abs(float(observed["duration_seconds"] or 0) - expected["duration_seconds"])
        < 0.01,
        "license": observed["license"] == "cc-by-4.0",
        "license_url": str(observed["license_url"] or "").rstrip("/")
        == source["license"]["url"].rstrip("/"),
        "attribution": observed["attribution"] == source["author"],
        "https_original": str(observed["original_media_url"] or "").startswith(
            "https://upload.wikimedia.org/"
        ),
        "https_teaching_derivative": str(observed["media_url"] or "").startswith(
            "https://upload.wikimedia.org/"
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise PublicAudioError("SOURCE_METADATA_MISMATCH: " + ",".join(failed))
    return {"status": "VERIFIED", "checks": checks, "observed": observed}


def ffmpeg_command(source: dict[str, Any], media_url: str, output: Path) -> list[str]:
    excerpt = source["excerpt"]
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        media_url,
        "-ss",
        str(excerpt["start_seconds"]),
        "-t",
        str(excerpt["duration_seconds"]),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        str(excerpt["channels"]),
        "-ar",
        str(excerpt["sample_rate_hz"]),
        "-c:a",
        excerpt["codec"],
        "-b:a",
        excerpt["bitrate"],
        "-metadata",
        f"title={source['title']} (교육용 10분 발췌)",
        "-metadata",
        f"artist={source['author']}",
        "-metadata",
        f"comment={source['attribution']}",
        "-f",
        "mp3",
        str(output),
    ]


def _duration_seconds(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise PublicAudioError("FFPROBE_NOT_FOUND")
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise PublicAudioError(f"FFPROBE_FAILED: exit_code={exc.returncode}") from exc
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise PublicAudioError("FFPROBE_DURATION_INVALID") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_hash_manifest(catalog: dict[str, Any]) -> None:
    tracked = [CATALOG_PATH, _repo_path(catalog["fallback_audio"])]
    for source in catalog["sources"]:
        output = _repo_path(source["excerpt"]["output"])
        if output.exists():
            tracked.append(output)
    lines = [
        f"{sha256_file(path)}  {path.relative_to(REPO_ROOT).as_posix()}" for path in tracked
    ]
    HASH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(source: dict[str, Any]) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PublicAudioError(
            "FFMPEG_NOT_FOUND: install ffmpeg, then rerun; use `resolve` for the fixture fallback"
        )

    verification = validate_source(source, commons_imageinfo(source))
    output = _repo_path(source["excerpt"]["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    command = ffmpeg_command(source, verification["observed"]["media_url"], temporary)
    command[0] = ffmpeg
    try:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            raise PublicAudioError(f"FFMPEG_EXCERPT_FAILED: exit_code={exc.returncode}") from exc
        duration = _duration_seconds(temporary)
        expected = float(source["excerpt"]["duration_seconds"])
        if abs(duration - expected) > 2.0:
            raise PublicAudioError(
                f"EXCERPT_DURATION_MISMATCH: expected={expected}, observed={duration:.3f}"
            )
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    catalog = load_catalog()
    write_hash_manifest(catalog)
    return {
        "status": "BUILT",
        "path": output.relative_to(REPO_ROOT).as_posix(),
        "duration_seconds": duration,
        "sha256": sha256_file(output),
        "attribution": source["attribution"],
    }


def resolve(catalog: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    excerpt = _repo_path(source["excerpt"]["output"])
    if excerpt.is_file():
        selected = excerpt
        reason = "CC_BY_EXCERPT_AVAILABLE"
        provenance = "public_cc_by_4_0"
    else:
        selected = _repo_path(catalog["fallback_audio"])
        if not selected.is_file():
            raise PublicAudioError("FALLBACK_AUDIO_NOT_FOUND")
        reason = "PUBLIC_EXCERPT_NOT_BUILT_USING_SYNTHETIC_FIXTURE"
        provenance = "synthetic_non_identifying_fixture"
    return {
        "status": "READY",
        "path": selected.relative_to(REPO_ROOT).as_posix(),
        "reason": reason,
        "provenance": provenance,
        "automatic_external_write": False,
    }


def dry_run(source: dict[str, Any]) -> dict[str, Any]:
    output = _repo_path(source["excerpt"]["output"])
    command = ffmpeg_command(source, "MEDIA_URL_FROM_VERIFIED_COMMONS_API", output)
    return {
        "status": "DRY_RUN",
        "source_id": source["id"],
        "license": source["license"]["spdx"],
        "output": output.relative_to(REPO_ROOT).as_posix(),
        "command": command,
        "network_called": False,
        "file_written": False,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("catalog", "dry-run", "verify-source", "build", "resolve"))
    parser.add_argument("--source", help="source id from sources.json")
    parser.add_argument("--path-only", action="store_true", help="with resolve, print only the path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        catalog = load_catalog()
        source = select_source(catalog, args.source)
        if args.action == "catalog":
            result: dict[str, Any] = {
                "default_source_id": catalog["default_source_id"],
                "sources": [
                    {
                        "id": item["id"],
                        "title": item["title"],
                        "license": item["license"]["spdx"],
                        "output": item["excerpt"]["output"],
                    }
                    for item in catalog["sources"]
                ],
                "fallback_audio": catalog["fallback_audio"],
            }
        elif args.action == "dry-run":
            result = dry_run(source)
        elif args.action == "verify-source":
            result = validate_source(source, commons_imageinfo(source))
        elif args.action == "build":
            result = build(source)
        else:
            result = resolve(catalog, source)

        if args.action == "resolve" and args.path_only:
            print(result["path"])
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except PublicAudioError as exc:
        print(json.dumps({"status": "EXPECTED_FAILURE", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
