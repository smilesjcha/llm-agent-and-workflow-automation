import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import {
  MUSINSA_PPT,
  MUSINSA_REFERENCE,
  makeCoursePalette,
} from "../../design-system/ppt/cha-sungjae-lecture/design-system.mjs";
import { DAY3_GLOBAL, DAY3_STUDENT_PERIODS } from "./day3_student_content.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUT = path.join(
  ROOT,
  "slides/IPA_LLM_Agent_업무자동화_Day3_2026_STUDENT_READY_176p.pptx",
);
const LAB_OUT = path.join(ROOT, "output/course-labs/day3-v2");
const RESULT_FILES = [
  "01_review_contract.json",
  "02_parsed_diff.json",
  "03_context_pack.json",
  "04_candidate_review.json",
  "05_hybrid_review.json",
  "06_human_review.json",
  "07_evaluation.json",
  "08_release_evidence.json",
];

const C = makeCoursePalette();
const FONT = "AppleGothic";
const MONO = "Menlo";
const deck = Presentation.create({ slideSize: MUSINSA_PPT.slide });
const assetCache = new Map();

// 09:00-17:30 teaching blocks are 400 minutes and Q&A is 30 minutes.
// Slides 4-11 are pre-class reference screens. Slides 1-3 use the first six
// minutes of period 1, so slides 12-17 give those six minutes back.
const NOTE_MINUTE_OVERRIDES = new Map([
  ...Array.from({ length: 8 }, (_, index) => [index + 4, 0]),
  [12, 0], [13, 1], [14, 2], [15, 2], [16, 2], [17, 1],
  [176, 22],
]);

const S = Object.freeze({
  deckTitle: 72,
  sectionTitle: 64,
  title: 48,
  lead: 36,
  body: 28,
  table: 27,
  label: 27,
  code: 25,
  footer: 14,
});

function addShape(slide, geometry, position, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({
    geometry,
    position,
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
  });
}

