"""Day 2 multi-source Korean meeting-intelligence workflow.

The classroom default is deterministic, local, and side-effect free.  A source
is normalized into exactly one :class:`TranscriptEnvelope`; domain context is
kept separate from what people actually said; evidence IDs survive every
stage; and Markdown/e-mail are drafts until a person approves them.

Optional model and CLI integrations are explicit opt-ins.  They never read or
print credentials, and provider failure is represented with stable error
codes instead of being presented as a successful live call.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Callable, Literal, Mapping, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


SourceMode = Literal["google_meet_text", "clovanote_txt", "audio_stt"]
ReviewDecision = Literal["approve", "edit", "reject"]
ExecutionStrategy = Literal["single_llm", "deterministic_workflow", "agent_router"]
STTCallable = Callable[[Path], tuple[str, list[dict[str, Any]], dict[str, Any]]]

DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"
FIXED_MEETING_ACTIONS = frozenset(
    {"normalize", "transcribe", "summarize", "perspectives", "todos", "insights", "draft"}
)


class TranscriptSegment(BaseModel):
    """One evidence-addressable utterance."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^s\d{2,}$")
    speaker: str | None = None
    text: str = Field(min_length=1)
    start_seconds: float | None = Field(default=None, ge=0)
    quality_flags: list[str] = Field(default_factory=list)


class TranscriptEnvelope(BaseModel):
    """Common contract produced by all three input adapters."""

    model_config = ConfigDict(extra="forbid")

    source_mode: SourceMode
    source_ref: str = Field(min_length=1)
    segments: list[TranscriptSegment] = Field(min_length=1)
    speaker_metadata: dict[str, dict[str, str]] = Field(default_factory=dict)
    history_metadata: dict[str, Any] = Field(default_factory=dict)
    stt_metadata: dict[str, Any] | None = None
    source_count: Literal[1] = 1

    @model_validator(mode="after")
    def keep_stt_metadata_on_audio_only(self) -> "TranscriptEnvelope":
        if self.source_mode != "audio_stt" and self.stt_metadata is not None:
            raise ValueError("STT_METADATA_ONLY_FOR_AUDIO")
        if len({segment.id for segment in self.segments}) != len(self.segments):
            raise ValueError("DUPLICATE_EVIDENCE_ID")
        return self

    @property
    def transcript_text(self) -> str:
        lines: list[str] = []
        for segment in self.segments:
            speaker = segment.speaker or "화자미상"
            lines.append(f"[{segment.id}] {speaker}: {segment.text}")
        return "\n".join(lines)


class SourceInput(BaseModel):
    """Raw input contract that forbids mixed Meet, ClovaNote, and audio data."""

    model_config = ConfigDict(extra="forbid")

    source_mode: SourceMode
    source_ref: str = Field(min_length=1)
    meet_transcript: str | None = None
    clovanote_text: str | None = None
    audio_path: str | None = None
    speaker_metadata: dict[str, dict[str, str]] = Field(default_factory=dict)
    history_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def exactly_one_matching_source(self) -> "SourceInput":
        values = {
            "google_meet_text": self.meet_transcript,
            "clovanote_txt": self.clovanote_text,
            "audio_stt": self.audio_path,
        }
        populated = [name for name, value in values.items() if value is not None]
        if populated != [self.source_mode]:
            raise ValueError("SOURCE_MODE_MIXING_FORBIDDEN")
        selected = values[self.source_mode]
        if isinstance(selected, str) and not selected.strip():
            raise ValueError("SOURCE_INPUT_EMPTY")
        return self


class DomainContext(BaseModel):
    """Business context supplied by the user, never confused with transcript evidence."""

    model_config = ConfigDict(extra="forbid")

    industry: str = Field(min_length=1)
    organization_context: str = Field(min_length=1)
    meeting_objective: str = Field(min_length=1)
    glossary: dict[str, str] = Field(default_factory=dict)
    prior_decisions: list[str] = Field(default_factory=list)
    desired_outcomes: list[str] = Field(default_factory=list)
    confidentiality: Literal["public", "internal", "restricted"] = "internal"


