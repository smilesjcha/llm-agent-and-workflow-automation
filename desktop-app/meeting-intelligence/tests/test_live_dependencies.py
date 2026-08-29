def test_live_stt_runtime_dependencies_import() -> None:
    import av  # noqa: F401
    import faster_whisper  # noqa: F401
    import requests  # noqa: F401