function addText(slide, text, position, options = {}) {
  const requested = options.size ?? S.body;
  const size = options.allowSmall ? requested : Math.max(requested, S.label);
  const box = addShape(
    slide,
    "textbox",
    position,
    options.fill ?? "none",
    options.lineFill ?? "none",
    options.lineWidth ?? 0,
  );
  box.text = String(text).replace(/[–—]/g, "-");
  box.text.style = {
    fontSize: size,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    typeface: options.typeface ?? FONT,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "none",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.08,
    insets: options.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

function addFooter(slide, period, page) {
  addShape(slide, "line", { left: 64, top: 674, width: 1152, height: 0 }, "none", C.faint, 1);
  addText(
    slide,
    "DAY 3 · REVIEW COPILOT",
    { left: 64, top: 684, width: 430, height: 18 },
    { size: S.footer, allowSmall: true, bold: true, color: C.muted },
  );
  addText(
    slide,
    String(page).padStart(3, "0"),
    { left: 1120, top: 684, width: 96, height: 18 },
    { size: S.footer, allowSmall: true, bold: true, color: C.muted, align: "right" },
  );
}

function addHeader(slide, title, period, eyebrow = "") {
  slide.background.fill = C.paper;
  const navigation = period
    ? `${period.classNumber}차시 · ${period.time}`
    : "DAY 3 · 09:00-18:00";
  addText(
    slide,
    navigation,
    { left: 64, top: 30, width: 650, height: 26 },
    { size: S.label, bold: true, color: C.muted },
  );
  addText(
    slide,
    title,
    { left: 64, top: 72, width: 1152, height: 60 },
    { size: S.title, bold: true, color: C.ink },
  );
  addFooter(slide, period, deck.slides.items.length);
}

function addNotes(slide, { minutes, talk, activity = "", sources = [] }) {
  const uniqueSources = [...new Set([MUSINSA_REFERENCE, ...sources])];
  const page = deck.slides.items.length;
  const effectiveMinutes = NOTE_MINUTE_OVERRIDES.get(page) ?? minutes;
  const timeLabel = effectiveMinutes === 0
    ? "- 권장 시간: 수업 전 확인(본 수업 시간 미산정)"
    : `- 권장 시간: ${effectiveMinutes}분`;
  slide.speakerNotes.textFrame.setText([
    "[강사용 진행]",
    timeLabel,
    `- 핵심 발화: ${talk}`,
    activity ? `- 수강생 활동: ${activity}` : "- 수강생 활동: 화면의 핵심 항목 확인",
    "",
    "[Sources]",
    ...uniqueSources.map((source) => `- ${source}`),
    "[/Sources]",
  ].join("\n"));
  slide.speakerNotes.setVisible(true);
}

function addManualTable(slide, { left = 64, top, headers, rows, widths, rowHeight = 86, headerHeight = 54, fontSize = S.table }) {
  let x = left;
  headers.forEach((header, index) => {
    addShape(slide, "rect", { left: x, top, width: widths[index], height: headerHeight }, C.black, C.black, 1);
    addText(
      slide,
      header,
      { left: x + 14, top: top + 12, width: widths[index] - 28, height: headerHeight - 20 },
      { size: S.label, bold: true, color: C.white, valign: "middle" },
    );
    x += widths[index];
  });
  rows.forEach((row, rowIndex) => {
    let xx = left;
    const y = top + headerHeight + rowIndex * rowHeight;
    row.forEach((value, columnIndex) => {
      addShape(
        slide,
        "rect",
        { left: xx, top: y, width: widths[columnIndex], height: rowHeight },
        rowIndex % 2 ? C.gray025 : C.white,
        C.faint,
        1,
      );
      addText(
        slide,
        value,
        { left: xx + 14, top: y + 12, width: widths[columnIndex] - 28, height: rowHeight - 24 },
        {
          size: fontSize,
          bold: columnIndex === 0,
          color: C.ink,
          valign: "middle",
          lineSpacing: 1.04,
        },
      );
      xx += widths[columnIndex];
    });
  });
}

async function assetBytes(relativePath) {
  const fullPath = path.join(ROOT, relativePath);
  if (!assetCache.has(fullPath)) assetCache.set(fullPath, await fs.readFile(fullPath));
  return assetCache.get(fullPath);
}

function notebookCode(periodIndex) {
  return DAY3_STUDENT_PERIODS[periodIndex].notebookSnippet;
}

async function resultPreview(periodIndex) {
  const fileName = RESULT_FILES[periodIndex];
  const filePath = path.join(LAB_OUT, fileName);
  const raw = await fs.readFile(filePath, "utf8");
  const parsed = JSON.parse(raw);
  const policyPreview = parsed.policy ?? parsed;
  const compact = [
    () => ({
      severities: (policyPreview.allowed_severities ?? []).join("/"),
      focus_count: (policyPreview.focus ?? []).length,
      ignored_count: (policyPreview.ignored ?? []).length,
      require_added_line: policyPreview.require_added_line,
      automatic_publish: policyPreview.automatic_publish,
    }),
    () => ({
      changed_paths: parsed.changed_paths.length,
      added_lines: parsed.added_lines.length,
      first_added_line: parsed.added_lines[0].line,
      first_added_text: parsed.added_lines[0].text,
    }),
    () => ({
      changed_paths: parsed.changed_paths,
      added_line_count: parsed.added_line_count,
      test_candidates: parsed.test_candidates,
      excluded_data: parsed.excluded_data,
    }),
    () => ({
      status: parsed.status,
      provider_requested: parsed.provider_requested,
      provider_used: parsed.provider_used,
      model: parsed.model,
      schema_valid: parsed.schema_valid,
      fallback_reason: parsed.fallback_reason,
      candidate_count: parsed.candidates.length,
    }),
    () => ({
      status: parsed.status,
      finding_count: parsed.findings.length,
      severities: parsed.findings.map(({ severity }) => severity),
      automatic_publish: parsed.automatic_publish,
      external_write: false,
    }),
    () => ({
      status: parsed.status,
      decision: parsed.decision,
      reviewer: parsed.reviewer,
      human_reviewed: parsed.human_reviewed,
      external_write: parsed.external_write,
    }),
    () => ({
      cases: `${parsed.case_passed}/${parsed.case_count}`,
      precision: parsed.precision,
      recall: parsed.recall,
      f1: parsed.f1,
      expected_failures: `${parsed.expected_failure_cases_passed}/${parsed.expected_failure_cases}`,
      release_decision: parsed.release_decision,
    }),
    () => ({
      finding_count: parsed.finding_count,
      human_review_required: parsed.human_review_required,
      rule_baseline: parsed.rule_baseline_gate.release_decision,
      provider_candidate: parsed.provider_candidate_gate.status,
      github: parsed.github_dry_run.status,
      decision: parsed.decision,
      external_write: parsed.external_write,
    }),
  ][periodIndex]();
  const lines = JSON.stringify(compact, null, 2)
    .split("\n")
    .slice(0, 14)
    .map((line) => (line.length > 58 ? `${line.slice(0, 55)}...` : line));
  return { fileName, filePath, text: lines.join("\n") };
}

function addNumberedRows(
  slide,
  rows,
  {
    top = 176,
    rowHeight = 108,
    bodySize = S.body,
    numberLeft = 78,
    lineLeft = 158,
    bodyLeft = 246,
    bodyWidth = 946,
  } = {},
) {
  rows.forEach((row, index) => {
    const y = top + index * rowHeight;
    addText(
      slide,
      String(index + 1).padStart(2, "0"),
      { left: numberLeft, top: y + 10, width: 64, height: 38 },
      { size: S.table, bold: true, color: C.muted, valign: "middle" },
    );
    addShape(slide, "line", { left: lineLeft, top: y + 30, width: 48, height: 0 }, "none", C.black, 2);
    addText(
      slide,
      row,
      { left: bodyLeft, top: y, width: bodyWidth, height: rowHeight - 18 },
      { size: bodySize, bold: index === 0, color: C.ink, valign: "middle" },
    );
  });
}

function labPath(value) {
  return String(value)
    .replaceAll("materials/day3/", "materials/day3/\n")
    .replaceAll("labs/day3/review_copilot/", "labs/day3/\nreview_copilot/")
    .replaceAll("src/course_services/", "src/course_services/\n")
    .replaceAll("output/course-labs/day3-v2/", "output/course-labs/day3-v2/\n")
    .replaceAll("tests/", "tests/\n")
    .replaceAll(" · ", "\n");
}

function terminalCommand(value) {
  return String(value)
    .replace(
      " --smoke-and-exit --port 0",
      " \\\n  --smoke-and-exit --port 0",
    )
    .split("\n")
    .map((line) => line.replace(" -k ", " \\\n  -k "))
    .join("\n");
}

function labArtifact(value) {
  const text = String(value);
  if (text.length <= 18) return text;
  const midpoint = Math.floor(text.length / 2);
  let split = text.lastIndexOf("_", midpoint + 5);
  if (split < 4) split = text.indexOf("_", midpoint);
  if (split < 0) return text;
  return `${text.slice(0, split + 1)}\n${text.slice(split + 1)}`;
}

function labMapPath(value) {
  return String(value)
    .replace(/ · \d차시/g, "")
    .split(" · ")
    .map((part) => {
      const trimmed = part.trim();
      if (!trimmed.includes("/")) return trimmed;
      return trimmed.split("/").at(-1);
    })
    .join("\n");
}

function addDayCover() {
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  addShape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  addText(slide, "IPA · LLM AGENT & 업무자동화 40H", { left: 84, top: 60, width: 720, height: 30 }, { size: S.label, bold: true, color: C.white });
  addText(slide, "DAY 3 · 09:00-18:00", { left: 84, top: 112, width: 720, height: 36 }, { size: S.table, bold: true, color: C.blue });
  addText(slide, DAY3_GLOBAL.title, { left: 84, top: 206, width: 1080, height: 100 }, { size: S.deckTitle, bold: true, color: C.white, valign: "middle" });
  addText(slide, DAY3_GLOBAL.subtitle, { left: 88, top: 338, width: 1080, height: 74 }, { size: S.lead, bold: true, color: C.gray300 });
  addShape(slide, "line", { left: 84, top: 474, width: 1092, height: 0 }, "none", C.blue, 4);
  addText(slide, "결과물", { left: 84, top: 514, width: 180, height: 30 }, { size: S.label, bold: true, color: C.gray300 });
  addText(slide, "실행 Notebook · Review Report · Localhost · Draft PR", { left: 270, top: 504, width: 900, height: 54 }, { size: S.body, bold: true, color: C.white, valign: "middle" });
  addNotes(slide, {
    minutes: 1,
    talk: "오늘은 코드 리뷰를 듣는 날이 아니라, diff를 읽고 근거를 검증해 사람 판단과 Draft PR까지 연결하는 서비스를 직접 만듭니다.",
    activity: "오늘 최종 결과물 4종 확인",
    sources: ["local:materials/day3/2026_Day3_강사용_상세교안.md"],
  });
}

async function addPreview() {
  const slide = deck.slides.add();
  addHeader(slide, "완성 서비스 Preview", null, "OPENING · 45초");
  const gif = await assetBytes("assets/demo-videos/day3_service_teaser.gif");
  slide.images.add({
    blob: gif,
    contentType: "image/gif",
    alt: "코드 리뷰 Agent 완성 서비스 시연",
    fit: "contain",
    position: { left: 178, top: 130, width: 924, height: 520 },
    geometry: "rect",
  });
  addNotes(slide, {
    minutes: 2,
    talk: "먼저 완성 화면을 봅니다. 오늘의 모든 이론과 코드는 이 입력·출력 사이의 빈칸을 채우기 위한 것입니다.",
    activity: "자신이 가진 회의 자료가 세 입력 중 어디에 해당하는지 선택",
    sources: ["local:assets/demo-videos/day3_service_teaser.gif"],
  });
}

async function addArchitectureOverview() {
  const slide = deck.slides.add();
  addHeader(slide, "Review Copilot 구조", null, "PRODUCT MAP");
  const image = await assetBytes("assets/demo-videos/day3_boundary.png");
  slide.images.add({
    blob: image,
    contentType: "image/png",
    alt: "Review Copilot의 로컬 분석과 사람 승인 단계",
    fit: "cover",
    crop: { left: 0.01, top: 0.13, right: 0.01, bottom: 0.22 },
    position: { left: 40, top: 138, width: 1200, height: 520 },
    geometry: "rect",
  });
  addShape(slide, "rect", { left: 40, top: 566, width: 1200, height: 108 }, C.white);
  addNotes(slide, {
    minutes: 3,
    talk: "Diff parsing, rule과 모델의 초안, 사람 판단, GitHub 단계의 구분을 먼저 확인합니다.",
    activity: "자동 처리와 사람 판단 단계 확인",
    sources: ["local:assets/demo-videos/day3_boundary.png"],
  });
}

function addSchedule(title, rows) {
  const slide = deck.slides.add();
  addHeader(slide, title, null, "DAY 3 TIMELINE");
  addManualTable(slide, {
    top: 156,
    headers: ["시간", "차시", "핵심 주제", "완료 결과"],
    rows: rows.map((row) => [...row.slice(0, 3), labArtifact(row[3])]),
    widths: [230, 120, 430, 372],
    rowHeight: rows.length > 4 ? 62 : 104,
    fontSize: rows.length > 4 ? S.label : S.table,
  });
  addNotes(slide, {
    minutes: 2,
    talk: `${title}에서 각 차시의 입력과 결과 파일을 연결해 봅니다. 앞 차시 결과가 다음 차시 입력으로 이어집니다.`,
    activity: `${title}의 시간대와 완료 결과 확인`,
    sources: ["local:materials/day3/2026_Day3_강사용_상세교안.md"],
  });
}

function addSetup(title, eyebrow, rows, talk) {
  const slide = deck.slides.add();
  addHeader(slide, title, null, eyebrow);
  const isRequiredLane = eyebrow === "FIXTURE LANE";
  addManualTable(slide, {
    top: isRequiredLane ? 132 : 146,
    headers: ["구분", "Program · 설정", "사용 시점"],
    rows,
    widths: [170, 690, 292],
    rowHeight: isRequiredLane ? 92 : 110,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 3,
    talk,
    activity: "자신의 설치 상태를 필수·선택으로 구분",
    sources: ["local:labs/day3/review_copilot/README.md"],
  });
}

function addLabMap(title, periods) {
  const slide = deck.slides.add();
  addHeader(slide, title, null, "LAB MAP");
  const mapLabels = [
    "Review Contract",
    "Diff Parser",
    "Context Pack",
    "Provider Adapter",
    "Hybrid Review",
    "Human Review",
    "Golden Set",
    "Localhost · PR",
  ];
  const rows = periods.map((period) => [
    `${period.classNumber}차시\n${mapLabels[period.classNumber - 1]}`,
    `${labMapPath(period.fileRoles[1][1])}\n${labMapPath(period.fileRoles[2][1])}`,
    `${period.labATitle}\n${period.labBTitle}\nCodex · ${period.codexTitle.replace("Codex Task · ", "")}`,
    `${labArtifact(period.artifact)}\n${period.mapCheck}`,
  ]);
  addManualTable(slide, {
    top: 150,
    headers: ["차시", "준비 파일", "직접 실행 · Codex Task", "완료 결과"],
    rows,
    widths: [170, 340, 350, 292],
    rowHeight: 198,
    fontSize: S.label,
  });
  addNotes(slide, {
    minutes: 3,
    talk: "표의 각 행은 준비 파일, 직접 실행, Codex 작업, 완료 확인의 순서입니다. PPT만 다시 볼 때도 이 순서로 진행합니다.",
    activity: "자신이 사용할 차시별 파일 경로 표시",
    sources: periods.flatMap((period) => period.sources),
  });
}

function addSectionCover(period) {
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  addShape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  addText(slide, `DAY 3 · ${period.classNumber}차시`, { left: 84, top: 54, width: 500, height: 30 }, { size: S.label, bold: true, color: C.white });
  addText(slide, `${period.time}  (50분)`, { left: 84, top: 102, width: 500, height: 34 }, { size: S.table, bold: true, color: C.blue });
  addText(slide, period.shortTitle, { left: 84, top: 182, width: 1080, height: 112 }, { size: S.sectionTitle, bold: true, color: C.white, valign: "middle" });
  addText(slide, period.subtitle, { left: 88, top: 320, width: 1080, height: 50 }, { size: S.lead, bold: true, color: C.gray300 });
  addShape(slide, "line", { left: 84, top: 414, width: 1092, height: 0 }, "none", C.blue, 4);
  const phases = [
    [period.phaseTimes[0], "핵심 이론"],
    [period.phaseTimes[1], "강사 Demo"],
    [period.phaseTimes[2], "소프트웨어 실습"],
    [period.phaseTimes[3], "Test · Review"],
  ];
  phases.forEach(([time, label], index) => {
    const x = 84 + index * 273;
    addText(slide, time, { left: x, top: 456, width: 240, height: 28 }, { size: S.label, bold: true, color: C.gray300 });
    addText(slide, label, { left: x, top: 500, width: 240, height: 56 }, { size: S.table, bold: true, color: C.white });
  });
  addText(slide, `완료 결과 · ${period.artifact}`, { left: 84, top: 624, width: 1092, height: 34 }, { size: S.table, bold: true, color: C.white, align: "right" });
  addNotes(slide, {
    minutes: 1,
    talk: `이번 차시는 ${period.focus}을 다룹니다. 마지막에는 ${period.artifact}을 직접 확인합니다.`,
    activity: "차시 종료 시 남길 파일과 Test 확인",
    sources: period.sources,
  });
}

function addFocus(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.focusTitle, period, "CORE IDEA");
  addText(slide, period.focus, { left: 104, top: 180, width: 1072, height: 112 }, { size: S.lead, bold: true, color: C.ink, align: "center", valign: "middle" });
  addShape(slide, "line", { left: 352, top: 330, width: 576, height: 0 }, "none", C.blue, 4);
  addText(slide, "핵심 관점", { left: 480, top: 378, width: 320, height: 34 }, { size: S.label, bold: true, color: C.muted, align: "center" });
  addText(slide, period.why, { left: 144, top: 432, width: 992, height: 128 }, { size: S.body, bold: true, color: C.ink, align: "center", valign: "middle" });
  addNotes(slide, {
    minutes: 2,
    talk: `핵심은 ${period.focus}입니다. 이 기준이 없으면 ${period.failure}`,
    activity: "현재 업무에서 비슷한 문제 한 가지 메모",
    sources: period.sources,
  });
}

function addConceptMap(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.conceptTitle, period, "CONCEPT-TO-CODE MAP");
  const rows = period.terms.map(([term, meaning], index) => [
    term,
    meaning,
    period.conceptFiles[index] ?? period.artifact,
  ]);
  addManualTable(slide, {
    top: 150,
    headers: ["용어", "수업에서의 의미", "Code · File"],
    rows,
    widths: [230, 400, 522],
    rowHeight: 102,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 3,
    talk: "용어를 외우기보다 실제 코드의 어느 부분과 연결되는지 함께 보겠습니다.",
    activity: "각 용어와 File Role 연결",
    sources: period.sources,
  });
}

