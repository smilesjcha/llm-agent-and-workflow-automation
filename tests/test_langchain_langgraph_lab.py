from src.langchain_lab import normalize_provider_failure, run_langchain_lab
from src.langgraph_lab import run_langgraph_lab


TRANSCRIPT = "[00:01] 서연: 공개 FAQ를 정리하겠습니다.\n[00:05] 준호: 금요일까지 Schema를 작성하겠습니다."


def _draft() -> dict:
    return run_langchain_lab(TRANSCRIPT)["result"]


def test_langchain_lcel_returns_typed_policy_safe_result() -> None:
    result = run_langchain_lab(TRANSCRIPT)
    assert result["framework"] == "LangChain LCEL"
    assert result["checks"]["schema_valid"] is True
    assert result["checks"]["evidence_present"] is True
    assert result["result"]["automatic_email"] is False
    assert result["result"]["requires_human_approval"] is True
    assert len(normalize_provider_failure(ValueError("x" * 500))) <= 200


def test_langgraph_approve_interrupts_then_exports_locally() -> None:
    result = run_langgraph_lab(_draft(), decision="approve", request_id="test-approve")
    assert result["interrupted"] is True
    assert result["thread_id_reused"] is True
    assert result["final_state"]["status"] == "READY_FOR_EXPORT"
    assert result["final_state"]["automatic_email"] is False


def test_langgraph_edit_resumes_with_human_summary() -> None:
    edited = "사람이 수정한 요약"
    result = run_langgraph_lab(
        _draft(),
        decision="edit",
        request_id="test-edit",
        edited_summary=edited,
    )
    assert result["final_state"]["draft"]["summary"] == edited
    assert result["final_state"]["review"]["decision"] == "edit"
    assert result["final_state"]["export_ready"] is True


def test_langgraph_reject_never_exports_or_sends() -> None:
    result = run_langgraph_lab(_draft(), decision="reject", request_id="test-reject")
    assert result["final_state"]["status"] == "REJECTED"
    assert result["final_state"]["export_ready"] is False
    assert result["final_state"]["automatic_email"] is False
