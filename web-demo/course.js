const course = {
  2: {
    title: "한국어 회의 Agent",
    subtitle: "오디오 계약 · STT · LangChain · 근거 검증",
    promise: "12분 합성 회의를 근거가 남는 업무 데이터로 전환",
  },
  3: {
    title: "코드 리뷰 Agent",
    subtitle: "Unified Diff · 변경 라인 · Test · Offline Eval",
    promise: "의도적으로 위험한 PR에서 실제 변경 라인 finding 생성",
  },
  4: {
    title: "GitHub 승인 Workflow",
    subtitle: "LangGraph · Human Approval · Dry-run · Idempotency",
    promise: "사람 승인 전 외부 쓰기를 차단하는 PR 리뷰 Workflow",
  },
  5: {
    title: "Agent Operations Console",
    subtitle: "Router · Trace · Dataset Eval · Release Gate",
    promise: "두 Agent를 관측·평가하고 배포 여부를 증거로 판단",
  },
};

const params = new URLSearchParams(location.search);
const day = Number(params.get("day") || 2);
const scene = params.get("scene") || "overview";
const selected = course[day] || course[2];

const byId = (id) => document.getElementById(id);
const pretty = (value) => JSON.stringify(value, null, 2);
const label = (value) => value.replaceAll("_", " ").toUpperCase();

function renderNavigation() {
  byId("day-navigation").innerHTML = Object.keys(course)
    .map((item) => `<a class="${Number(item) === day ? "active" : ""}" href="course.html?day=${item}">DAY ${item}</a>`)
    .join("");
}

function renderScene() {
  const target = document.querySelector(`[data-scene="${scene}"]`);
  if (target) {
    document.documentElement.style.scrollBehavior = "auto";
    requestAnimationFrame(() => target.scrollIntoView({ block: "start", behavior: "auto" }));
  }
}

function render(data) {
  document.title = `Day ${day} · ${selected.title}`;
  byId("day-label").textContent = `DAY ${day} · RESULT FIRST`;
  byId("service-title").textContent = selected.title;
  byId("service-subtitle").textContent = `${selected.subtitle}\n${selected.promise}`;
  byId("decision").textContent = data.decision;
  byId("artifact-path").textContent = `output/course-demos/day${day}/demo_result.json`;
  byId("result-json").textContent = pretty({ day, decision: data.decision, metrics: data.metrics, external_write: data.external_write });

  byId("stage-list").innerHTML = data.stages
    .map((stage, index) => `
      <article class="stage-card">
        <span>${String(index + 1).padStart(2, "0")}</span>
        <div><strong>${label(stage.name)}</strong><small>${stage.artifact}</small></div>
        <em>${stage.status}</em>
      </article>`)
    .join("");

  byId("metric-grid").innerHTML = Object.entries(data.metrics)
    .map(([name, value]) => `<article class="metric-card"><span>${label(name)}</span><strong>${value}</strong></article>`)
    .join("");

  byId("boundary-status").textContent = data.boundary_case.status;
  byId("boundary-json").textContent = pretty(data.boundary_case);
  renderScene();
}

async function initialize() {
  renderNavigation();
  try {
    const response = await fetch(`public/course-demos/day${day}.json`);
    if (!response.ok) throw new Error(`DEMO_DATA_${response.status}`);
    render(await response.json());
  } catch (error) {
    document.body.innerHTML = `<main class="error"><h1>Demo data error</h1><p>${error.message}</p></main>`;
  }
}

initialize();