function addProcess(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.processTitle, period, "ARCHITECTURE");
  const values = period.pipeline.slice(0, 5);
  values.slice(0, -1).forEach((_, index) => {
    addShape(slide, "line", { left: 202 + index * 226, top: 300, width: 118, height: 0 }, "none", C.black, 2);
  });
  values.forEach((value, index) => {
    const x = 70 + index * 226;
    addText(slide, String(index + 1).padStart(2, "0"), { left: x, top: 190, width: 84, height: 48 }, { size: S.lead, bold: true, color: C.ink });
    addShape(slide, "rect", { left: x, top: 260, width: 190, height: 150 }, C.gray025, C.faint, 1);
    addText(slide, value, { left: x + 16, top: 292, width: 158, height: 88 }, { size: S.table, bold: true, color: C.ink, align: "center", valign: "middle" });
  });
  addText(slide, `OUTPUT · ${period.artifact}`, { left: 180, top: 500, width: 920, height: 52 }, { size: S.body, bold: true, color: C.ink, align: "center" });
  addNotes(slide, {
    minutes: 3,
    talk: `입력에서 ${period.artifact}까지 흐름을 왼쪽부터 읽습니다. 모델이 필요한 단계와 코드로 고정할 단계를 구분해 보세요.`,
    activity: "모델 판단이 필요한 Node 표시",
    sources: period.sources,
  });
}

function addDecisionTable(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.decisionTitle, period, "DECISION TABLE");
  addManualTable(slide, {
    top: 162,
    headers: period.classNumber === 7
      ? ["Decision", "처리 결과", "외부 반영"]
      : ["상황", "선택", "이유 · Check"],
    rows: period.decisions,
    widths: [320, 350, 482],
    rowHeight: period.decisions.length === 4 ? 96 : 118,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 3,
    talk: "무조건 상위 모델을 쓰는 대신, 입력과 반복성, 권한을 기준으로 선택합니다.",
    activity: "자신의 업무 상황을 표의 한 행에 연결",
    sources: period.sources,
  });
}

function addFileAndSetup(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.filesTitle, period, "PREP · FILE ROLE");
  addManualTable(slide, {
    top: 146,
    headers: ["Role", "경로 · 준비 항목"],
    rows: period.fileRoles,
    widths: [230, 922],
    rowHeight: 82,
    fontSize: S.table,
  });
  addText(slide, "실행 전 Check", { left: 68, top: 556, width: 210, height: 32 }, { size: S.label, bold: true, color: C.muted });
  addText(slide, `Notebook Kernel · ${period.label} · ${period.artifact}`, { left: 278, top: 544, width: 916, height: 64 }, { size: S.label, bold: true, color: C.ink, valign: "middle" });
  addNotes(slide, {
    minutes: 2,
    talk: "PPT를 다시 볼 때는 이 장표가 시작점입니다. 읽을 파일, 실행할 파일, 수정할 코드, 확인할 Test를 구분합니다.",
    activity: "네 경로를 VS Code에서 열기",
    sources: period.fileRoles.map(([, file]) => `local:${file}`),
  });
}