class ParticipantPerspective(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participant: str = Field(min_length=1)
    perspective: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class TodoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    owner: str | None = None
    due_date: date | None = None
    evidence_ids: list[str] = Field(min_length=1)


class HorizonInsights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    short_term: list[str] = Field(min_length=1)
    medium_term: list[str] = Field(min_length=1)
    long_term: list[str] = Field(min_length=1)


class WellbeingRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: str = Field(min_length=1)
    risk: str = Field(min_length=1)
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    mitigation: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class MeetingRecord(BaseModel):
    """Evidence-backed record shared by workflow, review, and export stages."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    previous_context: str = Field(min_length=1)
    meeting_summary: str = Field(min_length=1)
    summary_evidence_ids: list[str] = Field(min_length=1)
    participant_perspectives: list[ParticipantPerspective] = Field(min_length=1)
    todos: list[TodoItem] = Field(min_length=1)
    insights: HorizonInsights
    wellbeing_risks: list[WellbeingRisk] = Field(default_factory=list)
    evidence_segment_count: int = Field(ge=1)
    status: Literal["DRAFT", "APPROVED", "EDITED"] = "DRAFT"
    human_review_required: Literal[True] = True
    external_write: Literal[False] = False


class MCPRetrievalPolicy(BaseModel):
    """Read-only policy used to *plan* MCP retrieval; it does not call MCP."""

    model_config = ConfigDict(extra="forbid")

    allowed_connectors: list[Literal["notion", "confluence", "slack"]] = Field(
        default_factory=list
    )
    explicit_user_authorization: bool = False
    lookback_days: int = Field(default=14, ge=1, le=90)
    allowed_scopes: dict[str, list[str]] = Field(default_factory=dict)
    participant_match_required: bool = True
    private_message_collection: Literal[False] = False
    max_items_per_connector: int = Field(default=20, ge=1, le=100)


class WorkflowState(TypedDict, total=False):
    source_input: dict[str, Any]
    domain_context: dict[str, Any]
    review_decision: ReviewDecision
    review_edits: dict[str, Any]
    transcriber: STTCallable | None
    retrieval_policy: dict[str, Any] | None
    envelope: dict[str, Any]
    record: dict[str, Any]
    evidence_errors: list[str]
    review: dict[str, Any]
    exports: dict[str, Any]
    retrieval_plan: dict[str, Any]
    trace: list[dict[str, Any]]
    status: str
    external_write: bool


_TIMESTAMP_SPEAKER = re.compile(
    r"^(?:\[)?(?P<minute>\d{1,2}):(?P<second>\d{2})(?:\])?\s+"
    r"(?P<speaker>[^:：]{1,40})[:：]\s*(?P<text>.+)$"
)
_BRACKETED_TIMESTAMP_SPEAKER = re.compile(
    r"^\[(?P<minute>\d{1,2}):(?P<second>\d{2})\]\s*"
    r"(?P<speaker>[^:：]{1,40})[:：]\s*(?P<text>.+)$"
)
_SPEAKER_ONLY = re.compile(r"^(?P<speaker>[^:：]{1,40})[:：]\s*(?P<text>.+)$")
_DATE_ISO = re.compile(r"\b(?P<year>20\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b")
_DATE_KO = re.compile(r"(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일")
_ACTION_WORDS = (
    "제가 ",
    "저는 ",
    "제 일정",
    "담당은",
    "담당:",
    "부탁드립니다",
    "해주세요",
    "할게요",
    "할게",
    "맡겠습니다",
    "올리겠습니다",
    "작성하겠습니다",
    "공유하겠습니다",
    "준비하겠습니다",
    "정리하겠습니다",
    "만들겠습니다",
)
_DECISION_WORDS = ("결정", "합의", "확정", "우선", "1차", "보류", "진행")
_WELLBEING_WORDS = ("야근", "번아웃", "과부하", "부담", "휴식", "지쳤", "병목")


def _seconds(minute: str | None, second: str | None) -> float | None:
    if minute is None or second is None:
        return None
    return int(minute) * 60 + int(second)


def _parse_text_segments(
    text: str,
    *,
    speaker_metadata: Mapping[str, Mapping[str, str]] | None = None,
) -> list[TranscriptSegment]:
    """Parse common Meet/Clova line formats without inventing speaker identity."""

    speaker_metadata = speaker_metadata or {}
    segments: list[TranscriptSegment] = []
    pending_speaker: str | None = None
    pending_start: float | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^\[s\d+\]\s*", "", line)
        match = _BRACKETED_TIMESTAMP_SPEAKER.match(line) or _TIMESTAMP_SPEAKER.match(line)
        if match:
            raw_speaker = match.group("speaker").strip()
            body = match.group("text").strip()
            start = _seconds(match.group("minute"), match.group("second"))
            pending_speaker = None
            pending_start = None
        else:
            clova_header = re.match(
                r"^(?P<speaker>화자\s*\d+|[^\s]{2,20})\s+(?P<minute>\d{1,2}):(?P<second>\d{2})$",
                line,
            )
            if clova_header:
                pending_speaker = clova_header.group("speaker").strip()
                pending_start = _seconds(
                    clova_header.group("minute"), clova_header.group("second")
                )
                continue
            speaker_only = _SPEAKER_ONLY.match(line)
            if speaker_only:
                raw_speaker = speaker_only.group("speaker").strip()
                body = speaker_only.group("text").strip()
                start = pending_start
                pending_speaker = None
                pending_start = None
            else:
                raw_speaker = pending_speaker
                body = line
                start = pending_start
                pending_speaker = None
                pending_start = None
        if not body:
            continue
        metadata = speaker_metadata.get(raw_speaker or "", {})
        speaker = metadata.get("display_name") or raw_speaker
        segments.append(
            TranscriptSegment(
                id=f"s{len(segments) + 1:02d}",
                speaker=speaker,
                text=body,
                start_seconds=start,
            )
        )
    if not segments:
        raise ValueError("EMPTY_TRANSCRIPT")
    return segments


def adapt_google_meet(source: SourceInput) -> TranscriptEnvelope:
    """Normalize a Google Meet transcript plus optional speaker/history metadata."""

    if source.source_mode != "google_meet_text":
        raise ValueError("ADAPTER_SOURCE_MODE_MISMATCH")
    assert source.meet_transcript is not None
    return TranscriptEnvelope(
        source_mode=source.source_mode,
        source_ref=source.source_ref,
        segments=_parse_text_segments(
            source.meet_transcript, speaker_metadata=source.speaker_metadata
        ),
        speaker_metadata=source.speaker_metadata,
        history_metadata=source.history_metadata,
    )


def adapt_clovanote(source: SourceInput) -> TranscriptEnvelope:
    """Normalize a ClovaNote text export while preserving anonymous speaker labels."""

    if source.source_mode != "clovanote_txt":
        raise ValueError("ADAPTER_SOURCE_MODE_MISMATCH")
    assert source.clovanote_text is not None
    return TranscriptEnvelope(
        source_mode=source.source_mode,
        source_ref=source.source_ref,
        segments=_parse_text_segments(
            source.clovanote_text, speaker_metadata=source.speaker_metadata
        ),
        speaker_metadata=source.speaker_metadata,
        history_metadata=source.history_metadata,
    )


def adapt_audio_stt(
    source: SourceInput,
    *,
    transcriber: STTCallable | None,
) -> TranscriptEnvelope:
    """Run an injected local STT adapter; never substitute another transcript silently."""

    if source.source_mode != "audio_stt":
        raise ValueError("ADAPTER_SOURCE_MODE_MISMATCH")
    if transcriber is None:
        raise RuntimeError("STT_ADAPTER_REQUIRED")
    assert source.audio_path is not None
    audio_path = Path(source.audio_path).expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError("AUDIO_FILE_NOT_FOUND")
    transcript_text, raw_segments, stt_metadata = transcriber(audio_path)
    if raw_segments:
        segments = [
            TranscriptSegment(
                id=f"s{index:02d}",
                speaker=item.get("speaker"),
                text=str(item.get("text", "")).strip(),
                start_seconds=item.get("start_seconds", item.get("start")),
                quality_flags=list(item.get("quality_flags", [])),
            )
            for index, item in enumerate(raw_segments, start=1)
            if str(item.get("text", "")).strip()
        ]
    else:
        segments = _parse_text_segments(
            transcript_text, speaker_metadata=source.speaker_metadata
        )
    if not segments:
        raise RuntimeError("STT_EMPTY_TRANSCRIPT")
    metadata = {
        **stt_metadata,
        "audio_path": str(audio_path),
        "fallback_transcript_substituted": False,
    }
    return TranscriptEnvelope(
        source_mode=source.source_mode,
        source_ref=source.source_ref,
        segments=segments,
        speaker_metadata=source.speaker_metadata,
        history_metadata=source.history_metadata,
        stt_metadata=metadata,
    )


def normalize_source(
    source: SourceInput,
    *,
    transcriber: STTCallable | None = None,
) -> TranscriptEnvelope:
    """Dispatch exactly one validated source to exactly one adapter."""

    if source.source_mode == "google_meet_text":
        return adapt_google_meet(source)
    if source.source_mode == "clovanote_txt":
        return adapt_clovanote(source)
    return adapt_audio_stt(source, transcriber=transcriber)


def _parse_due_date(text: str, *, reference_year: int = 2026) -> date | None:
    iso = _DATE_ISO.search(text)
    if iso:
        try:
            return date(int(iso.group("year")), int(iso.group("month")), int(iso.group("day")))
        except ValueError:
            return None
    korean = _DATE_KO.search(text)
    if korean:
        try:
            return date(reference_year, int(korean.group("month")), int(korean.group("day")))
        except ValueError:
            return None
    return None


def _action_owner(segment: TranscriptSegment) -> str | None:
    if segment.speaker and any(
        phrase in segment.text
        for phrase in ("제가 ", "저는 ", "제 일정", "할게", "맡겠습니다")
    ):
        return segment.speaker
    owner_match = re.search(
        r"(?P<owner>[가-힣A-Za-z][가-힣A-Za-z0-9_-]{1,9})(?:님(?:은|이|가)|\s+담당(?:은|:))",
        segment.text,
    )
    return owner_match.group("owner") if owner_match else None


def _compact_sentence(text: str, limit: int = 180) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 1]}…"


def structure_meeting_record(
    envelope: TranscriptEnvelope,
    domain: DomainContext,
) -> MeetingRecord:
    """Build a deterministic baseline record before any optional LLM enrichment."""

    by_speaker: dict[str, list[TranscriptSegment]] = defaultdict(list)
    for segment in envelope.segments:
        by_speaker[segment.speaker or "화자미상"].append(segment)

    perspectives = [
        ParticipantPerspective(
            participant=speaker,
            perspective=_compact_sentence(" ".join(item.text for item in items[-2:])),
            evidence_ids=[item.id for item in items[-3:]],
        )
        for speaker, items in by_speaker.items()
    ]

    todos: list[TodoItem] = []
    for segment in envelope.segments:
        due_date = _parse_due_date(segment.text)
        is_multi_owner_assignment = segment.text.count("님은") >= 2
        if not is_multi_owner_assignment and (
            due_date is not None or any(word in segment.text for word in _ACTION_WORDS)
        ):
            todos.append(
                TodoItem(
                    task=_compact_sentence(segment.text),
                    owner=_action_owner(segment),
                    due_date=due_date,
                    evidence_ids=[segment.id],
                )
            )
    if not todos:
        anchor = envelope.segments[-1]
        todos.append(
            TodoItem(
                task="후속 조치의 담당자와 기한 확정",
                owner=None,
                due_date=None,
                evidence_ids=[anchor.id],
            )
        )

    decision_segments = [
        segment
        for segment in envelope.segments
        if any(word in segment.text for word in _DECISION_WORDS)
    ]
    summary_basis = decision_segments[:3] or envelope.segments[:3]
    summary = _compact_sentence(" ".join(segment.text for segment in summary_basis), 360)

    risks: list[WellbeingRisk] = []
    for segment in envelope.segments:
        if any(word in segment.text for word in _WELLBEING_WORDS):
            severity: Literal["LOW", "MEDIUM", "HIGH"] = (
                "HIGH" if any(word in segment.text for word in ("번아웃", "과부하")) else "MEDIUM"
            )
            risks.append(
                WellbeingRisk(
                    signal=_compact_sentence(segment.text),
                    risk="업무 지속 가능성 저하 가능성",
                    severity=severity,
                    mitigation="담당 범위·기한을 다시 확인하고 필요한 경우 업무량을 조정",
                    evidence_ids=[segment.id],
                )
            )

    prior = domain.prior_decisions or list(
        envelope.history_metadata.get("prior_decisions", [])
    )
    previous_context = (
        "; ".join(str(item) for item in prior)
        if prior
        else domain.organization_context
    )
    first_outcome = (
        domain.desired_outcomes[0]
        if domain.desired_outcomes
        else "검토 가능한 회의 기록 초안"
    )
    return MeetingRecord(
        title=f"{domain.meeting_objective} 회의 기록",
        domain=domain.industry,
        purpose=domain.meeting_objective,
        previous_context=_compact_sentence(previous_context, 360),
        meeting_summary=summary,
        summary_evidence_ids=[segment.id for segment in summary_basis],
        participant_perspectives=perspectives,
        todos=todos,
        insights=HorizonInsights(
            short_term=[f"담당자·기한이 비어 있는 실행 항목을 먼저 확정하고 {first_outcome} 초안을 준비"],
            medium_term=["반복되는 회의 입력을 동일 계약으로 정규화하고 품질 기준을 수치화"],
            long_term=[f"{domain.industry} 맥락·근거·승인 이력을 조직 지식으로 축적"],
        ),
        wellbeing_risks=risks,
        evidence_segment_count=len(envelope.segments),
    )


def validate_record_evidence(
    record: MeetingRecord,
    envelope: TranscriptEnvelope,
) -> list[str]:
    """Verify every claim-bearing subrecord points to a real transcript segment."""

    known = {segment.id for segment in envelope.segments}
    errors: list[str] = []
    evidence_groups: list[tuple[str, list[str]]] = []
    evidence_groups.append(("SUMMARY", record.summary_evidence_ids))
    evidence_groups.extend(
        (f"PERSPECTIVE_{index}", item.evidence_ids)
        for index, item in enumerate(record.participant_perspectives, start=1)
    )
    evidence_groups.extend(
        (f"TODO_{index}", item.evidence_ids)
        for index, item in enumerate(record.todos, start=1)
    )
    evidence_groups.extend(
        (f"WELLBEING_{index}", item.evidence_ids)
        for index, item in enumerate(record.wellbeing_risks, start=1)
    )
    for label, evidence_ids in evidence_groups:
        if not evidence_ids:
            errors.append(f"{label}_EVIDENCE_REQUIRED")
            continue
        unknown = sorted(set(evidence_ids) - known)
        if unknown:
            errors.append(f"{label}_UNKNOWN_EVIDENCE:{','.join(unknown)}")
    return errors


def compare_execution_strategies() -> list[dict[str, Any]]:
    """Explain trade-offs as data that can be shown directly in the notebook."""

    return [
        {
            "strategy": "single_llm",
            "control_flow": "한 번의 구조화 요청",
            "best_for": "입력과 산출물이 단순한 일회성 작업",
            "llm_calls": "1",
            "strength": "가장 빠른 시작",
            "risk": "누락·형식 변동을 한 호출 안에서 발견하기 어려움",
        },
        {
            "strategy": "deterministic_workflow",
            "control_flow": "고정 노드와 검증 규칙",
            "best_for": "STT→요약→근거→승인처럼 순서가 정해진 반복 업무",
            "llm_calls": "0~필요한 노드 수",
            "strength": "비용·오류 위치·재실행 범위 예측 가능",
            "risk": "새 유즈케이스는 사람이 Workflow를 추가해야 함",
        },
        {
            "strategy": "agent_router",
            "control_flow": "요청·정책을 읽고 도구/Workflow 선택",
            "best_for": "Notion·Confluence·Slack 등 필요한 정보원이 요청마다 달라지는 작업",
            "llm_calls": "상황별 다수",
            "strength": "모호한 요청과 다양한 도구 조합에 대응",
            "risk": "비용·권한·잘못된 도구 선택 위험이 가장 큼",
        },
    ]


def route_execution_strategy(
    *,
    requested_actions: list[str],
    external_context_sources: list[str] | None = None,
    ambiguous_request: bool = False,
) -> dict[str, Any]:
    """Default rule router; it does not spend tokens deciding a known route."""

    external_context_sources = external_context_sources or []
    unknown_actions = sorted(set(requested_actions) - FIXED_MEETING_ACTIONS)
    if external_context_sources or ambiguous_request:
        strategy: ExecutionStrategy = "agent_router"
        reason = "VARIABLE_CONTEXT_OR_AMBIGUOUS_REQUEST"
    elif unknown_actions:
        strategy = "single_llm"
        reason = "ONE_OFF_UNMODELED_TRANSFORMATION"
    else:
        strategy = "deterministic_workflow"
        reason = "KNOWN_REPEATABLE_SEQUENCE"
    return {
        "strategy": strategy,
        "reason": reason,
        "requested_actions": requested_actions,
        "unknown_actions": unknown_actions,
        "external_context_sources": external_context_sources,
        "router_provider": "rule_based",
        "llm_router_call": False,
    }


def build_mcp_retrieval_plan(
    *,
    envelope: TranscriptEnvelope,
    domain: DomainContext,
    policy: MCPRetrievalPolicy | None,
) -> dict[str, Any]:
    """Create a simulated read-only MCP plan.  No connector is invoked here."""

    if policy is None or not policy.allowed_connectors:
        return {
            "status": "NOT_REQUESTED",
            "operations": [],
            "executed": False,
            "external_write": False,
        }
    missing_scopes = [
        connector
        for connector in policy.allowed_connectors
        if not policy.allowed_scopes.get(connector)
    ]
    if not policy.explicit_user_authorization or missing_scopes:
        reasons = []
        if not policy.explicit_user_authorization:
            reasons.append("EXPLICIT_USER_AUTHORIZATION_REQUIRED")
        if missing_scopes:
            reasons.append(f"ALLOWED_SCOPE_REQUIRED:{','.join(missing_scopes)}")
        return {
            "status": "POLICY_HOLD",
            "reasons": reasons,
            "operations": [],
            "executed": False,
            "external_write": False,
        }
    query_terms = [domain.meeting_objective, *domain.glossary.keys()]
    operations = []
    for connector in policy.allowed_connectors:
        operations.append(
            {
                "connector": connector,
                "operation": "search_read_only",
                "query_terms": query_terms,
                "lookback_days": policy.lookback_days,
                "allowed_scopes": policy.allowed_scopes.get(connector, []),
                "max_items": policy.max_items_per_connector,
                "participant_match_required": policy.participant_match_required,
                "private_message_collection": False,
            }
        )
    return {
        "status": "SIMULATED_POLICY_PLAN",
        "meeting_source_mode": envelope.source_mode,
        "operations": operations,
        "policy_checks": [
            "READ_ONLY_OPERATION",
            "SCOPE_ALLOWLIST_REQUIRED",
            "LOOKBACK_LIMIT_APPLIED",
            "PRIVATE_MESSAGES_EXCLUDED",
            "RETRIEVED_TEXT_REQUIRES_CITATION",
        ],
        "executed": False,
        "external_write": False,
    }


def _apply_review_edits(record: MeetingRecord, edits: Mapping[str, Any]) -> MeetingRecord:
    allowed_text_fields = {"title", "purpose", "previous_context", "meeting_summary"}
    unknown = set(edits) - allowed_text_fields - {"todo_updates"}
    if unknown:
        raise ValueError(f"UNSUPPORTED_REVIEW_EDIT:{','.join(sorted(unknown))}")
    payload = record.model_dump(mode="json")
    for field in allowed_text_fields:
        if field in edits:
            value = str(edits[field]).strip()
            if not value:
                raise ValueError(f"EMPTY_REVIEW_EDIT:{field}")
            payload[field] = value
    for index_text, update in dict(edits.get("todo_updates", {})).items():
        index = int(index_text)
        if index < 0 or index >= len(payload["todos"]):
            raise ValueError("TODO_EDIT_INDEX_OUT_OF_RANGE")
        if "owner" in update:
            payload["todos"][index]["owner"] = update["owner"] or None
        if "due_date" in update:
            payload["todos"][index]["due_date"] = update["due_date"] or None
    payload["status"] = "EDITED"
    return MeetingRecord.model_validate(payload)


def review_meeting_record(
    record: MeetingRecord,
    *,
    decision: ReviewDecision,
    edits: Mapping[str, Any] | None = None,
) -> tuple[MeetingRecord, dict[str, Any]]:
    """Apply an explicit human approve/edit/reject decision."""

    edits = edits or {}
    if decision == "reject":
        return record, {
            "decision": "reject",
            "status": "REJECTED",
            "export_ready": False,
            "human_reviewed": True,
            "external_write": False,
        }
    if decision == "edit":
        updated = _apply_review_edits(record, edits)
        return updated, {
            "decision": "edit",
            "status": "EDITED_READY_FOR_DRAFT",
            "export_ready": True,
            "human_reviewed": True,
            "external_write": False,
        }
    approved = record.model_copy(update={"status": "APPROVED"})
    return approved, {
        "decision": "approve",
        "status": "APPROVED_READY_FOR_DRAFT",
        "export_ready": True,
        "human_reviewed": True,
        "external_write": False,
    }


def render_markdown_draft(record: MeetingRecord) -> str:
    """Render a local Markdown draft with evidence IDs, not an external write."""

    lines = [
        f"# {record.title}",
        "",
        f"- 산업/도메인: {record.domain}",
        f"- 목적: {record.purpose}",
        f"- 상태: {record.status}",
        "",
        "## 이전 맥락",
        "",
        record.previous_context,
        "",
        "## 회의 요약",
        "",
        f"{record.meeting_summary} (근거 {', '.join(record.summary_evidence_ids)})",
        "",
        "## 참석자별 관점",
        "",
    ]
    for item in record.participant_perspectives:
        lines.append(
            f"- {item.participant}: {item.perspective} ({', '.join(item.evidence_ids)})"
        )
    lines.extend(["", "## To Do", ""])
    for item in record.todos:
        owner = item.owner or "미정"
        due = item.due_date.isoformat() if item.due_date else "미정"
        lines.append(
            f"- [ ] {item.task} · 담당 {owner} · 기한 {due} · 근거 {', '.join(item.evidence_ids)}"
        )
    lines.extend(["", "## 단기·중기·장기 인사이트", ""])
    for label, values in (
        ("단기", record.insights.short_term),
        ("중기", record.insights.medium_term),
        ("장기", record.insights.long_term),
    ):
        for value in values:
            lines.append(f"- {label}: {value}")
    lines.extend(["", "## Well-being 점검", ""])
    if record.wellbeing_risks:
        for risk in record.wellbeing_risks:
            lines.append(
                f"- {risk.severity}: {risk.risk} · {risk.mitigation} · 근거 {', '.join(risk.evidence_ids)}"
            )
    else:
        lines.append("- 명시적 위험 신호 없음 · 사람이 업무량과 일정 적정성을 최종 확인")
    lines.extend(["", "> 외부 문서 저장 전 사람 검토가 필요한 초안입니다.", ""])
    return "\n".join(lines)


def render_email_draft(
    record: MeetingRecord,
    *,
    audience: Literal["internal", "external"] = "internal",
) -> dict[str, Any]:
    """Build an unsent e-mail draft.  Recipient selection remains a human step."""

    greeting = "안녕하세요, 회의 참석자 여러분." if audience == "internal" else "안녕하세요."
    todo_lines = []
    for item in record.todos:
        owner = item.owner or "담당 미정"
        due = item.due_date.isoformat() if item.due_date else "기한 미정"
        todo_lines.append(f"- {item.task} / {owner} / {due}")
    body = "\n".join(
        [
            greeting,
            "",
            f"{record.purpose} 관련 회의 내용을 아래와 같이 정리했습니다.",
            "",
            record.meeting_summary,
            "",
            "[후속 조치]",
            *todo_lines,
            "",
            "담당자·기한·대외 공유 범위를 확인한 뒤 발송해 주세요.",
        ]
    )
    return {
        "subject": f"[회의 기록] {record.title}",
        "audience": audience,
        "to": [],
        "body": body,
        "send": False,
        "external_write": False,
        "human_recipient_check_required": True,
    }


def _event(state: WorkflowState, node: str, status: str, **details: Any) -> list[dict[str, Any]]:
    return [
        *state.get("trace", []),
        {"node": node, "status": status, "external_write": False, **details},
    ]


def _policy_node(state: WorkflowState) -> dict[str, Any]:
    source = SourceInput.model_validate(state["source_input"])
    return {
        "status": "POLICY_READY",
        "external_write": False,
        "trace": _event(
            state,
            "policy",
            "SUCCESS",
            source_mode=source.source_mode,
            source_count=1,
            human_review_required=True,
        ),
    }


def _normalize_node(state: WorkflowState) -> dict[str, Any]:
    source = SourceInput.model_validate(state["source_input"])
    if source.source_mode == "audio_stt":
        return {
            "trace": _event(
                state,
                "input_normalize",
                "SOURCE_CONTRACT_VALID",
                source_mode=source.source_mode,
                segment_count=None,
            )
        }
    envelope = normalize_source(source)
    return {
        "envelope": envelope.model_dump(mode="json"),
        "trace": _event(
            state,
            "input_normalize",
            "SUCCESS",
            source_mode=source.source_mode,
            segment_count=len(envelope.segments),
        ),
    }


def _stt_node(state: WorkflowState) -> dict[str, Any]:
    source = SourceInput.model_validate(state["source_input"])
    if source.source_mode != "audio_stt":
        return {"trace": _event(state, "stt_optional", "SKIPPED_TEXT_INPUT")}
    envelope = normalize_source(source, transcriber=state.get("transcriber"))
    return {
        "envelope": envelope.model_dump(mode="json"),
        "trace": _event(
            state,
            "stt_optional",
            "SUCCESS",
            provider=(envelope.stt_metadata or {}).get("provider", "injected_local_stt"),
            segment_count=len(envelope.segments),
        ),
    }


def _structure_node(state: WorkflowState) -> dict[str, Any]:
    envelope = TranscriptEnvelope.model_validate(state["envelope"])
    domain = DomainContext.model_validate(state["domain_context"])
    record = structure_meeting_record(envelope, domain)
    retrieval_policy = (
        MCPRetrievalPolicy.model_validate(state["retrieval_policy"])
        if state.get("retrieval_policy")
        else None
    )
    retrieval_plan = build_mcp_retrieval_plan(
        envelope=envelope, domain=domain, policy=retrieval_policy
    )
    return {
        "record": record.model_dump(mode="json"),
        "retrieval_plan": retrieval_plan,
        "trace": _event(
            state,
            "structure",
            "SUCCESS",
            participant_count=len(record.participant_perspectives),
            todo_count=len(record.todos),
        ),
    }


def _evidence_node(state: WorkflowState) -> dict[str, Any]:
    record = MeetingRecord.model_validate(state["record"])
    envelope = TranscriptEnvelope.model_validate(state["envelope"])
    errors = validate_record_evidence(record, envelope)
    return {
        "evidence_errors": errors,
        "trace": _event(
            state,
            "evidence",
            "HOLD" if errors else "SUCCESS",
            error_count=len(errors),
        ),
    }


def _review_node(state: WorkflowState) -> dict[str, Any]:
    errors = state.get("evidence_errors", [])
    if errors:
        review = {
            "decision": "reject",
            "status": "HOLD_EVIDENCE_ERROR",
            "export_ready": False,
            "human_reviewed": False,
            "external_write": False,
        }
        return {
            "review": review,
            "status": review["status"],
            "trace": _event(state, "human_review", "BLOCKED_BY_EVIDENCE"),
        }
    record = MeetingRecord.model_validate(state["record"])
    reviewed, review = review_meeting_record(
        record,
        decision=state["review_decision"],
        edits=state.get("review_edits", {}),
    )
    return {
        "record": reviewed.model_dump(mode="json"),
        "review": review,
        "status": review["status"],
        "trace": _event(
            state,
            "human_review",
            review["status"],
            decision=review["decision"],
        ),
    }


def _export_node(state: WorkflowState) -> dict[str, Any]:
    review = state["review"]
    if not review["export_ready"]:
        exports = {
            "status": "SKIPPED_NOT_APPROVED",
            "markdown": None,
            "email": None,
            "external_write": False,
        }
        return {
            "exports": exports,
            "trace": _event(state, "export_draft", "SKIPPED_NOT_APPROVED"),
        }
    record = MeetingRecord.model_validate(state["record"])
    exports = {
        "status": "DRAFT_READY",
        "markdown": render_markdown_draft(record),
        "email": render_email_draft(record),
        "external_write": False,
    }
    return {
        "exports": exports,
        "status": "DRAFT_READY",
        "trace": _event(state, "export_draft", "DRAFT_READY"),
    }


def build_meeting_graph():
    """Compile the actual LangGraph used by all three classroom scenarios."""

    builder = StateGraph(WorkflowState)
    builder.add_node("policy", _policy_node)
    builder.add_node("input_normalize", _normalize_node)
    builder.add_node("stt_optional", _stt_node)
    builder.add_node("structure", _structure_node)
    builder.add_node("evidence", _evidence_node)
    builder.add_node("human_review", _review_node)
    builder.add_node("export_draft", _export_node)
    builder.add_edge(START, "policy")
    builder.add_edge("policy", "input_normalize")
    builder.add_edge("input_normalize", "stt_optional")
    builder.add_edge("stt_optional", "structure")
    builder.add_edge("structure", "evidence")
    builder.add_edge("evidence", "human_review")
    builder.add_edge("human_review", "export_draft")
    builder.add_edge("export_draft", END)
    return builder.compile()


def run_meeting_workflow(
    source_input: SourceInput | Mapping[str, Any],
    domain_context: DomainContext | Mapping[str, Any],
    *,
    review_decision: ReviewDecision,
    review_edits: Mapping[str, Any] | None = None,
    transcriber: STTCallable | None = None,
    retrieval_policy: MCPRetrievalPolicy | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run policy→normalize→optional STT→structure→evidence→review→draft."""

    source = SourceInput.model_validate(source_input)
    domain = DomainContext.model_validate(domain_context)
    policy_payload = (
        MCPRetrievalPolicy.model_validate(retrieval_policy).model_dump(mode="json")
        if retrieval_policy is not None
        else None
    )
    result = build_meeting_graph().invoke(
        {
            "source_input": source.model_dump(mode="json"),
            "domain_context": domain.model_dump(mode="json"),
            "review_decision": review_decision,
            "review_edits": dict(review_edits or {}),
            "transcriber": transcriber,
            "retrieval_policy": policy_payload,
            "trace": [],
            "status": "CREATED",
            "external_write": False,
        }
    )
    # The callable is execution plumbing, not part of the serializable audit record.
    result.pop("transcriber", None)
    result["framework"] = "LangGraph"
    result["graph_nodes"] = [
        "policy",
        "input_normalize",
        "stt_optional",
        "structure",
        "evidence",
        "human_review",
        "export_draft",
    ]
    result["external_write"] = False
    return result


def _normalize_openai_error(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()
    class_name = type(exc).__name__.lower()
    if status == 404 or (
        "model" in message
        and any(token in message for token in ("not found", "does not exist", "access"))
    ):
        return "MODEL_NOT_AVAILABLE"
    if status in {401, 403} or "authentication" in class_name:
        return "AUTHENTICATION_FAILED"
    if status == 429 or "rate limit" in message:
        return "RATE_LIMITED"
    if "timeout" in class_name or "timed out" in message:
        return "REQUEST_TIMEOUT"
    return "OPENAI_REQUEST_FAILED"


def run_optional_openai_prompt(
    prompt: str,
    *,
    env: Mapping[str, str] | None = None,
    client: Any | None = None,
    model: str | None = None,
    allow_fixture_fallback: bool = True,
    fixture_text: str = "로컬 fixture: API를 호출하지 않은 구조 검증 결과",
) -> dict[str, Any]:
    """Optional Responses API adapter with an explicit live opt-in boundary."""

    environment = os.environ if env is None else env
    selected_model = model or environment.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    live_opt_in = environment.get("OPENAI_LIVE_OPT_IN", "0") == "1"
    key = environment.get("OPENAI_API_KEY")
    if not live_opt_in:
        error_code = "OPENAI_LIVE_OPT_IN_REQUIRED"
    elif not key and client is None:
        error_code = "OPENAI_API_KEY_MISSING"
    else:
        error_code = None

    if error_code is None:
        try:
            if client is None:
                try:
                    from openai import OpenAI  # type: ignore[import-not-found]
                except ImportError:
                    raise RuntimeError("OPENAI_SDK_NOT_INSTALLED") from None
                client = OpenAI(api_key=key)
            response = client.responses.create(model=selected_model, input=prompt)
            output_text = str(getattr(response, "output_text", "")).strip()
            if not output_text:
                raise RuntimeError("OPENAI_EMPTY_RESPONSE")
            return {
                "status": "SUCCESS",
                "provider_requested": "openai",
                "provider_used": "openai",
                "model": selected_model,
                "model_available": True,
                "live_attempted": True,
                "output_text": output_text,
                "fallback_reason": None,
                "api_key_value_exposed": False,
                "external_write": False,
            }
        except Exception as exc:
            if str(exc) == "OPENAI_SDK_NOT_INSTALLED":
                error_code = "OPENAI_SDK_NOT_INSTALLED"
            else:
                error_code = _normalize_openai_error(exc)

    model_available = False if error_code == "MODEL_NOT_AVAILABLE" else None
    if not allow_fixture_fallback:
        return {
            "status": "EXPECTED_FAILURE",
            "provider_requested": "openai",
            "provider_used": None,
            "model": selected_model,
            "model_available": model_available,
            "live_attempted": live_opt_in,
            "output_text": None,
            "error_code": error_code,
            "api_key_value_exposed": False,
            "external_write": False,
        }
    return {
        "status": "FALLBACK",
        "provider_requested": "openai",
        "provider_used": "fixture",
        "model": selected_model,
        "model_available": model_available,
        "live_attempted": live_opt_in,
        "output_text": fixture_text,
        "fallback_reason": error_code,
        "api_key_value_exposed": False,
        "external_write": False,
    }


def run_optional_openai_record(
    envelope: TranscriptEnvelope,
    domain: DomainContext,
    *,
    env: Mapping[str, str] | None = None,
    client: Any | None = None,
    model: str | None = None,
    allow_fixture_fallback: bool = True,
) -> dict[str, Any]:
    """Request one MeetingRecord, then revalidate it at the software boundary."""

    deterministic_fixture = structure_meeting_record(envelope, domain)
    prompt = "\n".join(
        [
            "당신은 한국어 회의 기록 구조화 모델입니다.",
            "아래 JSON Schema를 만족하는 JSON object만 반환하세요.",
            "원문에 없는 담당자·기한은 null이며 evidence ID를 새로 만들지 마세요.",
            "human_review_required는 true, external_write는 false입니다.",
            f"DOMAIN_CONTEXT={json.dumps(domain.model_dump(mode='json'), ensure_ascii=False)}",
            f"MEETING_RECORD_SCHEMA={json.dumps(MeetingRecord.model_json_schema(), ensure_ascii=False)}",
            f"TRANSCRIPT={envelope.transcript_text}",
        ]
    )
    provider_result = run_optional_openai_prompt(
        prompt,
        env=env,
        client=client,
        model=model,
        allow_fixture_fallback=allow_fixture_fallback,
        fixture_text=deterministic_fixture.model_dump_json(),
    )
    output_text = provider_result.get("output_text")
    if not output_text:
        return {
            **provider_result,
            "record": None,
            "schema_valid": False,
        }
    normalized = str(output_text).strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:json)?\s*|\s*```$", "", normalized, flags=re.I)
    try:
        record = MeetingRecord.model_validate_json(normalized)
        evidence_errors = validate_record_evidence(record, envelope)
        if evidence_errors:
            raise ValueError("OPENAI_EVIDENCE_INVALID")
    except (ValidationError, ValueError, json.JSONDecodeError):
        if not allow_fixture_fallback:
            return {
                **provider_result,
                "status": "EXPECTED_FAILURE",
                "provider_used": None,
                "record": None,
                "schema_valid": False,
                "error_code": "OPENAI_SCHEMA_INVALID",
            }
        return {
            **provider_result,
            "status": "FALLBACK",
            "provider_used": "fixture",
            "fallback_reason": "OPENAI_SCHEMA_INVALID",
            "record": deterministic_fixture.model_dump(mode="json"),
            "schema_valid": True,
        }
    return {
        **provider_result,
        "record": record.model_dump(mode="json"),
        "schema_valid": True,
        "evidence_errors": [],
    }


def diagnose_provider_options() -> dict[str, Any]:
    """Inspect executable availability only; no login, model, or API call is made."""

    definitions = {
        "ollama": {
            "command": "ollama",
            "opt_in_example": "ollama run qwen3:4b",
            "role": "로컬 LLM 선택 실습",
        },
        "codex": {
            "command": "codex",
            "opt_in_example": "codex exec --ephemeral --sandbox read-only '<요청>'",
            "role": "저장소 분석·코드 생성 Harness",
        },
        "claude_code": {
            "command": "claude",
            "opt_in_example": "claude -p --tools '' --no-session-persistence '<요청>'",
            "role": "대체 코딩 Agent Harness",
        },
    }
    options: dict[str, Any] = {}
    for name, definition in definitions.items():
        executable = shutil.which(definition["command"])
        options[name] = {
            **definition,
            "installed": executable is not None,
            "status": "INSTALLED_NOT_EXECUTED" if executable else "NOT_INSTALLED",
            "auth_checked": False,
            "command_executed": False,
            "credential_value_read": False,
            "external_write": False,
        }
    options["openai_api"] = {
        "default_model": DEFAULT_OPENAI_MODEL,
        "activation": "OPENAI_LIVE_OPT_IN=1 and OPENAI_API_KEY configured",
        "status": "ENV_OPT_IN_ONLY",
        "credential_value_read": False,
        "external_write": False,
    }
    return options


def run_optional_cli_prompt(
    provider: Literal["ollama", "codex", "claude_code"],
    prompt: str,
    *,
    live_opt_in: bool = False,
    model: str = "qwen3:4b",
    timeout_seconds: int = 90,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run a constrained optional CLI call without a shell or external writes.

    Codex is restricted to a read-only ephemeral sandbox and Claude Code has no
    tools.  The default path only returns the planned command; it never checks
    login state or starts a model.
    """

    definitions = {
        "ollama": ["ollama", "run", model, prompt],
        "codex": [
            "codex",
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            prompt,
        ],
        "claude_code": [
            "claude",
            "-p",
            "--tools",
            "",
            "--no-session-persistence",
            prompt,
        ],
    }
    args = definitions[provider]
    safe_plan = {
        "provider_requested": provider,
        "command": [*args[:-1], "<PROMPT>"],
        "shell": False,
        "external_write": False,
        "credential_value_read": False,
    }
    if not live_opt_in:
        return {
            **safe_plan,
            "status": "EXPECTED_SKIP",
            "error_code": "CLI_LIVE_OPT_IN_REQUIRED",
            "command_executed": False,
            "output_text": None,
        }
    executable = shutil.which(args[0])
    if executable is None and runner is None:
        return {
            **safe_plan,
            "status": "EXPECTED_FAILURE",
            "error_code": "CLI_NOT_INSTALLED",
            "command_executed": False,
            "output_text": None,
        }
    selected_runner = runner
    if selected_runner is None:
        selected_runner = subprocess.run
    try:
        completed = selected_runner(
            [executable or args[0], *args[1:]],
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (TimeoutError, subprocess.TimeoutExpired):
        return {
            **safe_plan,
            "status": "EXPECTED_FAILURE",
            "error_code": "CLI_TIMEOUT",
            "command_executed": True,
            "output_text": None,
        }
    if completed.returncode != 0:
        return {
            **safe_plan,
            "status": "EXPECTED_FAILURE",
            "error_code": "CLI_EXECUTION_FAILED",
            "command_executed": True,
            "output_text": None,
        }
    output_text = str(completed.stdout).strip()
    return {
        **safe_plan,
        "status": "SUCCESS",
        "error_code": None,
        "command_executed": True,
        "output_text": output_text,
    }


def source_mixing_error_example() -> dict[str, Any]:
    """Return a stable boundary example for the notebook without leaking validation internals."""

    try:
        SourceInput(
            source_mode="google_meet_text",
            source_ref="mixed-input",
            meet_transcript="민지: Meet 본문",
            clovanote_text="화자 1: Clova 본문",
        )
    except ValidationError:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "SOURCE_MODE_MIXING_FORBIDDEN",
            "external_write": False,
        }
    return {"status": "UNEXPECTED_SUCCESS", "external_write": False}


def compact_workflow_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-friendly projection for classroom scorecards."""

    envelope = TranscriptEnvelope.model_validate(result["envelope"])
    record = MeetingRecord.model_validate(result["record"])
    return {
        "status": result["status"],
        "source_mode": envelope.source_mode,
        "segment_count": len(envelope.segments),
        "purpose": record.purpose,
        "summary": record.meeting_summary,
        "participant_count": len(record.participant_perspectives),
        "todo_count": len(record.todos),
        "wellbeing_risk_count": len(record.wellbeing_risks),
        "review": result["review"],
        "trace": result["trace"],
        "retrieval_plan": result["retrieval_plan"],
        "external_write": False,
    }


def pretty_json(payload: Any) -> str:
    """Small helper used by the notebook and instructor console."""

    return json.dumps(payload, ensure_ascii=False, indent=2)
