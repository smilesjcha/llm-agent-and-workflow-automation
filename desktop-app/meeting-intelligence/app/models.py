"""Stable public contracts for the meeting-record application."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


SourceMode = Literal["google_meet", "clova_note", "audio"]
ExecutionMode = Literal["auto", "llm", "workflow", "agent"]
OutputKind = Literal["summary", "participant_perspectives", "todos", "insights"]
ProviderName = Literal["fixture", "ollama", "codex", "claude", "openai"]


class AudioMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    content_type: Optional[str] = None
    size_bytes: int = Field(ge=1)
    format: str
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    sample_rate: Optional[int] = Field(default=None, ge=1)
    channels: Optional[int] = Field(default=None, ge=1)


class Participant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    role: Optional[str] = Field(default=None, max_length=100)
    team: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=200)


class TranscriptSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^s\d{3}$")
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    speaker: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def end_follows_start(self) -> "TranscriptSegment":
        if self.end < self.start:
            raise ValueError("SEGMENT_END_BEFORE_START")
        return self


class TranscriptEnvelope(BaseModel):
    """One normalized transcript source shared by all input adapters."""

    model_config = ConfigDict(extra="forbid")

    source_mode: SourceMode
    source_filename: str = Field(min_length=1, max_length=255)
    segments: list[TranscriptSegment] = Field(min_length=1)
    source_count: Literal[1] = 1


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=2)
    evidence_ids: list[str] = Field(min_length=1)


class ParticipantPerspective(EvidenceItem):
    participant: str = Field(min_length=1, max_length=80)


class ActionItem(EvidenceItem):
    assignee: str = Field(min_length=1, max_length=80)
    due_date: Optional[str] = Field(default=None, max_length=40)
    status: Literal["OPEN", "CONFIRM_REQUIRED"] = "OPEN"


class MeetingRecord(BaseModel):
    """Provider output. Every substantive statement points back to transcript IDs."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=120)
    summary: Optional[EvidenceItem] = None
    participant_perspectives: list[ParticipantPerspective] = Field(default_factory=list)
    decisions: list[EvidenceItem] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    short_term_insights: list[EvidenceItem] = Field(default_factory=list)
    mid_term_insights: list[EvidenceItem] = Field(default_factory=list)
    long_term_insights: list[EvidenceItem] = Field(default_factory=list)
    open_questions: list[EvidenceItem] = Field(default_factory=list)


class MeetingBrief(BaseModel):
    """Original Day 2 contract kept for existing notebooks and validator examples."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=10)
    decisions: list[EvidenceItem] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[EvidenceItem] = Field(default_factory=list)


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str = Field(pattern=r"^s\d{3}$")
    speaker: str
    text: str


class EmailDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipients: list[str] = Field(default_factory=list)
    subject: str
    body: str
    send_status: Literal["DRAFT_ONLY"] = "DRAFT_ONLY"


class IntegrationPlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination: Literal["notion", "confluence", "email"]
    proposed_action: Literal["create_page", "create_draft"]
    content_source: Literal["markdown_preview", "email_draft"]
    approval_required: Literal[True] = True
    status: Literal["PLAN_ONLY"] = "PLAN_ONLY"


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["READY", "HOLD"]
    stage: str
    error_codes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    source_mode: SourceMode
    source_filename: Optional[str] = None
    participants: list[Participant] = Field(default_factory=list)
    requested_outputs: list[OutputKind] = Field(default_factory=list)
    execution_mode_requested: ExecutionMode
    execution_mode_used: Optional[Literal["llm", "workflow", "agent"]] = None
    route_reason: Optional[str] = None
    workflow_steps: list[str] = Field(default_factory=list)

    # Legacy STT fields remain so prior notebooks and tests keep a stable contract.
    stt_mode_requested: Literal["not_required", "fixture", "live"]
    stt_mode_used: Optional[str] = None
    provider_requested: ProviderName
    provider_used: Optional[str] = None
    model_requested: Optional[str] = None
    model_used: Optional[str] = None
    fallback_reason: Optional[str] = None

    audio: Optional[AudioMetadata] = None
    segments: list[TranscriptSegment] = Field(default_factory=list)
    meeting_record: Optional[MeetingRecord] = None
    evidence: list[EvidenceReference] = Field(default_factory=list)
    evidence_errors: list[str] = Field(default_factory=list)
    markdown_preview: Optional[str] = None
    email_draft: Optional[EmailDraft] = None
    integration_plan: list[IntegrationPlanItem] = Field(default_factory=list)
    human_review_required: bool = True
    external_write: bool = False

    @property
    def brief(self) -> Optional[MeetingRecord]:
        """Compatibility accessor for existing Python callers."""

        return self.meeting_record

    @model_validator(mode="after")
    def enforce_safety_contract(self) -> "PipelineResult":
        if self.status == "HOLD" and not self.error_codes:
            raise ValueError("HOLD_REQUIRES_ERROR_CODE")
        if self.external_write:
            raise ValueError("EXTERNAL_WRITE_MUST_BE_FALSE")
        if not self.human_review_required:
            raise ValueError("HUMAN_REVIEW_MUST_BE_REQUIRED")
        if any(not item.approval_required or item.status != "PLAN_ONLY" for item in self.integration_plan):
            raise ValueError("INTEGRATION_PLAN_MUST_REQUIRE_APPROVAL")
        return self

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        """Expose the old `brief` key without making it a second source of truth."""

        value = super().model_dump(*args, **kwargs)
        value["brief"] = value.get("meeting_record")
        return value