async function addDemoScreen(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.demoTitle, period, "INSTRUCTOR DEMO");
  if (period.classNumber === 1) {
    addManualTable(slide, {
      top: 158,
      headers: ["요청", "선택 방식", "선택 이유"],
      rows: [
        ["회의 요약·To Do", "Workflow", "반복 순서 고정"],
        ["Notion·Slack 맥락 검색", "Agent Router", "자료·도구 선택 필요"],
        ["자동 메일 발송", "Human Review", "승인 전 실행 차단"],
      ],
      widths: [390, 300, 462],
      rowHeight: 126,
      fontSize: S.table,
    });
    addNotes(slide, {
      minutes: 2,
      talk: "같은 회의 요청이라도 한 번의 생성, 고정 절차, 도구 선택, 외부 반영은 서로 다른 실행 방식입니다.",
      activity: "세 요청의 선택 방식과 승인 위치 확인",
      sources: period.sources,
    });
    return;
  }
  if (period.classNumber === 2) {
    addShape(slide, "rect", { left: 72, top: 154, width: 596, height: 456 }, C.black);
    addText(slide, `$ FASTER_WHISPER_LIVE_OPT_IN=1
  # 공개 음성 75초 Demo

{
  "status": "SUCCESS",
  "provider": "faster-whisper",
  "model": "small",
  "duration_seconds": 75.0,
  "segment_count": 13,
  "first_segment_id": "s01",
  "word_timestamps": true,
  "transcript_substituted": false
}`, { left: 98, top: 180, width: 544, height: 408 }, {
      size: S.code, allowSmall: true, color: C.white, typeface: MONO, lineSpacing: 1.0,
    });
    addManualTable(slide, {
      left: 708,
      top: 176,
      headers: ["실행 경로", "사용 시점"],
      rows: [
        ["Reviewed Fixture", "기본 Run All\nNetwork 0회 · 재현 우선"],
        ["Live faster-whisper", "명시적 Opt-in\n실제 음질·오인식 검토"],
      ],
      widths: [248, 252],
      rowHeight: 138,
      fontSize: S.label,
    });
    addText(slide, "첫 문장의 오인식 가능성도 성공 결과에 포함해 사람이 확인", { left: 738, top: 520, width: 440, height: 74 }, { size: S.label, bold: true, color: C.ink, align: "center", valign: "middle" });
    addNotes(slide, {
      minutes: 2,
      talk: "왼쪽은 강사 PC에서 공개 음성 75초를 실제 faster-whisper small로 처리한 결과입니다. 실행 성공과 전사 정확도는 별개이므로 첫 Segment도 함께 검토합니다.",
      activity: "Fixture와 Live STT의 목적·성공 기준 비교",
      sources: ["local:output/course-labs/day3-v2/02_local_stt_75s_reference.json", ...period.sources],
    });
    return;
  }
  if (period.classNumber === 3) {
    addManualTable(slide, {
      top: 154,
      headers: ["Connector", "허용 범위", "실행 상태", "외부 저장·발송"],
      rows: [
        ["Notion", "최근 14일 · CX PoC", "PLAN_ONLY", "false"],
        ["Confluence", "CX PoC Project", "PLAN_ONLY", "false"],
        ["Slack", "#cx-poc Channel", "PLAN_ONLY", "false"],
      ],
      widths: [240, 430, 270, 212],
      rowHeight: 126,
      fontSize: S.table,
    });
    addNotes(slide, {
      minutes: 2,
      talk: "MCP 실습은 사이트 구경이 아니라 Connector, 기간, Scope, 최대 개수를 가진 읽기 계획을 코드로 만드는 과정입니다.",
      activity: "세 Connector가 실행되지 않고 계획으로만 남는지 확인",
      sources: period.sources,
    });
    return;
  }
  if (period.classNumber === 4) {
    const recordPreview = `{
  "meeting_summary": "배송 지연 자동화 범위 합의",
  "summary_evidence_ids": ["s003"],
  "todos": [{
    "owner": null,
    "due_date": null,
    "evidence_ids": ["s006"]
  }],
  "human_review_required": true,
  "external_write": false
}`;
    addShape(slide, "rect", { left: 72, top: 154, width: 650, height: 448 }, C.black);
    addText(slide, recordPreview, { left: 100, top: 180, width: 596, height: 392 }, {
      size: S.code, color: C.white, typeface: MONO, lineSpacing: 1.02,
    });
    addText(slide, "별도 오류 입력", { left: 760, top: 180, width: 420, height: 34 }, { size: S.label, bold: true, color: C.muted });
    addShape(slide, "rect", { left: 760, top: 236, width: 448, height: 164 }, C.gray025, C.faint, 1);
    addText(slide, "s999", { left: 790, top: 270, width: 388, height: 42 }, { size: S.lead, bold: true, color: C.ink, typeface: MONO });
    addText(slide, "TODO_1_UNKNOWN_EVIDENCE", { left: 790, top: 328, width: 388, height: 48 }, { size: S.code, bold: true, color: C.ink, typeface: MONO });
    addText(slide, "확인 원칙", { left: 760, top: 448, width: 420, height: 34 }, { size: S.label, bold: true, color: C.muted });
    addText(slide, "모르는 값은 null\n사실 Field는 Segment ID 필수", { left: 760, top: 500, width: 448, height: 88 }, { size: S.table, bold: true, color: C.ink });
    addNotes(slide, {
      minutes: 2,
      talk: "왼쪽은 통과하는 MeetingRecord, 오른쪽은 존재하지 않는 근거 ID를 넣었을 때의 실제 Error Code입니다.",
      activity: "s003·s006과 오류용 s999의 차이 확인",
      sources: period.sources,
    });
    return;
  }
  if (period.statusDemoRows) {
    addManualTable(slide, {
      top: 156,
      headers: ["Provider", "현재 상태", "수업 경로"],
      rows: period.statusDemoRows,
      widths: [320, 260, 572],
      rowHeight: 102,
      fontSize: S.table,
    });
    addNotes(slide, {
      minutes: 2,
      talk: period.classNumber === 6
        ? "기본 Run All은 Fixture로 재현하고, 강사 PC의 qwen3:4b Live 실행은 JSON·Thinking·줄바꿈 옵션을 고정한 뒤 Schema와 Evidence를 모두 통과했습니다."
        : "Provider 이름보다 현재 설치·Opt-in·Fallback 상태를 먼저 확인합니다. 표는 강사 PC의 Preflight 결과입니다.",
      activity: "자신의 Fixture·Local·Live 경로 선택",
      sources: period.classNumber === 6
        ? ["local:output/course-labs/day3-v2/06_ollama_qwen3_4b_reference.json", ...period.sources]
        : period.sources,
    });
    return;
  }
  const image = await assetBytes(`assets/screenshots/${period.image}`);
  if (period.classNumber === 5) {
    slide.images.add({
      blob: image, contentType: "image/png", alt: "Codex Task Spec, Diff, Test, Human Review 순서",
      fit: "contain",
      position: { left: 178, top: 136, width: 924, height: 520 }, geometry: "rect",
    });
    addNotes(slide, {
      minutes: 2,
      talk: "왼쪽은 사람이 준 Goal과 Expected Error, 오른쪽은 Codex가 확인한 Diff, Test, Error Code이며 마지막 판단은 사람에게 남습니다.",
      activity: "Goal·Test·Expected Error·Human Merge Decision 확인",
      sources: [`local:assets/screenshots/${period.image}`, ...period.sources],
    });
    return;
  }
  if (period.classNumber === 7) {
    addText(slide, "Decision", { left: 74, top: 148, width: 280, height: 30 }, { size: S.label, bold: true, color: C.muted });
    addText(slide, "Interrupt Payload", { left: 690, top: 148, width: 300, height: 30 }, { size: S.label, bold: true, color: C.muted });
    slide.images.add({
      blob: image, contentType: "image/png", alt: "Approve, Edit, Reject 실제 실행 화면",
      fit: "contain",
      position: { left: 72, top: 184, width: 574, height: 323 }, geometry: "rect",
    });
    ["승인", "수정", "거절"].forEach((label, index) => {
      const left = 80 + (index * 184);
      addShape(slide, "roundRect", { left, top: 520, width: 168, height: 50 }, index === 0 ? C.black : C.gray025, C.faint, 1);
      addText(slide, label, { left, top: 530, width: 168, height: 30 }, { size: S.label, bold: true, color: index === 0 ? C.white : C.ink, align: "center" });
    });
    addShape(slide, "roundRect", { left: 80, top: 584, width: 536, height: 46 }, C.blue);
    addText(slide, "이 결정으로 재개", { left: 80, top: 592, width: 536, height: 30 }, { size: S.label, bold: true, color: C.white, align: "center" });
    addShape(slide, "rect", { left: 678, top: 184, width: 530, height: 446 }, C.black);
    addText(slide, `{
  "decision": "approve",
  "options": [
    "approve", "edit", "reject"
  ],
  "evidence_ids": ["s12", "s18"],
  "approval_required": true,
  "automatic_email": false
}`, { left: 710, top: 216, width: 466, height: 382 }, {
      size: S.code, color: C.white, typeface: MONO, lineSpacing: 1.02,
    });
    addNotes(slide, {
      minutes: 2,
      talk: "왼쪽의 Approve·Edit·Reject와 오른쪽의 Interrupt Payload를 한 화면에서 연결해 확인합니다.",
      activity: "Decision Button과 evidence_ids·options Field 확인",
      sources: [`local:assets/screenshots/${period.image}`, ...period.sources],
    });
    return;
  }
  if (period.classNumber === 8) {
    addText(slide, "실제 localhost 화면 · 이메일 초안", { left: 72, top: 142, width: 600, height: 30 }, { size: S.label, bold: true, color: C.muted });
    slide.images.add({
      blob: image, contentType: "image/png", alt: "Local App Workflow와 Email Draft 화면",
      fit: "cover",
      position: { left: 72, top: 176, width: 1136, height: 424 }, geometry: "rect",
    });
    addShape(slide, "rect", { left: 72, top: 600, width: 1136, height: 42 }, C.black);
    addText(slide, "받는 사람 직접 입력 · 자동 발송 없음 · 외부 저장 없음", { left: 96, top: 607, width: 1088, height: 28 }, {
      size: S.label, bold: true, color: C.white, align: "center",
    });
    addNotes(slide, {
      minutes: 2,
      talk: "실제 Localhost 화면에서 이메일 초안과 자동 발송 없음 문구를 크게 확인합니다. 실행 상태 값은 161쪽 결과 파일에서 다시 검증합니다.",
      activity: "이메일 초안·자동 발송 없음·사람 확인 문구 확인",
      sources: [`local:assets/screenshots/${period.image}`, ...period.sources],
    });
    return;
  }
  if (period.fullScreenDemo) {
    slide.images.add({
      blob: image,
      contentType: "image/png",
      alt: period.demoTitle,
      fit: "contain",
      position: { left: 160, top: 132, width: 960, height: 540 },
      geometry: "rect",
    });
    addNotes(slide, {
      minutes: 2,
      talk: `화면에서 ${period.demo.join(", ")} 순서로 상태 변화를 확인합니다. 다음 장표에서 같은 입력과 명령을 재현합니다.`,
      activity: "화면의 입력·상태·결과 위치 확인",
      sources: [`local:assets/screenshots/${period.image}`, ...period.sources],
    });
    return;
  }
  slide.images.add({
    blob: image,
    contentType: "image/png",
    alt: period.demoTitle,
    fit: "contain",
    position: { left: 560, top: 142, width: 640, height: 432 },
    geometry: "rect",
  });
  addText(slide, "화면에서 볼 것", { left: 72, top: 166, width: 330, height: 34 }, { size: S.label, bold: true, color: C.muted });
  addNumberedRows(slide, period.demo, { top: 222, rowHeight: 112, bodySize: S.table });
  const demoRowCount = period.demo.length;
  const demoShapes = slide.shapes.items.slice(-(demoRowCount * 3));
  demoShapes.forEach((shape, shapeIndex) => {
    if (!shape.position) return;
    const column = shapeIndex % 3;
    if (column === 0) shape.position.left = 72;
    if (column === 1) shape.position.left = 142;
    if (column === 2) {
      shape.position.left = 202;
      shape.position.width = 320;
    }
  });
  addNotes(slide, {
    minutes: 2,
    talk: `먼저 강사가 ${period.demo.join(", ")} 순서로 보여드립니다. 이후 같은 경로를 직접 실행합니다.`,
    activity: "입력·명령·출력 위치만 먼저 확인",
    sources: [`local:assets/screenshots/${period.image}`, ...period.sources],
  });
}

