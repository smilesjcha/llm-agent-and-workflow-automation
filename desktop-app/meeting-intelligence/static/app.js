const form = document.querySelector("#meeting-form");
const transcriptInput = document.querySelector("#transcript-file");
const audioInput = document.querySelector("#audio-file");
const runButton = document.querySelector("#run-button");
const emptyResult = document.querySelector("#empty-result");
const resultPanel = document.querySelector("#result");
const formError = document.querySelector("#form-error");
const providerSelect = document.querySelector("#provider");
let lastResult = null;
let loadedTranscriptSample = null;

const sourceLabels = {
  google_meet: "Google Meet 또는 전사 TXT",
  clova_note: "ClovaNote TXT",
  audio: "회의 녹음",
};
const modeLabels = {
  llm: "한 번에 정리 · LLM",
  workflow: "정해진 순서 · Workflow",
  agent: "상황 판단 · Agent",
};
const providerLabels = {
  fixture: "인터넷 없이 연습용 결과",
  ollama: "내 컴퓨터의 Ollama",
  codex: "로그인된 Codex 프로그램",
  claude: "로그인된 Claude Code 프로그램",
  openai: "OpenAI API",
};
const errorMessages = {
  UNKNOWN_SOURCE_MODE: "회의 입력 종류를 다시 선택해 주세요.",
  UNKNOWN_PROVIDER: "사용할 AI를 다시 선택해 주세요.",
  UNKNOWN_EXECUTION_MODE: "일하는 방식을 다시 선택해 주세요.",
  REQUESTED_OUTPUTS_INVALID: "원하는 결과를 한 가지 이상 선택해 주세요.",
  EMPTY_TRANSCRIPT_FILE: "전사 TXT 파일이 비어 있습니다.",
  TRANSCRIPT_FILE_TOO_LARGE: "전사 TXT는 2MB 이하만 사용할 수 있습니다.",
  TRANSCRIPT_ENCODING_UNSUPPORTED: "TXT 문자 형식을 읽을 수 없습니다. UTF-8로 다시 저장해 주세요.",
  TRANSCRIPT_BINARY_CONTENT: "TXT가 아닌 파일로 보입니다. 내보낸 전사 파일을 선택해 주세요.",
  TRANSCRIPT_PARSE_FAILED: "화자와 대화를 찾지 못했습니다. 화면의 예시 형식을 확인해 주세요.",
  TRANSCRIPT_TIME_ORDER_INVALID: "전사의 시간이 앞뒤로 뒤섞여 있습니다.",
  TRANSCRIPT_TOO_SHORT: "회의 내용이 너무 짧아 기록을 만들 수 없습니다.",
  EMPTY_AUDIO: "회의 녹음 파일을 선택해 주세요.",
  UNSUPPORTED_AUDIO_TYPE: "지원하지 않는 음성 형식입니다.",
  AUDIO_TOO_LARGE: "회의 녹음은 100MB 이하만 사용할 수 있습니다.",
  INVALID_WAV: "WAV 파일이 손상되었거나 올바른 음성 파일이 아닙니다.",
  INVALID_AUDIO: "음성 파일을 읽을 수 없습니다. 파일을 다시 내보내 주세요.",
  LIVE_STT_DEPENDENCY_MISSING: "음성 변환 프로그램이 설치되지 않았습니다.",
  LIVE_STT_MODEL_UNAVAILABLE: "음성 변환 모델을 준비하지 못했습니다. 인터넷 연결과 저장 공간을 확인해 주세요.",
  LIVE_STT_FAILED: "음성을 글로 바꾸지 못했습니다. 지원 형식과 음질을 확인해 주세요.",
  EMPTY_TRANSCRIPT: "음성에서 말소리를 찾지 못했습니다.",
  PARTICIPANT_METADATA_INVALID: "참석자 정보 형식을 읽을 수 없습니다.",
  PARTICIPANT_COUNT_INVALID: "참석자 정보를 한 명 이상, 50명 이하로 입력해 주세요.",
  DUPLICATE_PARTICIPANT: "같은 이름의 참석자가 두 번 입력되었습니다.",
  OPENAI_API_KEY_MISSING: "OpenAI API 키 환경 변수가 설정되지 않았습니다.",
  OPENAI_MODEL_INVALID: "OpenAI 모델 이름이 올바르지 않거나 사용할 수 없습니다.",
  PROVIDER_AUTH_REQUIRED: "선택한 AI의 로그인이 필요합니다.",
  PROVIDER_UNAVAILABLE: "선택한 AI에 연결할 수 없습니다.",
  PROVIDER_RATE_LIMITED: "AI 사용량 제한에 도달했습니다. 잠시 뒤 다시 시도해 주세요.",
  HOST_BRIDGE_NOT_STARTED: "Codex 또는 Claude를 안전하게 연결하는 실행 프로그램이 시작되지 않았습니다.",
  CLI_NOT_FOUND: "선택한 AI 프로그램을 찾지 못했습니다.",
  CLI_TIMEOUT: "AI 프로그램의 응답 시간이 초과되었습니다.",
  PROVIDER_SCHEMA_INVALID: "AI 결과의 필수 항목이 빠져 있어 검토를 멈췄습니다.",
};
const warningMessages = {
  PARTICIPANTS_INFERRED_FROM_TRANSCRIPT: "참석자 정보가 없어 전사에 적힌 화자명을 사용했습니다.",
  SPEAKER_LABELS_REQUIRE_REVIEW: "음성 변환만으로는 화자를 구분하지 못하므로 참석자와 발화를 직접 확인해 주세요.",
  FIXTURE_TRANSCRIPT_UPLOAD_NOT_TRANSCRIBED: "연습 모드에서는 업로드 음성 대신 포함된 예시 전사로 화면 흐름을 확인했습니다.",
  FIXTURE_FALLBACK_USED: "선택한 AI에 연결하지 못해 연습용 결과로 화면 흐름을 이어갔습니다.",
};

