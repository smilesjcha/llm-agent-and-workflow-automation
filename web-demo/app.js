const state = {
  data: null,
  decision: "approve",
  result: null,
};

const byId = (id) => document.getElementById(id);

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function renderPipeline() {
  const steps = state.data.langchain.pipeline;
  byId("pipeline-steps").innerHTML = steps
    .map(
      (step, index) => `
        <article class="pipeline-step">
          <span>0${index + 1}</span>
          <strong>${step}</strong>
        </article>`,
    )
    .join("");

  byId("transcript-source").textContent = state.data.transcript;
  const checks = state.data.langchain.checks;
  byId("policy-status").textContent = Object.values(checks).every(Boolean)
    ? "모든 정책 검사 통과"
    : "사람 확인 필요";
  byId("policy-checks").innerHTML = Object.entries(checks)
    .map(([name, passed]) => `<li>${passed ? "PASS" : "HOLD"} · ${name}</li>`)
    .join("");
}

function renderDraft() {
  const draft = state.data.langchain.result;
  byId("meeting-title").textContent = draft.title;
  byId("meeting-summary").textContent = draft.summary;
  byId("edited-summary").value = state.data.scenarios.edit.human_input.edited_summary;
  byId("action-items").innerHTML = draft.action_items
    .map(
      (item) => `
        <div class="action-item">
          <p><strong>${item.task}</strong><br /><span>근거 ${item.evidence_ids.join(", ")}</span></p>
          <span>${item.owner} · ${item.due_date}</span>
        </div>`,
    )
    .join("");
}

function selectDecision(decision) {
  state.decision = decision;
  document.querySelectorAll(".decision-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.decision === decision);
  });
  byId("edit-box").classList.toggle("hidden", decision !== "edit");
  const scenario = state.data.scenarios[decision];
  byId("interrupt-json").textContent = pretty(scenario.interrupt_payload);
}

function applyDecision() {
  const original = state.data.scenarios[state.decision];
  state.result = structuredClone(original);

  if (state.decision === "edit") {
    const editedSummary = byId("edited-summary").value.trim();
    if (!editedSummary) {
      byId("edited-summary").focus();
      return;
    }
    state.result.human_input.edited_summary = editedSummary;
    state.result.final_state.draft.summary = editedSummary;
  }

  renderResult();
  byId("result").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderResult() {
  const finalState = state.result.final_state;
  const evaluation = state.result.evaluation;
  byId("terminal-status").textContent = finalState.status;
  byId("release-gate").textContent = evaluation.decision;
  byId("terminal-note").textContent = finalState.export_ready
    ? "사람 승인을 기록한 뒤 로컬 JSON 저장이 가능합니다."
    : "외부로 내보내지 않고 검토 상태로 종료합니다.";

  byId("audit-events").innerHTML = finalState.audit_events
    .map(
      (event) => `
        <li>
          <strong>${event.node}</strong><br />
          <span class="muted">${event.status || event.decision || event.side_effect || "recorded"}</span>
        </li>`,
    )
    .join("");
}

function downloadResult() {
  const payload = {
    saved_at: new Date().toISOString(),
    source: state.data.generated_from,
    decision: state.decision,
    result: state.result,
  };
  const blob = new Blob([pretty(payload)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `meeting-agent-${state.decision}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function initialize() {
  try {
    const response = await fetch("public/demo-data.json");
    if (!response.ok) throw new Error(`데이터를 불러오지 못했습니다: ${response.status}`);
    state.data = await response.json();
    state.result = structuredClone(state.data.scenarios.approve);
    renderPipeline();
    renderDraft();
    selectDecision("approve");
    renderResult();
  } catch (error) {
    document.body.innerHTML = `<main class="hero"><h1>Demo data error</h1><p>${error.message}</p></main>`;
  }
}

document.querySelectorAll(".decision-button").forEach((button) => {
  button.addEventListener("click", () => selectDecision(button.dataset.decision));
});
byId("apply-decision").addEventListener("click", applyDecision);
byId("download-result").addEventListener("click", downloadResult);

initialize();