async function addDay3DemoScreen(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.demoTitle, period, "INSTRUCTOR DEMO");

  if (period.classNumber === 4) {
    addManualTable(slide, {
      top: 164,
      headers: ["Provider", "실행 조건", "결과 표시", "수업 경로"],
      rows: [
        ["Fixture", "조건 없음", "provider_used=fixture", "전원 필수"],
        ["Ollama", "localhost + opt-in", "used 또는 fallback_reason", "선택"],
        ["OpenAI", "API secret + opt-in", "used 또는 fallback_reason", "강사 선택"],
        ["호출 실패", "timeout · schema 오류", "EXPECTED_FAILURE", "원인 기록"],
      ],
      widths: [220, 350, 350, 232],
      rowHeight: 96,
      fontSize: S.table,
    });
    addShape(slide, "rect", { left: 80, top: 614, width: 1136, height: 40 }, C.black);
    addText(slide, "Fixture 기본 · 실제 사용 경로와 fallback 이유 공개", { left: 100, top: 620, width: 1096, height: 28 }, {
      size: S.label, bold: true, color: C.white, align: "center",
    });
    addNotes(slide, {
      minutes: 2,
      talk: "Fixture, Ollama, OpenAI는 결과 계약이 같고 실행 조건만 다릅니다. 실제 사용 경로와 fallback 이유를 숨기지 않습니다.",
      activity: "자신의 실행 경로 한 행 선택",
      sources: period.sources,
    });
    return;
  }

  if (period.classNumber === 5) {
    addManualTable(slide, {
      top: 164,
      headers: ["후보", "출처", "Diff 근거", "결과"],
      rows: [
        ["eval(action)", "Rule", "line 7", "P0 유지"],
        ["requests.post", "Rule + LLM", "line 9", "P1 한 건"],
        ["except Exception", "Rule", "line 10", "P2 유지"],
        ["존재하지 않는 line", "LLM", "line 999", "제외"],
      ],
      widths: [330, 270, 270, 282],
      rowHeight: 96,
      fontSize: S.table,
    });
    addShape(slide, "rect", { left: 80, top: 614, width: 1136, height: 40 }, C.black);
    addText(slide, "P0·P1·P2 세 finding · 실제 added line 근거", { left: 100, top: 620, width: 1096, height: 28 }, {
      size: S.label, bold: true, color: C.white, align: "center",
    });
    addNotes(slide, {
      minutes: 2,
      talk: "Rule과 모델 후보를 합친 뒤, 같은 finding은 한 건만 남기고 diff에 없는 line 999는 제외합니다.",
      activity: "유지·중복 제거·제외 기준 확인",
      sources: period.sources,
    });
    return;
  }

  if (period.classNumber === 7) {
    const metrics = [
      ["Golden", "8/8"], ["TP", "7"], ["FP", "0"], ["FN", "0"],
      ["Precision", "1.0"], ["Recall", "1.0"], ["F1", "1.0"], ["Expected failure", "1/1"],
    ];
    metrics.forEach(([label, value], index) => {
      const column = index % 4;
      const row = Math.floor(index / 4);
      const left = 80 + column * 286;
      const top = 170 + row * 190;
      addShape(slide, "roundRect", { left, top, width: 258, height: 160 }, C.white, C.faint, 1);
      addText(slide, label, { left: left + 22, top: top + 22, width: 214, height: 28 }, {
        size: S.label, bold: true, color: C.muted, align: "center",
      });
      addText(slide, value, { left: left + 22, top: top + 66, width: 214, height: 64 }, {
        size: S.sectionTitle, bold: true, color: C.ink, align: "center", valign: "middle",
      });
    });
    addShape(slide, "rect", { left: 80, top: 574, width: 1136, height: 58 }, C.black);
    addText(slide, "Release Gate · READY", { left: 100, top: 586, width: 1096, height: 34 }, {
      size: S.table, bold: true, color: C.white, align: "center",
    });
    addNotes(slide, {
      minutes: 2,
      talk: "8개 case와 예상 실패까지 모두 통과했습니다. 많이 지적하는 것이 아니라 FP와 FN을 함께 줄이는 것이 목표입니다.",
      activity: "TP·FP·FN과 READY 기준 확인",
      sources: period.sources,
    });
    return;
  }

  const imageFolders = new Map([
    [1, "assets/demo-videos/day3_overview.png"],
    [2, "assets/demo-videos/day3_pipeline.png"],
    [3, "assets/screenshots/vscode-repo-workspace-local.png"],
    [4, "assets/screenshots/ollama-langchain-provider-local.png"],
    [5, "assets/screenshots/vscode-pytest-19-passed-local.png"],
    [6, "assets/screenshots/langgraph-interrupt-demo-local.png"],
    [7, "assets/demo-videos/day3_result.png"],
    [8, "assets/screenshots/day3-review-copilot-local.png"],
  ]);
  const imagePath = imageFolders.get(period.classNumber);
  const image = await assetBytes(imagePath);
  const fullScreen = period.classNumber === 6 || period.classNumber === 8;

  if (fullScreen) {
    slide.images.add({
      blob: image,
      contentType: "image/png",
      alt: period.demoTitle,
      fit: period.classNumber === 8 ? "cover" : "contain",
      position: { left: 80, top: 132, width: 1120, height: 514 },
      geometry: "rect",
    });
  } else {
    slide.images.add({
      blob: image,
      contentType: "image/png",
      alt: period.demoTitle,
      fit: "contain",
      position: { left: 548, top: 144, width: 650, height: 430 },
      geometry: "rect",
    });
    addText(slide, "화면 확인", { left: 72, top: 158, width: 340, height: 34 }, {
      size: S.label, bold: true, color: C.muted,
    });
    addNumberedRows(slide, period.demo, {
      top: 214,
      rowHeight: 112,
      bodySize: S.table,
      numberLeft: 72,
      lineLeft: 132,
      bodyLeft: 192,
      bodyWidth: 320,
    });
  }
  addShape(slide, "rect", { left: 72, top: 610, width: 1136, height: 42 }, C.black);
  addText(slide, period.mapCheck, { left: 92, top: 617, width: 1096, height: 28 }, {
    size: S.label, bold: true, color: C.white, align: "center",
  });
  addNotes(slide, {
    minutes: 2,
    talk: `강사가 먼저 ${period.demo.join(", ")} 순서로 실행합니다. 화면의 성공 상태와 외부 서비스 변경 차단을 확인한 뒤 같은 경로를 직접 재현합니다.`,
    activity: "입력·실행·결과 위치 확인",
    sources: [`local:${imagePath}`, ...period.sources],
  });
}

