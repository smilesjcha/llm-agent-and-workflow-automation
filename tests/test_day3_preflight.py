"""Day 3 preflight contract tests."""

from __future__ import annotations

from scripts.run_day3_preflight import build_report


def test_day3_preflight_passes_required_offline_checks() -> None:
    report = build_report(full_suite=False)

    assert report["status"] == "PASS"
    assert all(report["required_files"].values())
    assert all(report["required_modules"].values())
    assert report["checks"]["day3_focused"]["status"] == "PASS"
    assert report["checks"]["localhost_smoke"]["status"] == "PASS"


def test_day3_preflight_never_reads_or_publishes_credentials() -> None:
    report = build_report(full_suite=False)

    assert report["secret_boundary"] == {
        "env_file_ignored": True,
        "env_values_read": False,
        "env_values_printed": False,
    }
    assert report["safety"] == {
        "network_call": False,
        "external_write": False,
        "automatic_push": False,
        "automatic_merge": False,
    }