function selectedSource() {
  return form.querySelector('input[name="source_mode"]:checked').value;
}

function updateSourceUI() {
  const source = selectedSource();
  loadedTranscriptSample = null;
  document.querySelectorAll(".source-card").forEach(card => {
    card.classList.toggle("selected", card.querySelector("input").checked);
  });
  document.querySelector("#text-upload-wrap").classList.toggle("hidden", source === "audio");
  document.querySelector("#audio-upload-wrap").classList.toggle("hidden", source !== "audio");
  const textLabel = document.querySelector("#text-file-label");
  if (!transcriptInput.files[0]) {
    textLabel.textContent = source === "clova_note" ? "ClovaNote TXT 파일 선택" : "전사 TXT 파일 선택";
  }
}

document.querySelectorAll('input[name="source_mode"]').forEach(input => input.addEventListener("change", updateSourceUI));
document.querySelectorAll('input[name="execution_mode"]').forEach(input => {
  input.addEventListener("change", () => {
    document.querySelectorAll(".mode-card").forEach(card => card.classList.toggle("selected", card.querySelector("input").checked));
  });
});
transcriptInput.addEventListener("change", () => {
  document.querySelector("#text-file-label").textContent = transcriptInput.files[0]?.name || "전사 TXT 파일 선택";
});
audioInput.addEventListener("change", () => {
  document.querySelector("#audio-file-label").textContent = audioInput.files[0]?.name || "회의 녹음 파일 선택";
});
providerSelect.addEventListener("change", () => {
  document.querySelector("#model-field").classList.toggle("hidden", providerSelect.value !== "openai");
});

document.querySelector("#load-text-sample").addEventListener("click", async () => {
  const source = selectedSource();
  if (source === "audio") {
    showFormError("예시 전사를 사용하려면 Google Meet 또는 ClovaNote 입력을 선택해 주세요.");
    return;
  }
  const sampleName = source === "clova_note" ? "clova-note" : "google-meet";
  const filename = source === "clova_note" ? "clova_note_sample_ko.txt" : "google_meet_sample_ko.txt";
  try {
    const response = await fetch(`/api/samples/${sampleName}`);
    if (!response.ok) throw new Error(`HTTP_${response.status}`);
    loadedTranscriptSample = new File([await response.blob()], filename, { type: "text/plain" });
    transcriptInput.value = "";
    document.querySelector("#text-file-label").textContent = `${filename} · 예시 준비 완료`;
    formError.classList.add("hidden");
  } catch (error) {
    showFormError(`예시 파일을 불러오지 못했습니다. ${error.message}`);
  }
});

document.querySelectorAll(".tab").forEach(button => {
  button.addEventListener("click", () => showTab(button.dataset.tab));
});

document.querySelector("#download-json").addEventListener("click", () => {
  if (!lastResult) return;
  downloadText(
    `meeting-record-${lastResult.status.toLowerCase()}.json`,
    JSON.stringify(lastResult, null, 2),
    "application/json",
  );
});