function addDemoSteps(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} Demo Steps`, period, "INPUT · RUN · OUTPUT");
  const rows = period.classNumber === 8
    ? [
      `실행\n${terminalCommand(period.demoCommand)}`,
      "브라우저\nhttp://127.0.0.1:8765",
      "분석\n샘플 자동 로드 · 분석 · 전체 유지",
      "확인·종료\nAPPROVED · DRY_RUN_READY · Terminal Ctrl+C",
    ]
    : [
      `입력\n${period.fileRoles[0][1]}`,
      `실행\n${terminalCommand(period.demoCommand ?? period.command)}`,
      `확인\n${period.resultChecks[0]} · ${period.resultChecks[1]}`,
      "실패 조건\n예상 오류 Case 실행",
    ];
  addNumberedRows(slide, rows, { top: 162, rowHeight: 112, bodySize: S.table });
  addNotes(slide, {
    minutes: 2,
    talk: "Demo는 입력, 실행, 기대 결과, 예상 오류의 네 화면만 봅니다. 이후 같은 경로를 직접 재현합니다.",
    activity: "자신의 화면에서 같은 File 위치 확인",
    sources: period.sources,
  });
}

function addCommand(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} Test 명령`, period, "TERMINAL");
  addShape(slide, "rect", { left: 72, top: 182, width: 1136, height: 230 }, C.black);
  addText(slide, "$", { left: 110, top: 260, width: 40, height: 42 }, { size: S.lead, bold: true, color: C.blue });
  addText(slide, terminalCommand(period.command), { left: 172, top: 226, width: 966, height: 112 }, { size: S.body, bold: true, color: C.white, typeface: MONO, valign: "middle" });
  addManualTable(slide, {
    top: 466,
    headers: ["실행 위치", "보안 확인", "Test 뒤 확인"],
    rows: [["Repository root", ".env · Key 출력 없음", labArtifact(period.artifact)]],
    widths: [360, 360, 432],
    rowHeight: 86,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 1,
    talk: "명령을 복사하기 전에 Terminal의 현재 폴더와 활성 Python 환경부터 확인합니다.",
    activity: "명령 복사·실행",
    sources: period.sources,
  });
}

async function addResult(period, periodIndex) {
  const slide = deck.slides.add();
  const result = await resultPreview(periodIndex);
  addHeader(slide, `${period.label} 검증 요약`, period, `RESULT CHECK · ${result.fileName}`);
  addShape(slide, "rect", { left: 72, top: 150, width: 690, height: 454 }, C.black);
  addText(slide, result.text, { left: 96, top: 174, width: 642, height: 404 }, { size: S.code, color: C.white, typeface: MONO, lineSpacing: 1.02 });
  addText(slide, "결과 파일에서 확인한 값", { left: 790, top: 176, width: 390, height: 34 }, { size: S.label, bold: true, color: C.muted });
  addNumberedRows(slide, period.resultChecks, {
    top: 230,
    rowHeight: 82,
    bodySize: S.table,
    numberLeft: 780,
    lineLeft: 828,
    bodyLeft: 850,
    bodyWidth: 358,
  });
  addNotes(slide, {
    minutes: 2,
    talk: "왼쪽은 저장된 결과 파일에서 계산한 검증 요약입니다. 오른쪽 네 항목을 확인하고 원본 구조는 Notebook에서 검색합니다.",
    activity: `자신의 ${result.fileName}에서 네 Field 찾기`,
    sources: [`local:${path.relative(ROOT, result.filePath)}`],
  });
}

