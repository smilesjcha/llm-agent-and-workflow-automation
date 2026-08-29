"""Three-source meeting workflow with grounded output and explicit approval gates."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .audio import AudioValidationError, inspect_audio
from .ingestion import InputError, decode_transcript, parse_participants, parse_transcript, validate_context
from .models import (
    EmailDraft,
    EvidenceReference,
    IntegrationPlanItem,
    MeetingRecord,
    OutputKind,
    Participant,
    PipelineResult,
    TranscriptSegment,
)
from .providers import ProviderError, summarize
from .stt import STTError, fixture_transcribe, live_transcribe, quality_errors


ALL_OUTPUTS: list[OutputKind] = ["summary", "participant_perspectives", "todos", "insights"]
ALLOWED_PROVIDERS = {"fixture", "ollama", "codex", "claude", "openai"}
ALLOWED_EXECUTION_MODES = {"auto", "llm", "workflow", "agent"}
AGENT_CUES = (
    "notion",
    "confluence",
    "slack",
    "이메일",
    "메일",
    "외부",
    "최근 기록",
    "찾아",
    "연결",
    "저장",
    "발송",
)


def validate_evidence(record: MeetingRecord, segments: list[TranscriptSegment]) -> list[str]:
    known_ids = {segment.id for segment in segments}
    errors: list[str] = []
    grounded_summary = record.summary if hasattr(record.summary, "evidence_ids") else None
    groups: list[tuple[str, list]] = [
        ("SUMMARY", [grounded_summary] if grounded_summary else []),
        ("PERSPECTIVE", getattr(record, "participant_perspectives", [])),
        ("DECISION", record.decisions),
        ("ACTION", record.action_items),
        ("SHORT_INSIGHT", getattr(record, "short_term_insights", [])),
        ("MID_INSIGHT", getattr(record, "mid_term_insights", [])),
        ("LONG_INSIGHT", getattr(record, "long_term_insights", [])),
        ("QUESTION", record.open_questions),
    ]
    for group_name, items in groups:
        for index, item in enumerate(items, start=1):
            if not item.evidence_ids:
                errors.append(f"{group_name}_{index}_EVIDENCE_REQUIRED")
                continue
            unknown = sorted(set(item.evidence_ids) - known_ids)
            if unknown:
                errors.append(f"{group_name}_{index}_UNKNOWN_EVIDENCE:{','.join(unknown)}")
    return errors


def validate_requested_outputs(record: MeetingRecord, requested: list[OutputKind]) -> list[str]:
    errors: list[str] = []
    if "summary" in requested and record.summary is None:
        errors.append("SUMMARY_OUTPUT_MISSING")
    if "participant_perspectives" in requested and not record.participant_perspectives:
        errors.append("PERSPECTIVE_OUTPUT_MISSING")
    if "todos" in requested and not record.action_items:
        errors.append("TODO_OUTPUT_MISSING")
    if "insights" in requested and not (
        record.short_term_insights or record.mid_term_insights or record.long_term_insights
    ):
        errors.append("INSIGHT_OUTPUT_MISSING")
    return errors


def route_execution(
    requested_mode: str,
    *,
    source_mode: str,
    requested_outputs: list[OutputKind],
    domain_context: str,
    prior_context: str,
    adaptive_request: str,
) -> tuple[str, str, list[str]]:
    if requested_mode != "auto":
        used = requested_mode
        reason = {
            "llm": "한 번의 구조화 요청이면 충분하다고 사용자가 선택했습니다.",
            "workflow": "정해진 처리 단계를 같은 순서로 반복하도록 사용자가 선택했습니다.",
            "agent": "상황을 먼저 판단하고 필요한 다음 단계를 계획하도록 사용자가 선택했습니다.",
        }[used]
    else:
        normalized_request = adaptive_request.casefold()
        if adaptive_request and any(cue in normalized_request for cue in AGENT_CUES):
            used = "agent"
            reason = "외부 정보·도구·후속 전달 가능성이 있는 추가 요청이라 계획과 승인을 먼저 분리했습니다."
        elif requested_outputs == ["summary"] and not domain_context and not prior_context and source_mode != "audio":
            used = "llm"
            reason = "텍스트를 한 번 요약하는 단순 요청이라 한 번의 모델 호출로 정리합니다."
        else:
            used = "workflow"
            reason = "입력 변환, 여러 결과 생성, 근거 검사와 사람 확인을 같은 순서로 반복해야 합니다."

    common_tail = ["근거 번호 검사", "사람 검토 대기"]
    if used == "llm":
        steps = ["회의 입력 정리", "구조화 결과 생성", *common_tail]
    elif used == "workflow":
        steps = [
            "회의 입력 정리",
            "품질 확인",
            "업무 맥락 결합",
            "선택 결과 생성",
            "문서·메일 초안 구성",
            *common_tail,
        ]
    else:
        steps = [
            "요청 목적 판단",
            "필요한 정보와 연결 후보 계획",
            "허용된 회의 입력만 사용",
            "선택 결과 생성",
            "외부 작업 계획 분리",
            *common_tail,
        ]
    return used, reason, steps


def _hold(
    *,
    stage: str,
    code: str,
    source_mode: str,
    provider: str,
    execution_mode: str = "auto",
    requested_outputs: list[OutputKind] | None = None,
    source_filename: str | None = None,
    participants: list[Participant] | None = None,
    audio=None,
    segments=None,
    stt_mode_requested: str = "not_required",
    stt_mode_used: str | None = None,
    execution_mode_used: str | None = None,
    route_reason: str | None = None,
    workflow_steps: list[str] | None = None,
    model_requested: str | None = None,
) -> PipelineResult:
    safe_source = source_mode if source_mode in {"google_meet", "clova_note", "audio"} else "google_meet"
    safe_provider = provider if provider in ALLOWED_PROVIDERS else "fixture"
    safe_execution = execution_mode if execution_mode in ALLOWED_EXECUTION_MODES else "auto"
    safe_stt = stt_mode_requested if stt_mode_requested in {"not_required", "fixture", "live"} else "not_required"
    return PipelineResult(
        status="HOLD",
        stage=stage,
        error_codes=[code],
        source_mode=safe_source,
        source_filename=source_filename,
        participants=participants or [],
        requested_outputs=requested_outputs or [],
        execution_mode_requested=safe_execution,
        execution_mode_used=execution_mode_used,
        route_reason=route_reason,
        workflow_steps=workflow_steps or [],
        stt_mode_requested=safe_stt,
        stt_mode_used=stt_mode_used,
        provider_requested=safe_provider,
        model_requested=model_requested,
        audio=audio,
        segments=segments or [],
    )


def _all_items(record: MeetingRecord) -> list:
    return [
        *([record.summary] if record.summary else []),
        *record.participant_perspectives,
        *record.decisions,
        *record.action_items,
        *record.short_term_insights,
        *record.mid_term_insights,
        *record.long_term_insights,
        *record.open_questions,
    ]


def _evidence_index(record: MeetingRecord, segments: list[TranscriptSegment]) -> list[EvidenceReference]:
    referenced = {evidence_id for item in _all_items(record) for evidence_id in item.evidence_ids}
    return [
        EvidenceReference(segment_id=segment.id, speaker=segment.speaker, text=segment.text)
        for segment in segments
        if segment.id in referenced
    ]


def _md_item(item) -> str:
    return f"- {item.text}  _(근거: {', '.join(item.evidence_ids)})_"


def render_markdown(record: MeetingRecord, *, source_mode: str) -> str:
    source_label = {
        "google_meet": "Google Meet 또는 일반 전사",
        "clova_note": "ClovaNote 전사",
        "audio": "회의 음성",
    }[source_mode]
    lines = [f"# {record.title}", "", f"> 입력: {source_label} · 사람 검토 전 초안", ""]
    if record.summary:
        lines.extend(["## 회의 요약", "", record.summary.text, f"근거: {', '.join(record.summary.evidence_ids)}", ""])
    groups = [
        ("참석자별 관점", record.participant_perspectives),
        ("결정 사항", record.decisions),
        ("할 일", record.action_items),
        ("단기 인사이트", record.short_term_insights),
        ("중기 인사이트", record.mid_term_insights),
        ("장기 인사이트", record.long_term_insights),
        ("확인할 질문", record.open_questions),
    ]
    for title, items in groups:
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for item in items:
            prefix = f"**{item.participant}** · " if hasattr(item, "participant") else ""
            suffix = ""
            if hasattr(item, "assignee"):
                suffix = f" / 담당: {item.assignee} / 기한: {item.due_date or '확인 필요'}"
            lines.append(f"- {prefix}{item.text}{suffix}  _(근거: {', '.join(item.evidence_ids)})_")
        lines.append("")
    lines.extend(["---", "이 문서는 자동 저장·발송되지 않은 검토용 초안입니다."])
    return "\n".join(lines).strip()


def build_email_draft(record: MeetingRecord, participants: list[Participant]) -> EmailDraft:
    recipients = [participant.email for participant in participants if participant.email]
    body_lines = ["안녕하세요.", "", f"‘{record.title}’ 회의 기록 초안을 공유드립니다.", ""]
    if record.summary:
        body_lines.extend([record.summary.text, ""])
    if record.action_items:
        body_lines.append("[후속 할 일]")
        body_lines.extend(
            f"- {item.text} / 담당: {item.assignee} / 기한: {item.due_date or '확인 필요'}"
            for item in record.action_items
        )
        body_lines.append("")
    body_lines.extend(
        [
            "원문 근거와 담당자·기한을 확인한 뒤 발송해 주세요.",
            "",
            "감사합니다.",
        ]
    )
    return EmailDraft(
        recipients=recipients,
        subject=f"[검토 요청] {record.title}",
        body="\n".join(body_lines),
    )


def _integration_plan() -> list[IntegrationPlanItem]:
    return [
        IntegrationPlanItem(
            destination="notion",
            proposed_action="create_page",
            content_source="markdown_preview",
        ),
        IntegrationPlanItem(
            destination="confluence",
            proposed_action="create_page",
            content_source="markdown_preview",
        ),
        IntegrationPlanItem(
            destination="email",
            proposed_action="create_draft",
            content_source="email_draft",
        ),
    ]


def process_request(
    *,
    source_mode: str,
    source_filename: str,
    content_type: Optional[str],
    source_data: bytes,
    participants_raw: str = "",
    domain_context: str = "",
    prior_context: str = "",
    requested_outputs: list[str] | None = None,
    execution_mode: str = "auto",
    adaptive_request: str = "",
    provider: str = "fixture",
    model: str | None = None,
    allow_fixture_fallback: bool = True,
    legacy_stt_mode: str | None = None,
) -> PipelineResult:
    if source_mode not in {"google_meet", "clova_note", "audio"}:
        return _hold(stage="request", code="UNKNOWN_SOURCE_MODE", source_mode=source_mode, provider=provider)
    if provider not in ALLOWED_PROVIDERS:
        return _hold(stage="request", code="UNKNOWN_PROVIDER", source_mode=source_mode, provider=provider)
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        return _hold(
            stage="request",
            code="UNKNOWN_EXECUTION_MODE",
            source_mode=source_mode,
            provider=provider,
        )
    selected = requested_outputs or ALL_OUTPUTS.copy()
    if not selected or any(item not in ALL_OUTPUTS for item in selected) or len(selected) != len(set(selected)):
        return _hold(
            stage="request",
            code="REQUESTED_OUTPUTS_INVALID",
            source_mode=source_mode,
            provider=provider,
            execution_mode=execution_mode,
        )
    selected_typed: list[OutputKind] = list(selected)  # type: ignore[assignment]

    try:
        participants = parse_participants(participants_raw)
        domain_context = validate_context(domain_context, "domain_context")
        prior_context = validate_context(prior_context, "prior_context")
        adaptive_request = validate_context(adaptive_request, "adaptive_request")
    except InputError as exc:
        return _hold(
            stage="input_validation",
            code=exc.code,
            source_mode=source_mode,
            source_filename=Path(source_filename or "upload").name,
            provider=provider,
            execution_mode=execution_mode,
            requested_outputs=selected_typed,
            model_requested=model,
        )

    used_mode, route_reason, steps = route_execution(
        execution_mode,
        source_mode=source_mode,
        requested_outputs=selected_typed,
        domain_context=domain_context,
        prior_context=prior_context,
        adaptive_request=adaptive_request,
    )
    filename = Path(source_filename or ("meeting.txt" if source_mode != "audio" else "meeting.wav")).name
    warnings: list[str] = []
    audio = None
    stt_mode_requested = "not_required"
    stt_mode_used: str | None = f"not_required:{source_mode}_txt" if source_mode != "audio" else None
    try:
        if source_mode in {"google_meet", "clova_note"}:
            transcript = decode_transcript(source_data)
            segments = parse_transcript(transcript, source=source_mode, participants=participants)
            if not participants:
                warnings.append("PARTICIPANTS_INFERRED_FROM_TRANSCRIPT")
        else:
            audio = inspect_audio(filename=filename, content_type=content_type, data=source_data)
            stt_mode_requested = legacy_stt_mode or "live"
            if legacy_stt_mode == "fixture":
                segments = fixture_transcribe()
                stt_mode_used = "fixture"
                warnings.append("FIXTURE_TRANSCRIPT_UPLOAD_NOT_TRANSCRIBED")
            elif legacy_stt_mode not in {None, "live"}:
                raise STTError("UNKNOWN_STT_MODE")
            else:
                segments = live_transcribe(data=source_data, suffix=Path(audio.filename).suffix.lower())
                stt_mode_used = "live:faster-whisper"
                warnings.append("SPEAKER_LABELS_REQUIRE_REVIEW")
    except (AudioValidationError, InputError, STTError) as exc:
        code = exc.code
        stage = "audio_validation" if isinstance(exc, AudioValidationError) else "stt" if isinstance(exc, STTError) else "transcript_ingestion"
        return _hold(
            stage=stage,
            code=code,
            source_mode=source_mode,
            source_filename=filename,
            provider=provider,
            execution_mode=execution_mode,
            requested_outputs=selected_typed,
            participants=participants,
            audio=audio,
            stt_mode_requested=stt_mode_requested,
            stt_mode_used=stt_mode_used,
            execution_mode_used=used_mode,
            route_reason=route_reason,
            workflow_steps=steps,
            model_requested=model,
        )

    transcript_errors = quality_errors(segments)
    if transcript_errors:
        result = _hold(
            stage="transcript_quality_gate",
            code=transcript_errors[0],
            source_mode=source_mode,
            source_filename=filename,
            provider=provider,
            execution_mode=execution_mode,
            requested_outputs=selected_typed,
            participants=participants,
            audio=audio,
            segments=segments,
            stt_mode_requested=stt_mode_requested,
            stt_mode_used=stt_mode_used,
            execution_mode_used=used_mode,
            route_reason=route_reason,
            workflow_steps=steps,
            model_requested=model,
        )
        result.error_codes = transcript_errors
        result.warnings = warnings
        return result

    try:
        provider_result = summarize(
            provider=provider,
            segments=segments,
            allow_fixture_fallback=allow_fixture_fallback,
            participants=participants,
            requested_outputs=selected_typed,
            domain_context=domain_context,
            prior_context=prior_context,
            execution_mode=used_mode,
            adaptive_request=adaptive_request,
            model=model,
        )
    except ProviderError as exc:
        result = _hold(
            stage="meeting_record_generation",
            code=exc.code,
            source_mode=source_mode,
            source_filename=filename,
            provider=provider,
            execution_mode=execution_mode,
            requested_outputs=selected_typed,
            participants=participants,
            audio=audio,
            segments=segments,
            stt_mode_requested=stt_mode_requested,
            stt_mode_used=stt_mode_used,
            execution_mode_used=used_mode,
            route_reason=route_reason,
            workflow_steps=steps,
            model_requested=model,
        )
        result.warnings = warnings
        return result

    evidence_errors = [
        *validate_evidence(provider_result.record, segments),
        *validate_requested_outputs(provider_result.record, selected_typed),
    ]
    status = "HOLD" if evidence_errors else "READY"
    markdown_preview = render_markdown(provider_result.record, source_mode=source_mode) if status == "READY" else None
    email_draft = build_email_draft(provider_result.record, participants) if status == "READY" else None
    return PipelineResult(
        status=status,
        stage="human_review" if status == "READY" else "evidence_validation",
        error_codes=evidence_errors,
        warnings=[
            *warnings,
            *(["FIXTURE_FALLBACK_USED"] if provider_result.fallback_reason else []),
        ],
        source_mode=source_mode,
        source_filename=filename,
        participants=participants,
        requested_outputs=selected_typed,
        execution_mode_requested=execution_mode,
        execution_mode_used=used_mode,
        route_reason=route_reason,
        workflow_steps=steps,
        stt_mode_requested=stt_mode_requested,
        stt_mode_used=stt_mode_used,
        provider_requested=provider,
        provider_used=provider_result.provider_used,
        model_requested=provider_result.model_requested,
        model_used=provider_result.model_used,
        fallback_reason=provider_result.fallback_reason,
        audio=audio,
        segments=segments,
        meeting_record=provider_result.record,
        evidence=_evidence_index(provider_result.record, segments),
        evidence_errors=evidence_errors,
        markdown_preview=markdown_preview,
        email_draft=email_draft,
        integration_plan=_integration_plan() if status == "READY" else [],
    )


def process_meeting(
    *,
    filename: str,
    content_type: Optional[str],
    data: bytes,
    stt_mode: str,
    provider: str,
    allow_fixture_fallback: bool = True,
) -> PipelineResult:
    """Compatibility wrapper for the original audio-only Day 2 lab."""

    return process_request(
        source_mode="audio",
        source_filename=filename,
        content_type=content_type,
        source_data=data,
        requested_outputs=ALL_OUTPUTS.copy(),
        execution_mode="workflow",
        provider=provider,
        allow_fixture_fallback=allow_fixture_fallback,
        legacy_stt_mode=stt_mode,
    )
