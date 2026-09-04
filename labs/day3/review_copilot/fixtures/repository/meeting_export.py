"""Safe base revision used as repository context for a synthetic PR diff."""


def validate_payload(payload: dict) -> None:
    if "request_id" not in payload: raise ValueError("REQUEST_ID_REQUIRED")

def prepare_minutes(action: str, payload: dict) -> dict:
    validate_payload(payload)
    return {"status": "DRAFT", "action": action, "payload": payload}