function addNotebook(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} Notebook`, period, "HANDS-ON");
  addText(slide, "materials/day3/day3_review_intelligence_lab.ipynb", { left: 72, top: 136, width: 1136, height: 30 }, { size: S.label, bold: true, color: C.muted, typeface: MONO });
  addShape(slide, "rect", { left: 72, top: 174, width: 1136, height: 432 }, C.black);
  addText(slide, notebookCode(periodIndex), { left: 100, top: 196, width: 1080, height: 390 }, { size: period.classNumber === 1 ? 21 : S.code, allowSmall: true, color: C.white, typeface: MONO, lineSpacing: 0.98 });
  addText(slide, `결과 저장 · ${period.saveLine}`, { left: 90, top: 614, width: 1100, height: 32 }, { size: S.label, bold: true, color: C.ink, typeface: MONO, align: "center" });
  addNotes(slide, {
    minutes: 2,
    talk: "화면의 코드는 실행 Cell의 핵심 13줄입니다. 전체 Cell은 Notebook에서 실행하고, PPT에서는 변수와 출력 위치만 확인합니다.",
    activity: `Notebook ${period.classNumber}차시 Cell 실행`,
    sources: ["local:materials/day3/day3_review_intelligence_lab.ipynb"],
  });
}

function addCodexTask(period) {
  const slide = deck.slides.add();
  addHeader(slide, period.codexTitle, period, "COPY-READY TASK SPEC");
  addManualTable(slide, {
    top: 152,
    headers: ["항목", "Codex에 전달할 내용"],
    rows: [
      ["Goal", period.codexPrompt[0]],
      ["Allowed", period.codexPrompt[1]],
      ["Test", period.codexPrompt[2]],
      ["Do not", period.codexPrompt[3]],
    ],
    widths: [210, 942],
    rowHeight: 100,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 2,
    talk: "Codex에는 ‘알아서 만들어줘’ 대신 Goal, Allowed, Test, Do not을 한 번에 전달합니다.",
    activity: "표의 오른쪽 내용을 자신의 Codex Task에 복사",
    sources: ["local:AGENTS.md", ...period.sources],
  });
}

function addCodexConversation(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} Codex 대화`, period, "PLAN · PATCH · TEST · REVIEW");
  addNumberedRows(slide, [
    `분석\n${period.fileRoles[2][1]}의 현재 Role과 영향 파일`,
    `계획\n${period.label} 허용 범위·Test 우선순위`,
    `실행\n${terminalCommand(period.command)}`,
    `Review\ngit diff · ${period.artifact}`,
  ], { top: 160, rowHeight: 112, bodySize: S.table });
  addNotes(slide, {
    minutes: 2,
    talk: `${period.label} 작업은 분석, 계획, 실행, Review의 네 Turn으로 나눕니다. ${period.fileRoles[2][1]}의 영향 범위와 ${period.artifact} 생성 여부를 함께 확인합니다.`,
    activity: `Codex가 제안한 영향 파일·Test와 ${period.artifact} 확인`,
    sources: ["https://developers.openai.com/codex/cli", "local:materials/day3/2026_Day3_수강생_실습가이드.md"],
  });
}

function addHandsOn(period, title, steps, minutes, phase) {
  const slide = deck.slides.add();
  addHeader(slide, title, period, `HANDS-ON · ${phase}`);
  addNumberedRows(slide, steps, { top: 168, rowHeight: 120, bodySize: S.body });
  addShape(slide, "rect", { left: 176, top: 548, width: 928, height: 54 }, C.gray025, C.faint, 1);
  addText(slide, `${period.label} · ${phase} 실행 로그`, { left: 204, top: 560, width: 872, height: 30 }, { size: S.table, bold: true, color: C.ink, align: "center" });
  addNotes(slide, {
    minutes,
    talk: "이제 설명을 멈추고 화면의 세 단계를 직접 실행합니다. 막히면 오류 첫 줄과 현재 단계 번호만 확인합니다.",
    activity: steps.join(" → "),
    sources: period.fileRoles.map(([, file]) => `local:${file}`),
  });
}

function addTestCriteria(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} 성공·오류 기준`, period, "TEST RESULT");
  const externalState = period.externalState === "APPROVAL_REQUIRED"
    ? "Human Review 대기"
    : period.externalState;
  const rows = [
    ["예상 완료", period.success, "실행 계속"],
    ["예상 오류", period.expectedError, "원인 확인"],
    ["외부 저장·발송", period.externalRule, externalState],
    ["Execution Log", `status · error_code · ${period.artifact}`, "재현 가능"],
  ];
  addManualTable(slide, {
    top: 154,
    headers: ["Case", "확인 내용", "다음 상태"],
    rows,
    widths: [250, 602, 300],
    rowHeight: 104,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 3,
    talk: "오류는 수업 실패가 아니라 예상된 제품 상태입니다. Happy Path와 Expected Error를 모두 재현해야 완료입니다.",
    activity: "두 Case의 Test 결과 비교",
    sources: period.sources,
  });
}

function addRecovery(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} 오류 복구`, period, "FAILURE HANDLING");
  addNumberedRows(slide, period.recovery, { top: 160, rowHeight: 112, bodySize: S.body });
  addNotes(slide, {
    minutes: 2,
    talk: "복구는 다시 설치부터 시작하지 않습니다. 입력, 설정, 실행 위치, 결과 Field 순서로 좁혀갑니다.",
    activity: "현재 오류를 네 단계 중 하나로 분류",
    sources: period.sources,
  });
}