document.querySelector("#download-markdown").addEventListener("click", () => {
  if (!lastResult?.markdown_preview) return;
  downloadText("meeting-record.md", lastResult.markdown_preview, "text/markdown;charset=utf-8");
});

form.addEventListener("submit", async event => {
  event.preventDefault();
  formError.classList.add("hidden");
  const source = selectedSource();
  const selectedFile = source === "audio" ? audioInput.files[0] : (transcriptInput.files[0] || loadedTranscriptSample);
  const outputs = [...form.querySelectorAll('input[name="output_kind"]:checked')].map(input => input.value);
  if (!selectedFile) {
    showFormError(source === "audio" ? "회의 녹음 파일을 선택해 주세요." : "전사 TXT 파일을 선택해 주세요.");
    return;
  }
  if (!outputs.length) {
    showFormError("원하는 결과를 한 가지 이상 선택해 주세요.");
    return;
  }

  const data = new FormData(form);
  data.delete("output_kind");
  data.set("requested_outputs", outputs.join(","));
  data.set("allow_fixture_fallback", form.querySelector('input[name="allow_fixture_fallback"]').checked ? "true" : "false");
  if (source === "audio") data.delete("transcript_file");
  else {
    data.delete("audio");
    if (!transcriptInput.files[0] && loadedTranscriptSample) {
      data.set("transcript_file", loadedTranscriptSample, loadedTranscriptSample.name);
    }
  }

  runButton.disabled = true;
  runButton.textContent = source === "audio" ? "음성을 글로 바꾸고 기록 만드는 중" : "회의 기록 만드는 중";
  try {
    const response = await fetch("/api/process", { method: "POST", body: data });
    if (!response.ok) throw new Error(`HTTP_${response.status}`);
    lastResult = await response.json();
    render(lastResult);
    document.querySelector(".result-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    renderClientError(error);
  } finally {
    runButton.disabled = false;
    runButton.textContent = "회의 기록 만들기";
  }
});

function render(result) {
  emptyResult.classList.add("hidden");
  resultPanel.classList.remove("hidden");
  const ready = result.status === "READY";
  const badge = document.querySelector("#status-badge");
  badge.textContent = ready ? "검토 준비" : "확인 필요";
  badge.classList.toggle("hold", !ready);
  document.querySelector("#result-title").textContent = ready ? "회의 기록 초안이 준비되었습니다" : "입력을 확인한 뒤 다시 실행해 주세요";
  const provider = providerLabels[result.provider_used] || providerLabels[result.provider_requested] || "선택한 AI";
  const model = result.model_used && !result.model_used.startsWith("deterministic-") ? ` · ${result.model_used}` : "";
  document.querySelector("#result-meta").textContent = `${sourceLabels[result.source_mode] || "회의 입력"} · ${provider}${model}`;
  document.querySelector("#download-markdown").disabled = !result.markdown_preview;

  const alerts = [];
  (result.error_codes || []).forEach(code => alerts.push(`<div class="alert"><b>확인할 내용</b> ${escapeHtml(friendlyError(code))}</div>`));
  (result.warnings || []).forEach(code => {
    const message = warningMessages[code];
    if (message) alerts.push(`<div class="alert info">${escapeHtml(message)}</div>`);
  });
  if (result.fallback_reason) {
    alerts.push(`<div class="alert info"><b>AI 연결 전환</b> ${escapeHtml(friendlyError(result.fallback_reason))} 연습용 결과로 이어서 보여드립니다.</div>`);
  }
  if (ready) {
    alerts.push('<div class="alert info"><b>아직 저장하거나 보내지 않았습니다.</b> 원문, 담당자, 기한을 사람이 확인해야 합니다.</div>');
  }
  document.querySelector("#alerts").innerHTML = alerts.join("");

  renderRoute(result);
  const record = result.meeting_record || result.brief;
  const metrics = [
    [result.segments?.length || 0, "원문 구간"],
    [result.participants?.length || new Set((result.segments || []).map(item => item.speaker)).size, "확인할 참석자"],
    [record?.action_items?.length || 0, "할 일"],
    [result.evidence?.length || 0, "연결된 근거"],
  ];
  document.querySelector("#metrics").innerHTML = metrics.map(([value, label]) => `<div class="metric"><b>${escapeHtml(value)}</b><span>${label}</span></div>`).join("");
  document.querySelector("#tab-record").innerHTML = renderRecord(record);
  document.querySelector("#tab-markdown").innerHTML = result.markdown_preview
    ? `<pre class="preview">${escapeHtml(result.markdown_preview)}</pre>`
    : '<div class="empty-result"><span>근거 검사를 통과한 뒤 문서 미리보기가 만들어집니다.</span></div>';
  document.querySelector("#tab-email").innerHTML = renderEmail(result.email_draft);
  document.querySelector("#tab-integrations").innerHTML = renderIntegrations(result.integration_plan || []);
  document.querySelector("#tab-evidence").innerHTML = renderSegments(result.segments || []);
  showTab("record");
}

function renderRoute(result) {
  const mode = modeLabels[result.execution_mode_used] || "입력 확인 전";
  const steps = (result.workflow_steps || []).map(step => `<span>${escapeHtml(step)}</span>`).join("");
  document.querySelector("#route-card").innerHTML = `
    <div class="route-heading"><b>${escapeHtml(mode)}</b><span>이번 요청에 사용한 방식</span></div>
    <p class="route-reason">${escapeHtml(result.route_reason || "입력을 확인한 뒤 처리 방식을 선택합니다.")}</p>
    <div class="step-list">${steps}</div>`;
}

function renderRecord(record) {
  if (!record) return '<div class="empty-result"><span>회의 기록이 아직 만들어지지 않았습니다.</span></div>';
  const summary = record.summary
    ? `<div class="record-summary">${escapeHtml(record.summary.text)}${evidenceChips(record.summary.evidence_ids)}</div>`
    : "";
  return `<h3 class="record-title">${escapeHtml(record.title)}</h3>
    ${summary}
    ${renderGroup("참석자별 관점", record.participant_perspectives, "perspective")}
    ${renderGroup("결정 사항", record.decisions)}
    ${renderGroup("할 일", record.action_items, "action")}
    ${renderGroup("단기 인사이트", record.short_term_insights)}
    ${renderGroup("중기 인사이트", record.mid_term_insights)}
    ${renderGroup("장기 인사이트", record.long_term_insights)}
    ${renderGroup("확인할 질문", record.open_questions)}`;
}

function renderGroup(title, items = [], kind = "plain") {
  if (!items?.length) return "";
  return `<div class="record-group"><h4>${escapeHtml(title)}</h4>${items.map(item => {
    const prefix = kind === "perspective" ? `<b>${escapeHtml(item.participant)}</b> · ` : "";
    const detail = kind === "action" ? `<small>담당 ${escapeHtml(item.assignee)} · 기한 ${escapeHtml(item.due_date || "확인 필요")}</small>` : "";
    return `<div class="record-item">${prefix}${escapeHtml(item.text)}${detail}${evidenceChips(item.evidence_ids)}</div>`;
  }).join("")}</div>`;
}

function evidenceChips(ids = []) {
  return `<div>${ids.map(id => `<button type="button" class="evidence-chip" data-evidence="${escapeHtml(id)}">원문 ${escapeHtml(id)}</button>`).join("")}</div>`;
}

document.addEventListener("click", event => {
  const button = event.target.closest("[data-evidence]");
  if (!button) return;
  showTab("evidence");
  document.querySelector(`#segment-${CSS.escape(button.dataset.evidence)}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
});

function renderEmail(email) {
  if (!email) return '<div class="empty-result"><span>근거 검사를 통과한 뒤 이메일 초안이 만들어집니다.</span></div>';
  const recipients = email.recipients?.length ? email.recipients.join(", ") : "검토 후 직접 입력";
  return `<div class="email-sheet">
    <div class="email-row"><b>받는 사람</b><span>${escapeHtml(recipients)}</span></div>
    <div class="email-row"><b>제목</b><span>${escapeHtml(email.subject)}</span></div>
    <div class="email-body">${escapeHtml(email.body)}</div>
  </div><div class="plan-note">초안만 만들었습니다. 받는 사람과 내용을 확인해도 이 앱이 자동 발송하지는 않습니다.</div>`;
}

function renderIntegrations(items) {
  if (!items.length) return '<div class="empty-result"><span>근거 검사를 통과한 뒤 외부 연결 계획이 만들어집니다.</span></div>';
  const destination = { notion: "Notion", confluence: "Confluence", email: "이메일" };
  const action = { create_page: "새 문서 만들기", create_draft: "메일 초안 만들기" };
  return `<table class="plan-table"><thead><tr><th>연결 대상</th><th>승인 뒤 할 일</th><th>현재 상태</th></tr></thead><tbody>
    ${items.map(item => `<tr><td>${escapeHtml(destination[item.destination] || item.destination)}</td><td>${escapeHtml(action[item.proposed_action] || item.proposed_action)}</td><td>계획만 준비 · 승인 필요</td></tr>`).join("")}
    </tbody></table><div class="plan-note">이 앱은 외부 서비스에 로그인하거나 문서를 저장하지 않았습니다. 연결 기능을 붙이더라도 사람 승인 뒤에만 실행해야 합니다.</div>`;
}

function renderSegments(segments) {
  if (!segments.length) return '<div class="empty-result"><span>확인할 원문이 없습니다.</span></div>';
  return `<div class="segments">${segments.map(segment => `
    <div class="segment" id="segment-${escapeHtml(segment.id)}">
      <div class="segment-id">${escapeHtml(segment.id)}<br>${formatTime(segment.start)}</div>
      <div><b>${escapeHtml(segment.speaker)}</b><p>${escapeHtml(segment.text)}</p></div>
    </div>`).join("")}</div>`;
}

function showTab(name) {
  document.querySelectorAll(".tab").forEach(button => button.classList.toggle("active", button.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.toggle("hidden", panel.id !== `tab-${name}`));
}

function renderClientError(error) {
  lastResult = null;
  emptyResult.classList.add("hidden");
  resultPanel.classList.remove("hidden");
  const badge = document.querySelector("#status-badge");
  badge.textContent = "연결 확인";
  badge.classList.add("hold");
  document.querySelector("#result-title").textContent = "앱 실행 상태를 확인해 주세요";
  document.querySelector("#result-meta").textContent = "로컬 서버에 연결하지 못했습니다.";
  document.querySelector("#alerts").innerHTML = `<div class="alert">${escapeHtml(error.message)}</div>`;
  document.querySelector("#route-card").innerHTML = "";
  document.querySelector("#metrics").innerHTML = "";
  ["record", "markdown", "email", "integrations", "evidence"].forEach(name => {
    document.querySelector(`#tab-${name}`).innerHTML = "";
  });
}

function friendlyError(code) {
  if (errorMessages[code]) return errorMessages[code];
  if (code?.includes("UNKNOWN_EVIDENCE")) return "결과가 가리키는 원문 근거를 찾을 수 없습니다.";
  if (code?.includes("OUTPUT_MISSING")) return "선택한 결과 일부가 만들어지지 않았습니다.";
  if (code?.startsWith("PROVIDER_HTTP_")) return "선택한 AI 서비스가 요청을 처리하지 못했습니다.";
  return "결과의 품질 기준을 통과하지 못했습니다. 입력과 연결 상태를 확인해 주세요.";
}

function showFormError(message) {
  formError.textContent = message;
  formError.classList.remove("hidden");
  formError.scrollIntoView({ behavior: "smooth", block: "center" });
}

function formatTime(seconds) {
  const minutes = Math.floor(Number(seconds || 0) / 60).toString().padStart(2, "0");
  const rest = Math.floor(Number(seconds || 0) % 60).toString().padStart(2, "0");
  return `${minutes}:${rest}`;
}

function downloadText(filename, value, type) {
  const blob = new Blob([value], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

fetch("/api/capabilities")
  .then(response => response.json())
  .then(data => {
    const voiceReady = data.inputs?.live_stt_dependency_installed ?? data.stt?.live_dependency_installed;
    const openAI = data.providers?.openai_configured;
    const bridgeReady = data.providers?.host_bridge_configured;
    const mode = data.runtime?.delivery_mode === "docker" ? "Docker" : "localhost";
    document.querySelector("#health").textContent = `${mode} 준비 · 연습용 결과 가능 · 음성 변환 ${voiceReady ? "가능" : "추가 준비"} · OpenAI ${openAI ? "설정됨" : "선택"}`;
    ["codex", "claude"].forEach(provider => {
      const option = providerSelect.querySelector(`option[value="${provider}"]`);
      option.disabled = !bridgeReady;
      if (!bridgeReady && !option.textContent.includes("강사 확장")) option.textContent += " · 강사 확장";
    });
    if (data.providers?.openai_default_model) document.querySelector("#model").value = data.providers.openai_default_model;
  })
  .catch(() => { document.querySelector("#health").textContent = "로컬 앱 연결 확인 필요"; });

updateSourceUI();
