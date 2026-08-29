from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from tests.test_pipeline import MP3_SAMPLE, wav_bytes


client = TestClient(app)
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_capabilities_treats_disabled_bridge_token_as_not_configured(monkeypatch) -> None:
    monkeypatch.setenv("HOST_BRIDGE_TOKEN", "disabled")

    response = client.get("/api/capabilities")

    assert response.status_code == 200
    assert response.json()["providers"]["host_bridge_configured"] is False


def test_process_endpoint_runs_fixture_pipeline() -> None:
    response = client.post(
        "/api/process",
        files={"audio": ("meeting.wav", wav_bytes(), "audio/wav")},
        data={"stt_mode": "fixture", "provider": "fixture", "allow_fixture_fallback": "true"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["external_write"] is False
    assert payload["human_review_required"] is True


def test_process_endpoint_rejects_unknown_provider_without_execution() -> None:
    response = client.post(
        "/api/process",
        files={"audio": ("meeting.wav", wav_bytes(), "audio/wav")},
        data={"stt_mode": "fixture", "provider": "shell"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "HOLD"
    assert payload["error_codes"] == ["UNKNOWN_PROVIDER"]


def test_mp3_api_result_has_metadata_and_fixture_disclosure() -> None:
    response = client.post(
        "/api/process",
        files={"audio": ("public-meeting.mp3", MP3_SAMPLE, "audio/mpeg")},
        data={"stt_mode": "fixture", "provider": "fixture"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["audio"]["duration_seconds"] > 0
    assert payload["audio"]["sample_rate"] == 8000
    assert payload["audio"]["channels"] == 1
    assert "FIXTURE_TRANSCRIPT_UPLOAD_NOT_TRANSCRIBED" in payload["warnings"]


def test_google_meet_api_runs_text_adapter_without_stt() -> None:
    response = client.post(
        "/api/process",
        files={
            "transcript_file": (
                "meet.txt",
                (FIXTURES / "google_meet_sample_ko.txt").read_bytes(),
                "text/plain",
            )
        },
        data={
            "source_mode": "google_meet",
            "participants": (FIXTURES / "participants_sample.json").read_text(encoding="utf-8"),
            "requested_outputs": "summary,participant_perspectives,todos,insights",
            "execution_mode": "auto",
            "provider": "fixture",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["source_mode"] == "google_meet"
    assert payload["stt_mode_requested"] == "not_required"
    assert payload["meeting_record"]["summary"]["evidence_ids"]
    assert payload["external_write"] is False
    assert all(item["status"] == "PLAN_ONLY" for item in payload["integration_plan"])


def test_sample_download_allowlist() -> None:
    ok = client.get("/api/samples/clova-note")
    missing = client.get("/api/samples/../../app/main.py")

    assert ok.status_code == 200
    assert "참석자 1" in ok.text
    assert missing.status_code == 404