function addApplications(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} 활용`, period, "APPLICATION");
  addManualTable(slide, {
    top: 176,
    headers: ["관점", "남길 결과", "설명할 핵심"],
    rows: period.applications.map(([audience, result]) => [
      audience,
      result,
      audience === "재직자"
        ? `${period.label} 업무 오류·승인 위치`
        : `${period.label} Code·Test·결과`,
    ]),
    widths: [200, 620, 332],
    rowHeight: 154,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 2,
    talk: "재직자는 업무 개선 근거, 구직자는 재현 가능한 제작 근거를 중심으로 같은 결과를 설명합니다.",
    activity: "자신에게 맞는 한 열 선택",
    sources: period.sources,
  });
}

function addReplay(period) {
  const slide = deck.slides.add();
  addHeader(slide, `${period.classNumber}차시 재실행`, period, "SELF-PACED REPLAY");
  addNumberedRows(slide, [
    `준비 파일\n${period.fileRoles[1][1]}`,
    `실행\n${terminalCommand(period.replayCommand ?? period.command)}`,
    `확인\n${period.artifact} · ${period.success}`,
    `Codex Task\n${period.codexPrompt[0]}`,
  ], { top: 154, rowHeight: 112, bodySize: S.table });
  addNotes(slide, {
    minutes: 2,
    talk: "수업 후에는 이 한 장을 시작점으로 File, 명령, Output, Codex Task 순서로 다시 실행합니다.",
    activity: "다시 실행할 첫 File 표시",
    sources: period.sources,
  });
}

function addVariationChallenge(period) {
  const challenges = [
    ["Severity 변경", "팀의 P1 기준 한 줄 수정", "잘못된 severity 입력", "Contract Test"],
    ["Hunk 변형", "새 파일 diff 한 건 추가", "../ 경로 diff", "Line Mapping Test"],
    ["Budget 축소", "max_bytes를 20으로 설정", "private_* field 추가", "CONTEXT_BUDGET_EXCEEDED"],
    ["Provider 실패", "UnavailableReviewProvider 주입", "allow_fallback=false", "provenance 비교"],
    ["후보 중복", "같은 path·line·rule_id 두 번 입력", "line=999 후보", "3개 finding 유지"],
    ["사람 수정", "Edit로 finding 문구 변경", "알 수 없는 decision", "세 terminal state"],
    ["지표 미달", "TP=7·FP=1·FN=1 입력", "safe-negative finding 가정", "F1=0.875·HOLD"],
    ["PR Contract", "Review focus를 비운 Draft PR", ".env 변경 경로", "안정 error code"],
  ][period.classNumber - 1];
  const slide = deck.slides.add();
  addHeader(slide, `${period.label} 확장 과제`, period, "VARIATION CHALLENGE");
  addManualTable(slide, {
    top: 180,
    headers: ["변형", "직접 바꿀 값", "실패 조건", "확인"],
    rows: [challenges],
    widths: [230, 360, 330, 232],
    rowHeight: 190,
    fontSize: S.table,
  });
  addShape(slide, "rect", { left: 180, top: 500, width: 920, height: 70 }, C.gray025, C.faint, 1);
  addText(slide, `${period.label} 원본 Cell → 값 한 개 변경 → 결과 비교 → 원복`, { left: 210, top: 516, width: 860, height: 38 }, {
    size: S.table, bold: true, color: C.ink, align: "center",
  });
  addNotes(slide, {
    minutes: 2,
    talk: "기본 예시를 그대로 반복하지 않고 값 한 개만 바꿔 제품의 허용 범위를 확인합니다. 결과를 비교한 뒤 원본 상태로 복구합니다.",
    activity: challenges.join(" → "),
    sources: period.sources,
  });
}

function addCompletion(period, nextPeriod) {
  const slide = deck.slides.add();
  addHeader(slide, period.completionTitle, period, "EXIT CHECK");
  addNumberedRows(slide, period.completion, { top: 180, rowHeight: 120, bodySize: S.body });
  addShape(slide, "line", { left: 320, top: 548, width: 640, height: 0 }, "none", C.black, 2);
  addText(slide, nextPeriod ? `다음 연결 · ${nextPeriod.shortTitle}` : "다음 연결 · Q&A와 전체 복구", { left: 160, top: 584, width: 960, height: 42 }, { size: S.table, bold: true, color: C.ink, align: "center" });
  addNotes(slide, {
    minutes: 2,
    talk: `세 항목이 모두 확인되면 ${period.classNumber}차시 완료입니다. 결과 파일은 다음 차시의 입력으로 이어집니다.`,
    activity: "세 항목 체크",
    sources: period.sources,
  });
}

async function buildPeriod(period, periodIndex) {
  addSectionCover(period);                              // 1
  addFocus(period);                                     // 2
  addConceptMap(period);                                // 3
  addProcess(period);                                   // 4
  addDecisionTable(period);                             // 5
  addFileAndSetup(period);                              // 6
  await addDay3DemoScreen(period);                      // 7
  addDemoSteps(period);                                 // 8
  addCommand(period);                                   // 9
  await addResult(period, periodIndex);                 // 10
  addNotebook(period, periodIndex);                     // 11
  addCodexTask(period);                                 // 12
  addCodexConversation(period);                         // 13
  addHandsOn(period, period.labATitle, period.labA, 6, "BUILD A"); // 14
  addHandsOn(period, period.labBTitle, period.labB, 6, "BUILD B"); // 15
  addTestCriteria(period);                              // 16
  addRecovery(period);                                  // 17
  addApplications(period);                              // 18
  addVariationChallenge(period);                        // 19
  addCompletion(period, DAY3_STUDENT_PERIODS[periodIndex + 1]); // 20
}

function addArtifactMap(title, periods) {
  const slide = deck.slides.add();
  addHeader(slide, title, null, "DAY 3 OUTPUT");
  addManualTable(slide, {
    top: 156,
    headers: ["차시", "결과 파일", "확인 내용"],
    rows: periods.map((period) => [
      `${period.classNumber}차시`,
      labArtifact(period.artifact),
      `${period.resultChecks[0]} · ${period.resultChecks[1]}`,
    ]),
    widths: [170, 390, 592],
    rowHeight: 104,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 2,
    talk: "오늘의 산출물은 발표 자료가 아니라 다시 실행할 수 있는 JSON, Notebook, App 결과입니다.",
    activity: "누락 결과 파일 확인",
    sources: periods.flatMap((period) => period.sources),
  });
}

function addReferences() {
  const slide = deck.slides.add();
  addHeader(slide, "복습 자료", null, "OFFICIAL REFERENCE");
  addManualTable(slide, {
    top: 156,
    headers: ["주제", "공식 문서·영상"],
    rows: DAY3_GLOBAL.references,
    widths: [310, 842],
    rowHeight: 94,
    fontSize: S.table,
  });
  addNotes(slide, {
    minutes: 2,
    talk: "PPT의 요약보다 자세한 내용이 필요할 때는 공식 문서와 LangGraph 영상으로 확장합니다.",
    activity: "복습 링크 한 개 선택",
    sources: DAY3_GLOBAL.references.map(([, source]) => source),
  });
}

function addFullReplay() {
  const slide = deck.slides.add();
  addHeader(slide, "전체 실습 재실행", null, "6-STEP REPLAY");
  addNumberedRows(slide, [
    "Repository root · .venv312 · Notebook Kernel",
    "1~8차시 Cell 순서 실행",
    "output/course-labs/day3-v2/student-run · 8개 JSON 확인",
    "python scripts/run_day3_preflight.py --full-suite",
    "Localhost · 8765 · APPROVED·Golden 8/8 확인",
    "개인 branch · Draft PR · CI · 사람 Merge 판단",
  ], { top: 148, rowHeight: 80, bodySize: S.table });
  addNotes(slide, {
    minutes: 2,
    talk: "수업 후 전체를 다시 실행할 때는 여섯 단계만 기억하면 됩니다. 각 단계의 세부 정보는 차시별 Replay 장표에 있습니다.",
    activity: "재실행 시작 시점 선택",
    sources: ["local:materials/day3/day3_review_intelligence_lab.ipynb", "local:materials/day3/GitHub_PR_자동화_런북.md"],
  });
}

function addQA() {
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  addShape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  addText(slide, "17:30-18:00", { left: 84, top: 72, width: 500, height: 34 }, { size: S.table, bold: true, color: C.blue });
  addText(slide, "Q&A · 실습 복구", { left: 84, top: 190, width: 1080, height: 104 }, { size: S.deckTitle, bold: true, color: C.white });
  addText(slide, "질문 형식", { left: 84, top: 374, width: 220, height: 34 }, { size: S.label, bold: true, color: C.gray300 });
  addText(slide, "차시 번호 · 실행 명령 · Error 첫 줄 · 기대 결과", { left: 308, top: 360, width: 840, height: 64 }, { size: S.lead, bold: true, color: C.white, valign: "middle" });
  addShape(slide, "line", { left: 84, top: 482, width: 1092, height: 0 }, "none", C.blue, 4);
  addText(slide, "완료", { left: 84, top: 530, width: 220, height: 34 }, { size: S.label, bold: true, color: C.gray300 });
  addText(slide, "Notebook · 8개 JSON · Localhost · Draft PR · Test", { left: 308, top: 516, width: 840, height: 64 }, { size: S.body, bold: true, color: C.white, valign: "middle" });
  addNotes(slide, {
    minutes: 30,
    talk: "질문은 차시 번호, 명령, 오류 첫 줄, 기대 결과의 네 항목으로 받습니다. 공통 오류부터 화면으로 복구합니다.",
    activity: "질문 또는 Exit Check 제출",
    sources: ["local:materials/day3/2026_Day3_강사용_상세교안.md"],
  });
}

addDayCover();
await addPreview();
await addArchitectureOverview();
addSchedule("오전 운영표", DAY3_GLOBAL.scheduleMorning);
addSchedule("오후 운영표", DAY3_GLOBAL.scheduleAfternoon);
addSetup(
  "필수 설치",
  "FIXTURE LANE",
  DAY3_GLOBAL.requiredSetup,
  "필수 Lane은 외부 API 없이 1~8차시를 모두 완주하는 경로입니다.",
);
addSetup(
  "선택 설치와 Login",
  "OPTIONAL LANE",
  DAY3_GLOBAL.optionalSetup,
  "Ollama, Codex, Claude, OpenAI API는 확장 실습입니다. 준비되지 않아도 Fixture Lane은 계속됩니다.",
);
addLabMap("1~2차시 실습 지도", DAY3_STUDENT_PERIODS.slice(0, 2));
addLabMap("3~4차시 실습 지도", DAY3_STUDENT_PERIODS.slice(2, 4));
addLabMap("5~6차시 실습 지도", DAY3_STUDENT_PERIODS.slice(4, 6));
addLabMap("7~8차시 실습 지도", DAY3_STUDENT_PERIODS.slice(6, 8));

for (const [index, period] of DAY3_STUDENT_PERIODS.entries()) {
  await buildPeriod(period, index);
}

addArtifactMap("1~4차시 산출물", DAY3_STUDENT_PERIODS.slice(0, 4));
addArtifactMap("5~8차시 산출물", DAY3_STUDENT_PERIODS.slice(4, 8));
addReferences();
addFullReplay();
addQA();

if (deck.slides.items.length !== 176) {
  throw new Error(`Expected 176 slides, got ${deck.slides.items.length}`);
}

await fs.mkdir(path.dirname(OUT), { recursive: true });
const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(JSON.stringify({ slides: deck.slides.items.length, outPath: OUT }));
