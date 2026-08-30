"""FastAPI entrypoint for the local meeting-record application."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .audio import MAX_UPLOAD_BYTES
from .ingestion import MAX_TRANSCRIPT_BYTES
from .pipeline import ALL_OUTPUTS, process_request


ROOT = Path(__file__).resolve().parent.parent
APP_VERSION = "2.1.0"
app = FastAPI(title="나의 회의 기록 도우미", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.middleware("http")
async def local_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    )
    return response


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "meeting-intelligence",
        "version": APP_VERSION,
        "external_write": False,
    }


@app.get("/api/samples/{sample_name}", include_in_schema=False)
def sample_file(sample_name: str) -> FileResponse:
    allowed = {
        "google-meet": "google_meet_sample_ko.txt",
        "clova-note": "clova_note_sample_ko.txt",
        "participants": "participants_sample.json",
    }
    filename = allowed.get(sample_name)
    if filename is None:
        raise HTTPException(status_code=404, detail="SAMPLE_NOT_FOUND")
    return FileResponse(
        ROOT / "fixtures" / filename,
        filename=filename,
        media_type="application/json" if filename.endswith(".json") else "text/plain; charset=utf-8",
    )


@app.get("/api/capabilities")
def capabilities() -> dict:
    bridge_token = os.getenv("HOST_BRIDGE_TOKEN", "").strip()
    return {
        "runtime": {
            "delivery_mode": os.getenv("APP_DELIVERY_MODE", "source"),
            "local_url": os.getenv("APP_LOCAL_URL", "http://127.0.0.1:8766"),
            "fixture_ready": True,
        },
        "inputs": {
            "google_meet_txt": True,
            "clova_note_txt": True,
            "audio_live_stt": True,
            "live_stt_dependency_installed": importlib.util.find_spec("faster_whisper") is not None,
            "whisper_model": os.getenv("WHISPER_MODEL", "small"),
        },
        # Original keys remain for notebooks and health-check screenshots.
        "stt": {
            "fixture": True,
            "live_dependency_installed": importlib.util.find_spec("faster_whisper") is not None,
            "model": os.getenv("WHISPER_MODEL", "small"),
        },
        "providers": {
            "fixture": True,
            "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:4b"),
            "host_bridge_configured": bridge_token not in {"", "disabled"},
            "openai_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
            "openai_default_model": os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        },
        "privacy": {
            "credential_files_read": False,
            "browser_cookies_read": False,
            "source_persisted": False,
            "external_write": False,
            "human_review_required": True,
        },
    }


def _requested_outputs(raw: str) -> list[str]:
    cleaned = raw.strip()
    if not cleaned:
        return ALL_OUTPUTS.copy()
    if cleaned.startswith("["):
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError:
            return [cleaned]
        return value if isinstance(value, list) else [cleaned]
    return [item.strip() for item in cleaned.split(",") if item.strip()]


@app.post("/api/process")
async def process_source(
    source_mode: str = Form("audio"),
    transcript_file: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    participants: str = Form(""),
    domain_context: str = Form(""),
    prior_context: str = Form(""),
    requested_outputs: str = Form("summary,participant_perspectives,todos,insights"),
    execution_mode: str = Form("auto"),
    adaptive_request: str = Form(""),
    provider: str = Form("fixture"),
    model: str = Form(""),
    allow_fixture_fallback: bool = Form(True),
    # Compatibility input used only by the original audio lab; new UI omits it and always runs live STT.
    stt_mode: str | None = Form(None),
) -> dict:
    selected_file = audio if source_mode == "audio" else transcript_file
    limit = MAX_UPLOAD_BYTES if source_mode == "audio" else MAX_TRANSCRIPT_BYTES
    if selected_file is None:
        filename = "meeting.wav" if source_mode == "audio" else "meeting.txt"
        content_type = None
        data = b""
    else:
        filename = selected_file.filename or ("meeting.wav" if source_mode == "audio" else "meeting.txt")
        content_type = selected_file.content_type
        data = await selected_file.read(limit + 1)

    result = process_request(
        source_mode=source_mode,
        source_filename=filename,
        content_type=content_type,
        source_data=data,
        participants_raw=participants,
        domain_context=domain_context,
        prior_context=prior_context,
        requested_outputs=_requested_outputs(requested_outputs),
        execution_mode=execution_mode,
        adaptive_request=adaptive_request,
        provider=provider,
        model=model.strip() or None,
        allow_fixture_fallback=allow_fixture_fallback,
        legacy_stt_mode=stt_mode,
    )
    return result.model_dump(mode="json")
