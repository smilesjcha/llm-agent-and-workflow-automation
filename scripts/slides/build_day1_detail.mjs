import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import { MUSINSA_PPT, MUSINSA_REFERENCE, makeCoursePalette } from "../../design-system/ppt/cha-sungjae-musinsa-lecture/design-system.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUT = path.join(ROOT, "slides/IPA_LLM_Agent_업무자동화_Day1_2026-08-23_MUSINSA_PARTS_270p.pptx");
const ASSET = (name) => path.join(ROOT, "assets/screenshots", name);
const COMPONENT_ROOT = path.join(ROOT, "design-system/ppt/cha-sungjae-musinsa-lecture/components");
const ICON = (name) => path.join(COMPONENT_ROOT, "icons/lucide", `${name}.svg`);
const REFERENCE = (name) => path.join(COMPONENT_ROOT, "references", name);
const INSTRUCTOR_NAME = "차성재";

const C = makeCoursePalette();
const FONT = MUSINSA_PPT.fonts.korean;
const deck = Presentation.create({ slideSize: MUSINSA_PPT.slide });

const ICON_NAMES = [
  "presentation", "shield-check", "message-square-text", "terminal",
  "rotate-ccw", "database", "workflow", "mic-vocal", "clock-3",
  "coffee", "circle-question-mark", "chart-no-axes-combined",
];
const ICON_BYTES = Object.fromEntries(await Promise.all(
  ICON_NAMES.map(async (name) => [name, await fs.readFile(ICON(name))]),
));

const MODULE_ICONS = [
  "presentation", "shield-check", "message-square-text", "terminal",
  "rotate-ccw", "database", "workflow", "mic-vocal",
];

function shape(slide, geometry, position, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({ geometry, position, fill, line: { style: "solid", fill: lineFill, width: lineWidth } });
}

function textBox(slide, text, position, opts = {}) {
  const s = shape(slide, "textbox", position, opts.fill ?? "none", opts.lineFill ?? "none", opts.lineWidth ?? 0);
  // Keep exported PDF typography predictable across renderers.
  s.text = String(text).replace(/[–—]/g, "-");
  s.text.style = {
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    typeface: opts.typeface ?? FONT,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: opts.lineSpacing ?? 1.08,
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return s;
}

function addNotes(slide, body, sources = []) {
  let notes = body.trim();
  const allSources = [...new Set([...sources, MUSINSA_REFERENCE])];
  notes += `\n\n[Sources]\n${allSources.map((s) => `- ${s}`).join("\n")}\n[/Sources]`;
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

function talkTrack(mod, title, extra = "") {
  return [
    `강의 구간: ${mod.partTime ?? mod.time} · ${mod.partTopic ?? mod.title}`,
    `이 장표의 역할: ${title}`,
    "진행: 핵심 문장을 먼저 말하고, 화면의 항목을 위에서 아래로 1개씩 연결한다.",
    "확인 질문: 학습자가 자신의 업무 또는 포트폴리오 상황에 같은 원리를 적용해 1문장으로 설명하게 한다.",
    "빠른 반: 아래 항목 중 하나를 실제 코드·정책·평가 지표로 확장한다.",
    "복구 반: 용어보다 입력·처리·출력·검증의 네 칸만 채우고 다음 장으로 이동한다.",
    extra,
  ].filter(Boolean).join("\n");
}

function plainTone(value) {
  return String(value)
    .replace(/하지는 않습니다\.$/, "하지 않는다.")
    .replace(/필요합니다\.$/, "필요하다.")
    .replace(/가능합니다\.$/, "가능하다.")
    .replace(/있습니다\.$/, "있다.")
    .replace(/없습니다\.$/, "없다.")
    .replace(/됩니다\.$/, "된다.")
    .replace(/합니다\.$/, "한다.")
    .replace(/입니다\.$/, "이다.");
}

function bulletParts(value) {
  const source = plainTone(value);
  const slashParts = source.split(/\s+\/\s+/).map((part) => part.trim()).filter(Boolean);
  if (slashParts.length > 1) return slashParts.slice(0, 4);
  const dotParts = source.split(/\s*·\s*/).map((part) => part.trim()).filter(Boolean);
  if (dotParts.length > 1 && dotParts.length <= 5) return dotParts;
  return [source];
}

function addComponentIcon(slide, name, position, alt = name) {
  slide.images.add({
    blob: ICON_BYTES[name],
    contentType: "image/svg+xml",
    alt,
    fit: "contain",
    position,
    geometry: "rect",
    borderRadius: 0,
  });
}

function addFooter(slide, page, mod) {
  shape(slide, "line", { left: 64, top: 674, width: 1152, height: 0 }, "none", C.faint, 1);
  textBox(slide, "CHA SUNGJAE · LLM AGENT & 업무자동화", { left: 64, top: 684, width: 440, height: 18 }, { size: 10, bold: true, color: C.muted });
  textBox(slide, `${mod.partTime ?? mod.time} · ${mod.short}`, { left: 470, top: 684, width: 420, height: 18 }, { size: 10, color: mod.accent, bold: true, align: "center" });
  textBox(slide, String(page).padStart(3, "0"), { left: 1156, top: 684, width: 60, height: 18 }, { size: 10, bold: true, color: C.muted, align: "right" });
}

function participantLabel(kicker) {
  const value = String(kicker ?? "");
  const tutorial = value.match(/^TUTORIAL\s+(\d+\/\d+)/i);
  if (tutorial) return `실습 화면 ${tutorial[1]}`;
  const labels = {
    "DAY 1 · FOLLOW ALONG": "",
    "CORE IDEA": "",
    "KEY POINTS": "",
    "INSTRUCTOR": "강사 소개",
    "INSTRUCTOR · ONE PAGE": "강사 소개",
    "CAREER MAP": "강사 소개",
    "FIELD CASE": "현업 사례",
    "TEACHING": "강의·멘토 이력",
    "BEGINNER GLOSSARY · 4 TERMS": "처음 보는 용어 · 한 장으로 비교",
    "TOOL DECISION · WHY THIS STACK": "도구 선택 기준",
    "NEXT QUESTION": "오늘의 질문",
    "SCREEN ROUTE": "실습 화면 순서",
    "WORKFLOW": "진행 순서",
    "ACTUAL SCREEN": "실제 화면",
    "LIVE CODE": "코드 실습",
    "FOLLOW ALONG": "직접 실습",
    "FAILURE → RECOVERY": "실패 사례와 복구",
    "CAREER TRACK": "재직자·구직자 관점",
    "APPLICATION GATE": "판단 실습",
    "FINAL SYNTHESIS": "Q&A · Exit Ticket",
    "REFERENCE WORKFLOW": "공식 참고 자료",
    "GLOBAL DEVELOPER REFERENCE": "",
  };
  if (Object.hasOwn(labels, value)) return labels[value];
  if (value.startsWith("GLOBAL REFERENCE")) return "참고 사례";
  return value;
}

function addHeader(slide, title, mod, kicker = "") {
  const page = deck.slides.items.length;
  slide.background.fill = C.paper;
  const visibleLabel = participantLabel(kicker);
  if (visibleLabel) textBox(slide, visibleLabel, { left: 64, top: 38, width: 460, height: 20 }, { size: 11, bold: true, color: mod.accent });
  // Long Korean/English titles can be vertically displaced by some PPT renderers
  // when center anchoring and shrink-to-fit are combined. Top anchoring keeps the
  // baseline stable across PowerPoint, LibreOffice, and the render QA pipeline.
  textBox(slide, title, { left: 64, top: visibleLabel ? 78 : 58, width: 1152, height: visibleLabel ? 64 : 78 }, { size: MUSINSA_PPT.type.slideTitle, bold: true, color: C.ink, valign: "top" });
  addFooter(slide, page, mod);
}

function addBullets(slide, bullets, x, y, width, opts = {}) {
  const height = opts.height ?? 62;
  const gap = opts.gap ?? 12;
  bullets.forEach((item, i) => {
    const yy = y + i * (height + gap);
    shape(slide, "ellipse", { left: x, top: yy + 9, width: 11, height: 11 }, opts.dotColor ?? C.blue);
    textBox(slide, item, { left: x + 28, top: yy, width: width - 28, height }, {
      size: opts.size ?? 22, bold: opts.bold ?? false, color: opts.color ?? C.ink, lineSpacing: 1.12,
    });
  });
}

function coverSlide(mod) {
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  shape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  textBox(slide, "IPA · 40H PROJECT BASED LEARNING", { left: 84, top: 68, width: 720, height: 26 }, { size: 13, bold: true, color: C.white });
  textBox(slide, `${mod.partTime} · ${mod.partNumber}`, { left: 84, top: 112, width: 720, height: 30 }, { size: 18, bold: true, color: C.blue });
  textBox(slide, "LLM Agent &\n업무자동화", { left: 84, top: 164, width: 1060, height: 154 }, { size: 58, bold: true, color: C.white, lineSpacing: 0.94 });
  textBox(slide, "답을 잘하는 AI에서, 일을 끝내는 Workflow로", { left: 86, top: 342, width: 1020, height: 38 }, { size: 23, bold: true, color: C.faint });
  textBox(slide, mod.partTopic, { left: 86, top: 392, width: 1020, height: 36 }, { size: 24, bold: true, color: C.white });
  textBox(slide, mod.partFlow, { left: 86, top: 426, width: 1090, height: 18 }, { size: 11, bold: true, color: C.gray300 });

  const guideColumns = [
    { x: 84, width: 364, label: "지금 배우는 내용", value: mod.partLearn },
    { x: 448, width: 430, label: "이 차시에서 이해할 것", value: mod.partUnderstand },
    { x: 878, width: 298, label: "함께 챙길 내용", value: mod.partOutput },
  ];
  guideColumns.forEach((column) => {
    shape(slide, "rect", { left: column.x, top: 448, width: column.width, height: 30 }, C.navy);
    textBox(slide, column.label, { left: column.x + 14, top: 454, width: column.width - 28, height: 18 }, { size: 11, bold: true, color: C.white, valign: "middle" });
    shape(slide, "rect", { left: column.x, top: 478, width: column.width, height: 58 }, C.white);
    textBox(slide, column.value, { left: column.x + 14, top: 486, width: column.width - 28, height: 42 }, { size: 14, bold: true, color: C.ink, valign: "middle", lineSpacing: 1.08 });
  });
  textBox(slide, `${INSTRUCTOR_NAME} · 무신사 Agentic AI Side PM\n서울시립대·아주대 AI 겸임교수`, { left: 84, top: 570, width: 760, height: 62 }, { size: 17, bold: true, color: C.white, lineSpacing: 1.16 });
  textBox(slide, "2026.08.23 SUN\n09:00-18:00 · LUNCH 14:00-15:00", { left: 844, top: 578, width: 332, height: 54 }, { size: 14, color: C.gray300, bold: true, align: "right", lineSpacing: 1.24 });
  addNotes(slide, talkTrack(mod, "과정 표지", "오프닝 2분. 40시간 동안 하나의 검증 가능한 업무 Agent를 완성한다고 선언한다."));
}

function sectionSlide(mod) {
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  shape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  textBox(slide, mod.partTime, { left: 84, top: 62, width: 600, height: 58 }, { size: 35, bold: true, color: C.blue });
  textBox(slide, mod.partNumber, { left: 924, top: 72, width: 252, height: 32 }, { size: 17, bold: true, color: C.white, align: "right" });
  textBox(slide, mod.partTopic, { left: 84, top: 148, width: 1092, height: 92 }, { size: 47, bold: true, color: C.white, lineSpacing: 1.0, valign: "middle" });
  textBox(slide, mod.partFlow, { left: 88, top: 272, width: 1088, height: 28 }, { size: 16, bold: true, color: C.faint });
  const guideColumns = [
    { x: 84, width: 364, label: "지금 배우는 내용", value: mod.partLearn },
    { x: 448, width: 430, label: "이 차시에서 이해할 것", value: mod.partUnderstand },
    { x: 878, width: 298, label: "함께 챙길 내용", value: mod.partOutput },
  ];
  guideColumns.forEach((column) => {
    shape(slide, "rect", { left: column.x, top: 336, width: column.width, height: 44 }, C.black);
    textBox(slide, column.label, { left: column.x + 16, top: 346, width: column.width - 32, height: 24 }, { size: 14, bold: true, color: C.white, valign: "middle" });
    shape(slide, "rect", { left: column.x, top: 380, width: column.width, height: 172 }, C.white);
    textBox(slide, column.value, { left: column.x + 18, top: 400, width: column.width - 36, height: 130 }, { size: 20, bold: true, color: C.ink, valign: "middle", lineSpacing: 1.14 });
  });
  shape(slide, "line", { left: 84, top: 594, width: 1092, height: 0 }, "none", C.blue, 3);
  textBox(slide, `슬라이드 ${mod.partSlides}`, { left: 88, top: 612, width: 1088, height: 28 }, { size: 15, bold: true, color: C.gray300, align: "right" });
  addNotes(slide, talkTrack(mod, "차시 구분 표지", "시간을 먼저 읽고, 지금 배울 내용·이해할 기준·함께 챙길 내용을 왼쪽부터 확인한다."));
}

function dayTimetableSlide(mod) {
  const slide = deck.slides.add();
  addHeader(slide, "1일차는 여덟 개 차시로 진행합니다", mod, "첫날 전체 시간표");
  textBox(slide, "현재 차시의 시간·내용·결과를 확인하고, 쉬는 시간에는 실습 상태를 저장합니다.", { left: 68, top: 134, width: 1108, height: 30 }, { size: 17, bold: true, color: C.muted });

  const columns = [
    { x: 68, width: 146, label: "시간" },
    { x: 214, width: 78, label: "슬라이드" },
    { x: 292, width: 308, label: "진행 내용" },
    { x: 600, width: 284, label: "강의·시연·실습" },
    { x: 884, width: 292, label: "수강생이 남길 것" },
  ];
  const rows = [
    ["09:00-09:50", "1-29", "1일차 1차시 · Agent와 문제 정의", "강의 12 · 시연 8 · 실습 22 · 확인 8분", "자동화할 일 한 문장", "part"],
    ["09:50-10:40", "30-64", "1일차 2차시 · Tool Calling과 실행 권한", "강의 15 · 시연 10 · 실습 20 · 확인 5분", "허용할 도구와 막을 행동", "part"],
    ["10:40-11:30", "65-99", "1일차 3차시 · 한국어 데이터와 PBL 사례", "강의 14 · 시연 10 · 실습 21 · 확인 5분", "입력·결과·근거 예시", "part"],
    ["11:30-12:00", "-", "쉬는 시간", "1-3차시 종료 후 휴식", "빠른 점심 또는 간식 권장", "break"],
    ["12:00-12:50", "100-134", "1일차 4차시 · Python·VS Code·Git 환경", "강의 10 · 시연 15 · 실습 20 · 확인 5분", "버전·경로·PR 준비 상태", "part"],
    ["12:50-13:40", "135-168", "1일차 5차시 · 안전한 Agent 실행 루프", "강의 10 · 시연 10 · 실습 25 · 확인 5분", "정상·실패 test 결과", "part"],
    ["13:40-14:00", "-", "쉬는 시간", "4-5차시 종료 후 휴식", "점심 전 실습 상태 저장", "break"],
    ["14:00-15:00", "-", "점심시간", "1시간", "14:55까지 복귀", "lunch"],
    ["15:00-15:40", "169-202", "1일차 6차시 · 무료·로컬 LLM과 Adapter", "강의 8 · 시연 10 · 실습 17 · 확인 5분", "성공 또는 예상된 실패 결과", "part"],
    ["15:40-16:20", "203-236", "1일차 7차시 · LangGraph와 사람 승인", "강의 8 · 시연 12 · 실습 15 · 확인 5분", "승인·수정·거절 상태", "part"],
    ["16:20-17:00", "237-269", "1일차 8차시 · STT와 LangSmith", "강의 8 · 시연 10 · 실습 15 · 확인 7분", "품질 기준과 READY/HOLD 판단", "part"],
    ["17:00-17:30", "-", "쉬는 시간", "6-8차시 종료 후 휴식", "질문 정리", "break"],
    ["17:30-18:00", "270", "Q&A · 실습 복구 · Exit Ticket", "질문 15 · 복구 10 · Exit 5분", "오늘의 핵심 세 문장", "qa"],
  ];

  shape(slide, "rect", { left: 68, top: 172, width: 1108, height: 34 }, C.black);
  columns.forEach((column) => textBox(slide, column.label, { left: column.x + 10, top: 179, width: column.width - 20, height: 20 }, { size: 12, bold: true, color: C.white, valign: "middle" }));

  rows.forEach((row, index) => {
    const y = 206 + index * 34;
    const kind = row[5];
    const fill = kind === "lunch" || kind === "qa" ? C.blueSoft : kind === "break" ? C.gray100 : index % 2 === 1 ? C.gray100 : C.white;
    shape(slide, "rect", { left: 68, top: y, width: 1108, height: 34 }, fill);
    if (kind === "part" || kind === "qa") shape(slide, "rect", { left: 68, top: y, width: 5, height: 34 }, kind === "qa" ? C.navy : C.blue);
    const values = row.slice(0, 5);
    columns.forEach((column, columnIndex) => {
      const color = columnIndex === 0 && kind === "part" ? C.blue : kind === "lunch" ? C.navy : C.ink;
      textBox(slide, values[columnIndex], { left: column.x + 10, top: y + 6, width: column.width - 20, height: 22 }, {
        size: columnIndex < 2 ? 11 : 11.5,
        bold: columnIndex === 0 || kind === "qa" || kind === "lunch" || (columnIndex === 2 && kind === "part"),
        color,
        valign: "middle",
        lineSpacing: 1.0,
      });
    });
    shape(slide, "line", { left: 68, top: y + 34, width: 1108, height: 0 }, "none", C.faint, 1);
  });
  addNotes(slide, talkTrack(mod, "첫날 전체 시간표", "3쪽의 하루 지도다. 각 차시 표지에서 같은 시간·내용·산출물을 다시 찾아 현재 위치를 확인한다."));
}

function openingScheduleSlide(mod) {
  const slide = deck.slides.add();
  addHeader(slide, "첫날은 점심시간이 14시입니다", mod, "DAY 1 · 운영 안내");
  addComponentIcon(slide, "coffee", { left: 1094, top: 72, width: 86, height: 86 }, "점심과 휴식을 알리는 커피 아이콘");
  textBox(slide, "강사의 오후 주요 일정으로 이번 주만 1시간 점심시간을 14:00-15:00에 운영합니다.", { left: 68, top: 150, width: 970, height: 50 }, { size: 22, bold: true, color: C.ink, lineSpacing: 1.15 });
  shape(slide, "rect", { left: 68, top: 210, width: 1108, height: 48 }, C.blueSoft);
  textBox(slide, "11:30-12:00 쉬는 시간에는 빠른 점심 또는 간식을 미리 드시길 권합니다.", { left: 88, top: 220, width: 1068, height: 28 }, { size: 18, bold: true, color: C.navy, valign: "middle" });
  textBox(slide, "12-13시에 점심시간을 드리지 못하게 되었습니다. 불편을 드려 죄송합니다. ㅠ.ㅠ", { left: 68, top: 270, width: 1108, height: 34 }, { size: 18, color: C.muted });

  const blocks = [
    ["09:00-12:00", "1-3차시", "09:00-11:30 수업 (11:30-12:00 쉬는 시간)", "빠른 점심·간식 권장"],
    ["12:00-14:00", "4-5차시", "12:00-13:40 수업 (13:40-14:00 쉬는 시간)", "총 2시간"],
    ["14:00-15:00", "LUNCH", "점심시간", "이번 주만 14시 시작"],
    ["15:00-17:30", "6-8차시", "15:00-17:00 수업 (17:00-17:30 쉬는 시간)", "총 2시간 30분"],
    ["17:30-18:00", "Q&A", "질문·실습 복구·Exit Ticket", "쉬는 시간 뒤 시작"],
  ];
  blocks.forEach((block, i) => {
    const y = 318 + i * 58;
    const fill = i === 2 ? C.navy : i === 4 ? C.blue : C.black;
    shape(slide, "rect", { left: 68, top: y, width: 162, height: 38 }, fill);
    textBox(slide, block[0], { left: 68, top: y + 5, width: 162, height: 28 }, { size: 14, bold: true, color: C.white, align: "center", valign: "middle" });
    textBox(slide, block[1], { left: 260, top: y + 3, width: 142, height: 32 }, { size: 16, bold: true, color: i >= 2 ? C.blue : C.ink, valign: "middle" });
    textBox(slide, block[2], { left: 410, top: y + 3, width: 500, height: 32 }, { size: 16, bold: true, color: C.ink, valign: "middle" });
    textBox(slide, block[3], { left: 930, top: y + 3, width: 246, height: 32 }, { size: 14, color: C.muted, align: "right", valign: "middle" });
    shape(slide, "line", { left: 260, top: y + 45, width: 916, height: 0 }, "none", C.faint, 1);
  });
  addNotes(slide, talkTrack(mod, "첫날 운영 안내", "강사의 오후 주요 일정 때문에 이번 주만 점심시간을 14:00-15:00에 운영한다. 11:30-12:00에는 빠른 점심 또는 간식을 미리 섭취하도록 안내한다. 쉬는 시간은 각 수업 구간의 맨 끝에 배정한다."));
}

function moduleMap(mod, index) {
  if (index === 0) {
    openingScheduleSlide(mod);
    return;
  }
  const slide = deck.slides.add();
  addHeader(slide, mod.mapTitle, mod, "NEXT QUESTION");
  textBox(slide, mod.question, { left: 68, top: 164, width: 1120, height: 56 }, { size: 27, bold: true, color: C.ink });
  const lanes = mod.mapSteps;
  lanes.forEach((lane, i) => {
    const y = 248 + i * 72;
    shape(slide, "rect", { left: 78, top: y, width: 118, height: 48 }, i === 4 ? C.blue : C.black);
    textBox(slide, lane[0], { left: 78, top: y + 7, width: 118, height: 34 }, { size: 18, bold: true, color: C.white, align: "center", valign: "middle" });
    textBox(slide, lane[1], { left: 228, top: y + 6, width: 920, height: 40 }, { size: 23, color: C.ink, valign: "middle" });
  });
  addNotes(slide, talkTrack(mod, "시간대 지도", "필수 본편은 개념·화면·따라하기·증거다. 실패·복구와 확장은 반 속도에 맞춰 선택한다."));
}

function statementSlide(mod, item, iconName = null, insight = null) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "CORE IDEA");
  shape(slide, "rect", { left: 64, top: 184, width: 10, height: 360 }, item.kicker === "INSTRUCTOR" ? C.blue : C.black);
  const claimWidth = iconName ? 850 : 1020;
  textBox(slide, plainTone(item.claim), { left: 112, top: 188, width: claimWidth, height: 148 }, { size: item.size ?? 37, bold: true, color: C.ink, lineSpacing: 1.06, valign: "middle" });
  if (iconName) addComponentIcon(slide, iconName, { left: 1008, top: 194, width: 142, height: 142 }, `${mod.title} 핵심 개념 아이콘`);
  const bullets = bulletParts(item.support);
  addBullets(slide, bullets, 118, 382, 1010, { size: 21, height: 42, gap: 8, dotColor: C.black });
  if (insight) {
    shape(slide, "rect", { left: 112, top: 618, width: 1040, height: 38 }, C.blueSoft);
    textBox(slide, `${mod.insightLabel}  |  ${insight}`, { left: 132, top: 625, width: 1000, height: 24 }, { size: 15, bold: true, color: C.navy, valign: "middle" });
  }
  addNotes(slide, talkTrack(mod, item.title, item.note ?? ""), item.sources ?? []);
}

function profileCareerSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, "INSTRUCTOR · ONE PAGE");
  textBox(slide, item.lead, { left: 68, top: 154, width: 1110, height: 42 }, { size: 21, bold: true, color: C.muted });

  const columns = [
    { x: 68, width: 112, label: "산업" },
    { x: 180, width: 230, label: "데이터·AI" },
    { x: 410, width: 590, label: "풀었던 문제" },
    { x: 1000, width: 176, label: "역할" },
  ];
  shape(slide, "rect", { left: 68, top: 208, width: 1108, height: 38 }, C.black);
  columns.forEach((column) => textBox(slide, column.label, { left: column.x + 10, top: 216, width: column.width - 20, height: 22 }, { size: 13, bold: true, color: C.white, valign: "middle" }));

  item.rows.forEach((row, index) => {
    const y = 246 + index * 78;
    if (index % 2 === 1) shape(slide, "rect", { left: 68, top: y, width: 1108, height: 78 }, C.gray100);
    columns.forEach((column, columnIndex) => {
      textBox(slide, row[columnIndex], { left: column.x + 10, top: y + 10, width: column.width - 20, height: 58 }, {
        size: columnIndex === 0 ? 18 : columnIndex === 2 ? 16 : 15,
        bold: columnIndex === 0 || columnIndex === 3,
        color: columnIndex === 0 ? C.blue : C.ink,
        valign: "middle",
        lineSpacing: 1.12,
      });
    });
    shape(slide, "line", { left: 68, top: y + 78, width: 1108, height: 0 }, "none", C.faint, 1);
  });

  shape(slide, "rect", { left: 68, top: 574, width: 1108, height: 70 }, C.blueSoft);
  textBox(slide, item.bottom, { left: 88, top: 586, width: 1068, height: 46 }, { size: 16, bold: true, color: C.navy, valign: "middle" });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "금융→의료→교육→이커머스를 데이터 형태와 제품 책임의 확장으로 설명한다."), item.sources ?? []);
}

function glossaryTableSlide(mod, items) {
  const slide = deck.slides.add();
  addHeader(slide, mod.glossaryTitle, mod, "BEGINNER GLOSSARY · 4 TERMS");

  const columns = [
    { x: 68, width: 220, label: "용어" },
    { x: 288, width: 470, label: "쉽게 말하면" },
    { x: 758, width: 418, label: "오늘 쓰는 곳" },
  ];
  shape(slide, "rect", { left: 68, top: 168, width: 1108, height: 42 }, C.black);
  columns.forEach((column) => textBox(slide, column.label, { left: column.x + 14, top: 178, width: column.width - 28, height: 22 }, { size: 14, bold: true, color: C.white, valign: "middle" }));

  items.forEach((item, index) => {
    const y = 210 + index * 92;
    if (index % 2 === 1) shape(slide, "rect", { left: 68, top: y, width: 1108, height: 92 }, C.gray100);
    textBox(slide, `${item.term}\n${item.english}`, { left: 82, top: y + 12, width: 192, height: 66 }, { size: 17, bold: true, color: index === 3 ? C.blue : C.ink, valign: "middle", lineSpacing: 1.15 });
    textBox(slide, plainTone(item.meaning), { left: 302, top: y + 12, width: 442, height: 66 }, { size: 17, color: C.ink, valign: "middle", lineSpacing: 1.13 });
    textBox(slide, plainTone(item.example), { left: 772, top: y + 12, width: 390, height: 66 }, { size: 16, bold: true, color: C.ink, valign: "middle", lineSpacing: 1.13 });
    shape(slide, "line", { left: 68, top: y + 92, width: 1108, height: 0 }, "none", C.faint, 1);
  });
  addNotes(slide, talkTrack(mod, `${mod.glossaryTitle} · 통합 용어표`, "네 용어를 개별 장표로 반복하지 않고 한 표에서 역할 차이를 비교한다."), items.flatMap((item) => item.sources ?? []));
}

function toolComparisonSlide(mod) {
  const slide = deck.slides.add();
  addHeader(slide, mod.tutorialTitle, mod, "TOOL DECISION · WHY THIS STACK");
  textBox(slide, mod.tutorialLead, { left: 68, top: 154, width: 1110, height: 44 }, { size: 20, bold: true, color: C.muted });

  const columns = [
    { x: 68, width: 190, label: "도구·서비스" },
    { x: 258, width: 220, label: "도메인·역할" },
    { x: 478, width: 410, label: "이번 강의에서 쓰는 이유" },
    { x: 888, width: 288, label: "유사 도구와의 차이" },
  ];
  shape(slide, "rect", { left: 68, top: 214, width: 1108, height: 42 }, C.black);
  columns.forEach((column) => textBox(slide, column.label, { left: column.x + 12, top: 224, width: column.width - 24, height: 22 }, { size: 13, bold: true, color: C.white, valign: "middle" }));

  const rowHeight = mod.toolComparison.length === 5 ? 70 : 84;
  mod.toolComparison.forEach((row, index) => {
    const y = 256 + index * rowHeight;
    if (index % 2 === 1) shape(slide, "rect", { left: 68, top: y, width: 1108, height: rowHeight }, C.gray100);
    columns.forEach((column, columnIndex) => {
      textBox(slide, row[columnIndex], { left: column.x + 12, top: y + 9, width: column.width - 24, height: rowHeight - 18 }, {
        size: columnIndex === 0 ? 17 : 15,
        bold: columnIndex === 0 || columnIndex === 2,
        color: columnIndex === 0 ? C.blue : C.ink,
        valign: "middle",
        lineSpacing: 1.12,
      });
    });
    shape(slide, "line", { left: 68, top: y + rowHeight, width: 1108, height: 0 }, "none", C.faint, 1);
  });
  addNotes(slide, talkTrack(mod, `${mod.title} 도구 선택표`, "툴 이름을 나열하지 않고 역할·선택 이유·대안과의 차이를 먼저 비교한다."), mod.screenshots.map((item) => item.source));
}

async function referencePairSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "GLOBAL DEVELOPER REFERENCE");
  const leftBytes = await fs.readFile(REFERENCE(item.visualPair[0].image));
  const rightBytes = await fs.readFile(REFERENCE(item.visualPair[1].image));
  slide.images.add({ blob: leftBytes, contentType: item.visualPair[0].contentType, alt: item.visualPair[0].caption, fit: "cover", position: { left: 64, top: 170, width: 534, height: 300 }, geometry: "rect", borderRadius: 0 });
  slide.images.add({ blob: rightBytes, contentType: item.visualPair[1].contentType, alt: item.visualPair[1].caption, fit: "cover", position: { left: 618, top: 170, width: 598, height: 300 }, geometry: "rect", borderRadius: 0 });
  shape(slide, "rect", { left: 64, top: 492, width: 1152, height: 120 }, C.black);
  const points = bulletParts(item.support);
  points.forEach((point, i) => {
    textBox(slide, `0${i + 1}`, { left: 94 + i * 370, top: 518, width: 44, height: 32 }, { size: 14, bold: true, color: C.blue });
    textBox(slide, point, { left: 138 + i * 370, top: 514, width: 300, height: 62 }, { size: 18, bold: true, color: C.white, valign: "middle" });
  });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "이미지를 설명하기보다, 발표자가 말하고 장표는 한 메시지와 실제 화면만 남기는 방식을 관찰한다."), item.sources ?? []);
}

async function referenceVisualSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "REFERENCE WORKFLOW");
  addBullets(slide, item.visualBullets, 70, 190, 360, { size: 20, height: 62, gap: 12, dotColor: C.black });
  const bytes = await fs.readFile(REFERENCE(item.visual.image));
  slide.images.add({ blob: bytes, contentType: item.visual.contentType, alt: item.visual.caption, fit: "contain", position: { left: 470, top: 158, width: 746, height: 472 }, geometry: "rect", borderRadius: 0 });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "공식 튜토리얼의 workflow를 보며 어디에서 중단하고 사람이 개입하는지 확인한다."), item.sources ?? []);
}

function keyPointsSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "KEY POINTS");
  if (item.lead) textBox(slide, plainTone(item.lead), { left: 68, top: 158, width: 1110, height: 48 }, { size: 23, bold: true, color: C.muted });
  addBullets(slide, item.bullets.map(plainTone), 84, item.lead ? 226 : 186, 1080, { size: item.bulletSize ?? 21, height: item.height ?? 62, gap: item.gap ?? 10, dotColor: C.black });
  if (item.bottom) {
    shape(slide, "rect", { left: 64, top: 582, width: 1152, height: 64 }, item.bottomFill ?? C.blueSoft);
    textBox(slide, item.bottom, { left: 88, top: 596, width: 1102, height: 36 }, { size: 18, bold: true, color: C.ink, valign: "middle" });
  }
  addNotes(slide, talkTrack(mod, item.title, item.note ?? ""), item.sources ?? []);
}

function processSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "WORKFLOW");
  const left = 68, top = 220, gap = 18, n = item.steps.length;
  const w = (1140 - gap * (n - 1)) / n;
  item.steps.forEach((step, i) => {
    const x = left + i * (w + gap);
    shape(slide, "line", { left: x, top, width: w, height: 0 }, "none", i === n - 1 ? C.blue : C.black, 3);
    textBox(slide, String(i + 1).padStart(2, "0"), { left: x, top: top + 22, width: 54, height: 28 }, { size: 14, bold: true, color: C.blue });
    textBox(slide, step[0], { left: x, top: top + 72, width: w - 18, height: 52 }, { size: 22, bold: true, color: C.ink, valign: "middle" });
    textBox(slide, step[1], { left: x, top: top + 136, width: w - 18, height: 70 }, { size: 17, color: C.muted, lineSpacing: 1.16 });
  });
  if (item.bottom) textBox(slide, item.bottom, { left: 84, top: 510, width: 1100, height: 66 }, { size: 22, bold: true, color: C.ink, align: "center", valign: "middle" });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? ""), item.sources ?? []);
}

function openingGuidanceSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "오늘 실습 안내");

  if (item.variant === "class_cycle") {
    textBox(slide, item.lead, { left: 68, top: 154, width: 1108, height: 46 }, { size: 22, bold: true, color: C.muted });
    item.steps.forEach((step, index) => {
      const y = 218 + index * 88;
      shape(slide, "rect", { left: 68, top: y, width: 64, height: 64 }, index === item.steps.length - 1 ? C.blue : C.black);
      textBox(slide, String(index + 1), { left: 68, top: y, width: 64, height: 64 }, { size: 24, bold: true, color: C.white, align: "center", valign: "middle" });
      textBox(slide, step[0], { left: 166, top: y + 3, width: 310, height: 58 }, { size: 24, bold: true, color: C.ink, valign: "middle" });
      textBox(slide, step[1], { left: 500, top: y + 3, width: 650, height: 58 }, { size: 19, color: C.muted, valign: "middle", lineSpacing: 1.15 });
      shape(slide, "line", { left: 166, top: y + 72, width: 984, height: 0 }, "none", C.faint, 1);
    });
  } else if (item.variant === "help_request") {
    shape(slide, "rect", { left: 68, top: 174, width: 392, height: 360 }, C.black);
    addComponentIcon(slide, "message-square-text", { left: 100, top: 208, width: 70, height: 70 }, "도움을 요청하는 대화 아이콘");
    textBox(slide, "“안 돼요”", { left: 100, top: 310, width: 300, height: 64 }, { size: 42, bold: true, color: C.white });
    textBox(slide, "어디서부터 확인해야 할지\n알기 어렵습니다", { left: 100, top: 400, width: 300, height: 84 }, { size: 20, color: C.faint, lineSpacing: 1.18 });
    textBox(slide, "대신 아래 네 가지를 알려주세요", { left: 512, top: 166, width: 640, height: 44 }, { size: 24, bold: true, color: C.ink });
    item.steps.forEach((step, index) => {
      const y = 228 + index * 76;
      textBox(slide, String(index + 1).padStart(2, "0"), { left: 512, top: y, width: 48, height: 36 }, { size: 15, bold: true, color: C.blue, valign: "middle" });
      textBox(slide, step[0], { left: 578, top: y, width: 240, height: 36 }, { size: 20, bold: true, color: C.ink, valign: "middle" });
      textBox(slide, step[1], { left: 820, top: y, width: 332, height: 36 }, { size: 17, color: C.muted, valign: "middle" });
      shape(slide, "line", { left: 578, top: y + 48, width: 574, height: 0 }, "none", C.faint, 1);
    });
    shape(slide, "rect", { left: 68, top: 574, width: 1108, height: 70 }, C.blueSoft);
    textBox(slide, item.example, { left: 88, top: 587, width: 1068, height: 44 }, { size: 16, bold: true, color: C.navy, valign: "middle" });
  } else if (item.variant === "pace_choice") {
    textBox(slide, item.lead, { left: 68, top: 154, width: 1108, height: 44 }, { size: 22, bold: true, color: C.muted });
    const columns = [
      { x: 68, width: 250, label: "지금 내 상태" },
      { x: 318, width: 500, label: "지금 할 일" },
      { x: 818, width: 358, label: "다음에 남길 것" },
    ];
    shape(slide, "rect", { left: 68, top: 214, width: 1108, height: 42 }, C.black);
    columns.forEach((column) => textBox(slide, column.label, { left: column.x + 14, top: 224, width: column.width - 28, height: 22 }, { size: 14, bold: true, color: C.white, valign: "middle" }));
    item.steps.forEach((row, index) => {
      const y = 256 + index * 76;
      if (index % 2 === 1) shape(slide, "rect", { left: 68, top: y, width: 1108, height: 76 }, C.gray100);
      textBox(slide, row[0], { left: 82, top: y + 10, width: 222, height: 56 }, { size: 19, bold: true, color: index === item.steps.length - 1 ? C.blue : C.ink, valign: "middle" });
      textBox(slide, row[1], { left: 332, top: y + 10, width: 472, height: 56 }, { size: 18, color: C.ink, valign: "middle" });
      textBox(slide, row[2], { left: 832, top: y + 10, width: 330, height: 56 }, { size: 17, bold: true, color: C.muted, valign: "middle" });
      shape(slide, "line", { left: 68, top: y + 76, width: 1108, height: 0 }, "none", C.faint, 1);
    });
    textBox(slide, item.bottom, { left: 76, top: 582, width: 1092, height: 48 }, { size: 18, bold: true, color: C.navy, align: "center", valign: "middle" });
  } else if (item.variant === "proof") {
    textBox(slide, item.lead, { left: 68, top: 154, width: 1108, height: 44 }, { size: 22, bold: true, color: C.muted });
    textBox(slide, "완료 체크", { left: 68, top: 218, width: 440, height: 42 }, { size: 24, bold: true, color: C.ink });
    item.steps.forEach((step, index) => {
      const y = 278 + index * 68;
      shape(slide, "rect", { left: 72, top: y + 5, width: 34, height: 34 }, index === item.steps.length - 1 ? C.blue : C.black);
      textBox(slide, "✓", { left: 72, top: y + 4, width: 34, height: 34 }, { size: 20, bold: true, color: C.white, align: "center", valign: "middle" });
      textBox(slide, step[0], { left: 128, top: y, width: 410, height: 46 }, { size: 20, bold: true, color: C.ink, valign: "middle" });
    });
    shape(slide, "rect", { left: 590, top: 214, width: 586, height: 336 }, C.black);
    shape(slide, "rect", { left: 590, top: 214, width: 6, height: 336 }, C.blue);
    textBox(slide, "다시 확인할 수 있는 화면", { left: 620, top: 238, width: 520, height: 32 }, { size: 18, bold: true, color: C.faint });
    textBox(slide, item.terminal, { left: 620, top: 292, width: 520, height: 220 }, { size: 18, color: C.white, typeface: MUSINSA_PPT.fonts.mono, lineSpacing: 1.2 });
    shape(slide, "rect", { left: 68, top: 584, width: 1108, height: 60 }, C.blueSoft);
    textBox(slide, item.bottom, { left: 88, top: 596, width: 1068, height: 36 }, { size: 18, bold: true, color: C.navy, valign: "middle" });
  }

  addNotes(slide, talkTrack(mod, item.title, item.note ?? ""), item.sources ?? []);
}

async function screenshotSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "ACTUAL SCREEN");
  textBox(slide, "이 화면에서 딱 볼 것", { left: 70, top: 170, width: 350, height: 28 }, { size: 15, bold: true, color: C.blue });
  addBullets(slide, item.bullets, 70, 218, 390, { size: 19, height: 54, gap: 9, dotColor: C.black });
  shape(slide, "rect", { left: 500, top: 166, width: 716, height: 438 }, C.white, C.faint, 1);
  const bytes = await fs.readFile(ASSET(item.image));
  slide.images.add({ blob: bytes, contentType: "image/jpeg", alt: item.caption, fit: "contain", position: { left: 512, top: 178, width: 692, height: 396 }, geometry: "rect", borderRadius: 0 });
  textBox(slide, item.caption, { left: 512, top: 578, width: 690, height: 26 }, { size: 13, color: C.muted, align: "right" });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "화면에서 메뉴·명령·성공 신호를 순서대로 짚는다."), [item.source]);
}

function codeSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "LIVE CODE");
  textBox(slide, "코드 전체보다 경계 한 줄을 먼저 봅니다", { left: 70, top: 170, width: 400, height: 28 }, { size: 15, bold: true, color: C.blue });
  addBullets(slide, item.bullets, 70, 216, 400, { size: 19, height: 54, gap: 9, dotColor: C.black });
  shape(slide, "rect", { left: 506, top: 166, width: 710, height: 442 }, C.black, C.black, 1);
  shape(slide, "rect", { left: 506, top: 166, width: 6, height: 442 }, C.blue);
  textBox(slide, item.code, { left: 536, top: 194, width: 654, height: 390 }, { size: item.codeSize ?? 16, color: C.white, typeface: MUSINSA_PPT.fonts.mono, lineSpacing: 1.12 });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "코드를 위에서 아래로 읽고, 바꿔도 되는 값과 고정해야 할 계약을 구분한다."), item.sources ?? []);
}

function exerciseSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, "FOLLOW ALONG");
  textBox(slide, item.duration, { left: 64, top: 190, width: 184, height: 60 }, { size: 34, bold: true, color: C.black });
  shape(slide, "line", { left: 64, top: 264, width: 184, height: 0 }, "none", C.blue, 3);
  textBox(slide, "강사 화면을 보며\n각자 진행합니다", { left: 64, top: 306, width: 196, height: 74 }, { size: 18, bold: true, color: C.ink, lineSpacing: 1.16 });
  textBox(slide, "막히면 채팅창에\n첫 오류 한 줄만\n남겨주세요", { left: 64, top: 442, width: 196, height: 100 }, { size: 16, color: C.muted, lineSpacing: 1.16 });
  item.steps.forEach((step, i) => {
    textBox(slide, String(i + 1), { left: 318, top: 180 + i * 74, width: 40, height: 40 }, { size: 21, bold: true, color: C.blue, align: "center", valign: "middle" });
    textBox(slide, step, { left: 382, top: 179 + i * 74, width: 790, height: 48 }, { size: 22, color: C.ink, valign: "middle" });
    shape(slide, "line", { left: 382, top: 230 + i * 74, width: 790, height: 0 }, "none", C.faint, 1);
  });
  if (item.example) {
    textBox(slide, `예시  |  ${item.example}`, { left: 318, top: 476, width: 854, height: 42 }, { size: 16, bold: true, color: C.muted, valign: "middle" });
  }
  shape(slide, "rect", { left: 318, top: 536, width: 854, height: 70 }, C.blueSoft);
  textBox(slide, `완료 증거  |  ${item.done}`, { left: 342, top: 551, width: 806, height: 40 }, { size: 19, bold: true, color: C.navy, valign: "middle" });
  addNotes(slide, talkTrack(mod, item.title, `실습 ${item.duration}. 5분·2분·1분 전에 남은 시간을 공지한다. ${item.note ?? ""}`), item.sources ?? []);
}

function compareSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.kicker ?? "FAILURE → RECOVERY");
  textBox(slide, item.leftTitle ?? "현업에서 자주 깨지는 방식", { left: 70, top: 174, width: 500, height: 42 }, { size: 24, bold: true, color: C.black });
  textBox(slide, item.rightTitle ?? "제가 먼저 고치는 순서", { left: 676, top: 174, width: 500, height: 42 }, { size: 24, bold: true, color: C.blue });
  shape(slide, "line", { left: 620, top: 174, width: 0, height: 394 }, "none", C.faint, 2);
  addBullets(slide, item.left, 78, 236, 510, { size: 21, height: 56, gap: 10, dotColor: C.black });
  addBullets(slide, item.right, 684, 236, 510, { size: 21, height: 56, gap: 10, dotColor: C.blue });
  if (item.bottom) textBox(slide, item.bottom, { left: 80, top: 584, width: 1100, height: 46 }, { size: 20, bold: true, color: C.ink, align: "center" });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "실패를 숨기지 않고 재현한 뒤, 재시도·중단·사람 검토 중 하나를 선택한다."), item.sources ?? []);
}

function checkpointSlide(mod, item) {
  const slide = deck.slides.add();
  addHeader(slide, item.title, mod, item.title.includes("Q&A") ? "FINAL SYNTHESIS" : "APPLICATION GATE");
  const isFinalQa = item.title.includes("Q&A");
  if (isFinalQa) addComponentIcon(slide, "circle-question-mark", { left: 1094, top: 70, width: 84, height: 84 }, "질문과 답변 아이콘");
  textBox(slide, item.prompt ?? "처음 보는 상황입니다. 실행·차단·사람 검토 중 하나를 고르고 근거를 말해보세요.", { left: 72, top: 158, width: isFinalQa ? 930 : 1080, height: 58 }, { size: 22, color: C.muted });
  item.questions.forEach((q, i) => {
    const colors = [C.black, C.navy, C.blue];
    shape(slide, "rect", { left: 72, top: 236 + i * 112, width: 72, height: 72 }, colors[i]);
    textBox(slide, String(i + 1), { left: 72, top: 236 + i * 112, width: 72, height: 72 }, { size: 27, bold: true, color: C.white, align: "center", valign: "middle" });
    textBox(slide, q, { left: 176, top: 240 + i * 112, width: 950, height: 66 }, { size: 26, bold: true, color: C.ink, valign: "middle" });
  });
  addNotes(slide, talkTrack(mod, item.title, item.note ?? "온라인 개인 판단으로 진행한다. 발표나 공개 공유를 요구하지 않고, 질문이 있으면 채팅창에 첫 오류 또는 판단 근거 한 줄만 받는다. 강사가 대표 상황을 골라 해설한다."));
}

function definitionSlide(mod, item, index, total) {
  const slide = deck.slides.add();
  addHeader(slide, item.term, mod, `처음 듣는 용어 ${index + 1}/${total} · ${item.english}`);
  const rows = [
    ["한 줄로 말하면", plainTone(item.meaning)],
    ["왜 중요한가", plainTone(item.why)],
    ["오늘은 이렇게 쓴다", plainTone(item.example)],
  ];
  rows.forEach((row, i) => {
    const y = 178 + i * 142;
    textBox(slide, `0${i + 1}`, { left: 68, top: y + 7, width: 42, height: 32 }, { size: 14, bold: true, color: i === 2 ? C.blue : C.black });
    textBox(slide, row[0], { left: 126, top: y, width: 190, height: 44 }, { size: 18, bold: true, color: i === 2 ? C.blue : C.muted, valign: "middle" });
    textBox(slide, row[1], { left: 330, top: y, width: 842, height: 88 }, { size: i === 0 ? 27 : 21, bold: i !== 1, color: C.ink, lineSpacing: 1.14, valign: "middle" });
    shape(slide, "line", { left: 126, top: y + 108, width: 1046, height: 0 }, "none", i === 2 ? C.blue : C.faint, i === 2 ? 2 : 1);
  });
  addNotes(slide, talkTrack(mod, `${item.term} 용어 풀이`, `영문 철자보다 한 줄 뜻과 수업 예시를 먼저 이해시킨다.`), item.sources ?? []);
}

function tutorialMapSlide(mod) {
  if (mod.toolComparison) {
    toolComparisonSlide(mod);
    return;
  }
  const slide = deck.slides.add();
  addHeader(slide, mod.tutorialTitle, mod, "SCREEN ROUTE");
  textBox(slide, mod.tutorialLead, { left: 64, top: 154, width: 1120, height: 54 }, { size: 21, bold: true, color: C.muted });
  mod.screenshots.forEach((item, index) => {
    const route = mod.tutorialRoutes?.[index] ?? [item.title, item.bullets.at(-1)];
    const y = 230 + index * 74;
    textBox(slide, String(index + 1).padStart(2, "0"), { left: 64, top: y, width: 64, height: 44 }, { size: 17, bold: true, color: index === mod.screenshots.length - 1 ? C.blue : C.black, valign: "middle" });
    shape(slide, "line", { left: 140, top: y + 22, width: 72, height: 0 }, "none", C.gray300, 1);
    textBox(slide, route[0], { left: 240, top: y, width: 686, height: 44 }, { size: 22, bold: true, color: C.ink, valign: "middle" });
    textBox(slide, route[1], { left: 940, top: y, width: 238, height: 44 }, { size: 15, bold: true, color: index === mod.screenshots.length - 1 ? C.blue : C.muted, align: "right", valign: "middle" });
    shape(slide, "line", { left: 240, top: y + 56, width: 938, height: 0 }, "none", C.faint, 1);
  });
  addNotes(slide, talkTrack(mod, "단계별 화면 지도", "화면을 보기 전에 전체 경로와 마지막 성공 신호를 먼저 공유한다."), mod.screenshots.map((item) => item.source));
}

function c(title, claim, support, extra = {}) { return { title, claim, support, ...extra }; }
function p(title, ...parts) {
  const extra = parts.length > 0 && !Array.isArray(parts.at(-1)) ? parts.pop() : {};
  return { title, steps: parts, ...extra };
}
function s(title, image, caption, source, bullets, extra = {}) { return { title, image, caption, source, bullets, ...extra }; }
function e(title, code, bullets, extra = {}) { return { title, code, bullets, ...extra }; }
function l(title, duration, steps, done, extra = {}) { return { title, duration, steps, done, ...extra }; }
function f(title, left, right, extra = {}) { return { title, left, right, ...extra }; }
function g(term, english, meaning, why, example, sources = []) { return { term, english, meaning, why, example, sources }; }

const GLOSSARIES = [
  [
    g("생성형 AI", "Generative AI", "학습한 패턴을 바탕으로 새로운 텍스트·이미지·코드를 만들어내는 AI입니다.", "기존 데이터를 분류하는 AI와 달리 초안과 설명을 만들 수 있지만, 사실 확인과 통제가 필요합니다.", "회의 원문을 읽고 요약 초안을 만든 뒤 사람이 검토합니다."),
    g("LLM", "Large Language Model", "아주 많은 텍스트로 학습해 다음에 올 말의 가능성을 계산하는 언어 모델입니다.", "문장을 잘 만들지만 회사 규칙이나 최신 사실을 자동으로 보장하지는 않습니다.", "회의에서 결정·담당자·기한 후보를 구조화합니다."),
    g("Agent", "Goal + State + Tools + Loop", "목표를 받아 현재 상태를 보고, 도구를 선택하고, 결과를 확인하며 다음 행동을 정하는 실행 구조입니다.", "한 번의 답변이 아니라 여러 단계 업무를 안전하게 이어가기 위해 필요합니다.", "파일 읽기 → 요약 → 검증 → 승인 → 기록", ["https://docs.langchain.com/oss/python/langchain/overview"]),
    g("Harness Engineering", "Instructions + Tools + Tests", "모델 주변에 지시문·도구·권한·테스트·관측 장치를 설계하는 방식입니다.", "같은 모델도 어떤 실행 환경과 검증 루프에 넣느냐에 따라 업무 신뢰도가 달라집니다.", "Codex·Claude에 작은 작업을 주고 테스트와 diff로 결과를 확인합니다.")
  ],
  [
    g("Tool Calling", "Structured Tool Request", "모델이 자유문장 대신 도구 이름과 인자를 구조화해 요청하는 방식입니다.", "파일·API·DB 접근을 허용된 행동으로 제한할 수 있습니다.", "read_public_text(path=...) 요청을 만들고 실행기는 따로 검증합니다."),
    g("Schema", "Data Contract", "입력과 출력에 어떤 필드가 필요하고 어떤 타입인지 정한 계약입니다.", "모델 출력이 흔들려도 프로그램이 처리할 수 있는 경계를 만듭니다.", "path는 문자열, action_items는 배열, due는 날짜 또는 null"),
    g("Validation", "Contract Check", "실행 전에 입력이 Schema와 정책을 지키는지 검사하는 단계입니다.", "잘못된 경로·누락 필드·허용되지 않은 도구를 실제 실행 전에 막습니다.", "허용 확장자가 txt/md가 아니면 validation_error로 중단"),
    g("Side Effect", "External Change", "파일 쓰기·메일 발송·DB 변경처럼 외부 상태를 바꾸는 행동입니다.", "실패 후 재시도하면 중복 실행될 수 있어 승인과 중복 방지가 필요합니다.", "회의 요약을 Slack에 게시하는 행동은 승인 뒤 한 번만 실행합니다.")
  ],
  [
    g("Transcript", "Speech as Text", "음성 내용을 시간 순서대로 문자로 옮긴 기록입니다.", "요약보다 먼저 원문 근거를 보존해야 잘못된 결정을 추적할 수 있습니다.", "회의 발언과 타임스탬프를 함께 저장합니다."),
    g("Segment", "Timed Utterance", "Transcript를 시작·종료 시각이 있는 짧은 발화 단위로 나눈 것입니다.", "긴 회의를 자르고 특정 주장에 근거 시각을 연결할 수 있습니다.", "41.2–48.7초의 ‘금요일까지 초안’ 발화"),
    g("Golden Dataset", "Reference Examples", "정답 또는 검토 기준이 붙은 소량의 대표 예시 모음입니다.", "프롬프트·모델을 바꿀 때 좋아졌는지 같은 입력으로 비교할 수 있습니다.", "정상 회의·무음·모호한 기한·근거 누락 5건"),
    g("Evidence", "Source Grounding", "결론이나 Action Item이 어디에서 나왔는지 가리키는 원문 근거입니다.", "요약이 자연스러워도 원문과 다르면 업무 사고로 이어질 수 있습니다.", "Action Item마다 segment_id를 연결합니다.")
  ],
  [
    g("Runtime", "Execution Environment", "코드가 실제로 실행되는 Python·운영체제·패키지 환경입니다.", "같은 코드도 Runtime이 다르면 import와 경로 오류가 발생할 수 있습니다.", "python3 --version과 실행 경로를 먼저 확인합니다."),
    g("Interpreter", "Selected Python", "VS Code나 Notebook이 사용할 특정 Python 실행 파일입니다.", "Terminal과 Notebook이 다른 Python을 쓰면 설치한 패키지를 찾지 못합니다.", ".venv/bin/python을 VS Code Interpreter로 선택합니다."),
    g("Virtual Environment", "Isolated Packages", "프로젝트별 Python 패키지를 격리하는 폴더입니다.", "수업 패키지가 다른 프로젝트와 충돌하지 않고 재현성을 높입니다.", "python3 -m venv .venv 후 같은 환경에서 설치·실행합니다."),
    g("Repository", "Versioned Project Folder", "코드·문서·데이터와 변경 이력을 함께 관리하는 프로젝트 폴더입니다.", "무엇을 바꿨고 언제 동작했는지 Git으로 설명할 수 있습니다.", "src·tests·data·materials 폴더를 하나의 저장소로 관리합니다.")
  ],
  [
    g("Planner", "Next-action Selector", "현재 요청을 보고 다음에 사용할 도구와 인자를 정하는 부분입니다.", "모델이 없어도 규칙 기반 Planner로 실행 구조를 먼저 검증할 수 있습니다.", "‘txt를 읽어줘’에서 read_public_text와 path를 추출합니다."),
    g("Executor", "Validated Runner", "Planner의 요청을 다시 검사한 뒤 실제 도구 함수를 실행하는 부분입니다.", "모델의 제안과 실제 권한을 분리해 안전 경계를 만듭니다.", "Registry에 있는 허용 도구만 호출합니다."),
    g("Timeout", "Maximum Wait", "도구가 응답하지 않을 때 기다릴 최대 시간입니다.", "무한 대기 때문에 수업과 서비스 전체가 멈추는 것을 방지합니다.", "10초를 넘으면 timeout_error로 기록하고 fallback을 선택합니다."),
    g("Idempotency", "Same Request, One Effect", "같은 요청을 여러 번 실행해도 외부 결과가 한 번만 생기게 하는 성질입니다.", "재시도·중단 후 재개에서 메일·게시글·결제가 중복되는 것을 막습니다.", "request_id가 이미 성공했으면 저장된 결과를 반환합니다.")
  ],
  [
    g("Local LLM", "Model on My Computer", "외부 API가 아니라 내 PC에서 실행되는 언어 모델입니다.", "무료 실습과 데이터 통제에 유리하지만 설치·메모리·속도 제약이 있습니다.", "Ollama에서 qwen3 계열 작은 모델을 실행합니다."),
    g("Provider", "Model Access Method", "OpenAI·Anthropic·Ollama처럼 모델을 호출하는 서비스 또는 실행 방식입니다.", "Provider마다 URL·인증·응답 형식이 달라 코드 결합을 줄여야 합니다.", "local provider와 fixture provider를 같은 인터페이스로 부릅니다."),
    g("Adapter", "Common Interface", "서로 다른 Provider 호출 방식을 하나의 공통 함수로 감싸는 계층입니다.", "모델을 교체해도 나머지 Workflow를 바꾸지 않게 합니다.", "generate(prompt) 함수 뒤에 Ollama·LM Studio·fixture를 숨깁니다."),
    g("Fallback", "Alternative Path", "주 경로가 실패했을 때 학습이나 업무를 계속할 대체 경로입니다.", "설치와 네트워크 문제 때문에 전체 실습이 멈추지 않게 합니다.", "Local LLM이 없으면 고정 JSON fixture로 Schema·Graph 실습을 계속합니다.")
  ],
  [
    g("State", "Workflow Memory", "Graph의 각 단계가 읽고 갱신하는 구조화된 현재 상태입니다.", "대화 전체를 저장하는 대신 다음 단계에 필요한 값만 명시적으로 전달합니다.", "transcript·draft·errors·approval·status를 필드로 둡니다."),
    g("Node / Edge", "Step / Route", "Node는 한 책임의 작업이고 Edge는 다음 단계로 가는 조건입니다.", "복잡한 업무를 작은 단계와 명시적인 분기로 설명할 수 있습니다.", "validate Node가 READY면 review, 오류면 retry 또는 failed로 이동합니다."),
    g("Checkpoint", "Saved State", "Workflow의 중간 State를 저장해 나중에 같은 지점에서 이어갈 수 있게 합니다.", "긴 작업·사람 승인·오류 복구를 처음부터 다시 하지 않게 합니다.", "thread_id로 저장된 State를 불러와 승인 뒤 재개합니다.", ["https://docs.langchain.com/oss/python/langgraph/persistence"]),
    g("HITL", "Human in the Loop", "중요한 결정이나 외부 변경 전에 사람이 확인하고 승인·수정·거절하는 단계입니다.", "모델의 불확실성과 조직 책임을 사람의 판단으로 연결합니다.", "낮은 confidence Action Item은 reviewer가 근거를 보고 승인합니다.", ["https://docs.langchain.com/oss/python/langgraph/interrupts"])
  ],
  [
    g("STT", "Speech to Text", "사람의 음성을 문자와 타임스탬프로 변환하는 기술입니다.", "회의 내용을 검색·요약·평가하려면 먼저 검토 가능한 텍스트가 필요합니다.", "faster-whisper가 audio를 segment 배열로 변환합니다."),
    g("Trace", "Execution Record", "한 요청 안에서 Node·LLM·Tool이 어떤 입력과 출력을 냈는지 연결한 실행 기록입니다.", "느린 단계·실패 원인·사람 수정량을 실제 실행 단위로 찾을 수 있습니다.", "LangSmith run tree에서 Graph 아래 child run을 확인합니다."),
    g("Dataset / Experiment", "Fixed Inputs / Compared Runs", "Dataset은 평가 입력 묶음이고 Experiment는 같은 입력으로 특정 버전을 실행한 결과 묶음입니다.", "프롬프트·모델·Graph 변경 전후를 재현 가능하게 비교합니다.", "day2-v1 데이터셋에 baseline과 candidate를 각각 실행합니다.", ["https://docs.langchain.com/langsmith/evaluation"]),
    g("Release Gate", "Ship or Hold Rule", "품질·안전·지연시간 기준을 모두 통과할 때만 배포를 허용하는 규칙입니다.", "평가 점수를 실제 운영 결정인 READY 또는 HOLD로 바꿉니다.", "Schema 98%·근거 연결 90%·오발행 0건을 모두 만족해야 READY입니다.")
  ]
];

const MODULES = [
  {
    time: '09:00–12:00 · PART 1/3',
    short: 'OPENING',
    title: 'Agent 시대의 문제정의',
    subtitle: '강사의 산업 경험과 40시간 PBL 제품을 연결하고, 오늘의 학습 계약을 함께 세웁니다.',
    output: '개인 목표 · 환경 진단 · Agent 판단 기준',
    outcome: '수업이 끝날 때 “어떤 모델을 썼는가”보다 “어떤 업무를 어떤 증거와 통제로 바꿨는가”를 설명합니다.',
    accent: C.cyan,
    concepts: [
      c('머신러닝·딥러닝·LLM을 거쳐, 지금은 Agent 제품을 만듭니다', '', '', {
        profileCareer: true,
        lead: '차성재 · 무신사 Agentic AI Side PM · 서울시립대/아주대학교 AI 부문 겸임교수',
        rows: [
          ['금융', '정형 데이터\nAutoML·MLOps', '은행·카드·보험사의 예측과 의사결정을 자체 AutoML 솔루션으로 자동화', '에이젠글로벌\nML Team Leader'],
          ['의료', '대장내시경 영상\nDL·CVOps', '실시간 영상에서 용종 탐지·진단을 보조하는 의료 AI 서비스를 제작·운영', '아이넥스코퍼레이션\nAI Engineer'],
          ['교육', '말하기·글쓰기·상담\nLLMOps·AICC', '7만 명 영어 평가를 3–5일에서 약 10초로 단축하고 상담 전·중·후 AI를 총괄', '크레버스\nAI Engineer·AI PM'],
          ['이커머스', '고객·상품 맥락\nAgentic AI', 'AID Chat·쇼핑 탐색·Voice·AI 해설·SEO/GEO 등 고객 접점 Agent 제품을 담당', '무신사\nAgentic AI Side PM'],
        ],
        bottom: '강의·멘토 · 2개 대학원 AI 겸임교수 / KT·Kakao AX / 연구 AX / 재직자·취준생 AI Native / 출제·심사',
      }),
      c('40시간 뒤 남아야 할 것', '“AI를 써봤다”가 아니라 “검증 가능한 업무 Agent를 운영했다”.', 'STT·LLM·Tool / LangChain·LangGraph / Human Approval·LangSmith·Git 증거'),
      c('재직자와 구직자는 같은 기술을 다르게 증명한다', '재직자는 도입 통제, 구직자는 재현 가능한 포트폴리오를 강조한다.', '재직자: 보안·업무시간·승인 / 구직자: README·테스트·Git history / 공통: 실제 demo'),
      c('Chatbot과 Agent를 가르는 질문', '모델이 답했는가가 아니라 상태를 보고 도구를 선택·검증했는가를 본다.', '대화 생성 / 도구 선택 / 결과 관찰 / 다음 행동·중단 판단'),
      c('좋은 Agent의 첫 기준은 통제 가능성', '정확한 한 번보다 실패해도 안전하게 멈추는 흐름이 먼저다.', '허용 도구 / schema / timeout·retry / 승인 / trace·평가'),
    ],
    procedures: [
      p('수업은 네 번의 움직임을 반복합니다', ['강사 화면을 먼저 봅니다', '완성 결과와 클릭·명령 순서를 먼저 확인합니다.'], ['같은 화면을 따라 만듭니다', '한 단계씩 멈추며 내 화면과 비교합니다.'], ['일부러 한 번 틀려봅니다', '입력값 하나를 바꿔 실패 메시지를 직접 확인합니다.'], ['다시 실행해 확인합니다', '원상 복구한 뒤 test와 결과 파일을 남깁니다.'], {
        variant: 'class_cycle',
        lead: '먼저 보고, 그대로 따라하고, 일부러 틀려본 뒤, 성공 증거를 남깁니다.',
      }),
      p('막히면 “안 돼요”보다 네 가지를 알려주세요', ['첫 오류 문장', '화면에 보이는 그대로'], ['직전 행동', '누른 버튼 또는 입력한 명령'], ['내 실행 환경', '운영체제와 Python 버전'], ['기대한 결과', '원래 나와야 했던 화면'], {
        variant: 'help_request',
        example: '예시  |  macOS · Python 3.11 · pip install 뒤 ModuleNotFoundError · notebook가 열릴 것으로 기대',
      }),
      p('실습 속도가 달라도, 다음 행동은 분명합니다', ['바로 다시 실행할 수 있어요', '혼자 한 번 더 실행하고 결과를 비교합니다.', '성공 화면 1장'], ['장표를 따라가는 중이에요', '현재 표시된 단계까지만 끝내고 강사 화면과 비교합니다.', '현재 단계 체크'], ['오류에서 멈췄어요', '채팅창에 첫 오류 한 줄을 남긴 뒤 복구 파일에서 다시 시작합니다.', '오류 문장 1줄'], ['먼저 끝냈어요', '실패 입력을 하나 더 넣고 왜 막혔는지 기록합니다.', '반례와 이유'], {
        variant: 'pace_choice',
        lead: '빠르거나 느린 것이 아니라, 지금 내 상태에 맞는 행동 하나를 고르면 됩니다.',
        bottom: '막혔을 때 조용히 기다리지 않아도 됩니다. 첫 오류 한 줄이 가장 좋은 질문입니다.',
      }),
      p('실습 완료는 “작동했다”가 아니라 “다시 확인할 수 있다”입니다', ['결과 파일이 저장되어 있습니다'], ['같은 명령을 다시 실행해도 성공합니다'], ['test 또는 schema 검사가 통과합니다'], ['왜 안전한지 한 문장으로 설명할 수 있습니다'], {
        variant: 'proof',
        lead: '다음 네 가지 중 하나라도 없으면, 아직 실습이 끝난 것이 아닙니다.',
        terminal: '$ python3 -m src.day1_agent\nstatus: SUCCESS\n\n$ python3 -m pytest -q\n10 passed\n\n$ git status --short\nM src/day1_agent.py',
        bottom: '오늘 남길 것  |  실행 화면 1장 + test 결과 1줄 + 내가 설명한 안전 기준 1문장',
      }),
      p('강사 Harness Engineering 데모', ['SPEC', '작업을 파일로 명시'], ['AGENT', 'Codex·Claude 실행'], ['DIFF', '변경 범위 검토'], ['TEST', '증거 없으면 미완료']),
    ],
    screenshots: [
      s('Codex CLI · 저장소를 읽고 실행하는 Agent', 'codex-cli-docs-official.png', 'OpenAI Codex CLI 공식 문서 화면', 'https://developers.openai.com/codex/cli/', ['작업 디렉터리에서 시작', '요구사항을 파일·테스트로 구체화', 'diff와 명령 결과를 사람이 검토', '학생 필수 경로는 로컬 코드']),
      s('Claude Code · 터미널 중심 Harness', 'claude-code-overview-official.png', 'Anthropic Claude Code 공식 Overview', 'https://docs.anthropic.com/en/docs/claude-code/overview', ['코드베이스 맥락 읽기', '작업을 작은 단계로 지시', '변경·테스트·설명 확인', '구독·정책은 별도 확인']),
      s('실제 VS Code 저장소 · 수업의 출발 화면', 'vscode-repo-workspace-local.png', '로컬에서 연 강의용 저장소', 'local://llm-agent-and-workflow-automation', ['src·tests·materials를 먼저 찾기', '.env는 열지 않기', '강사와 같은 폴더 구조 확인', '실습 시작 화면으로 사용']),
      s('실제 Agent 코드 · 표준 라이브러리부터', 'vscode-day1-agent-local.png', 'VS Code에서 연 src/day1_agent.py', 'local://src/day1_agent.py', ['처음에는 framework 없이 제어 루프', '읽기 도구만 허용', '오류를 결과 객체로 정규화', 'Ollama는 선택 adapter']),
    ],
    examples: [
      e('작업 요청을 먼저 spec으로 고정', 'goal: 안전한 파일 읽기 Agent\ninput: 공개 txt/md\nallowed_tools: [read_public_text]\nstop: validation_error | success\nevidence: pytest + output json', ['목표를 한 문장으로', '입력·출력 형식', '허용 행동', '중단과 완료 증거']),
      e('Agent의 최소 반복 구조', 'while state.status == \"RUNNING\":\n    call = planner(state)\n    checked = validate(call)\n    result = execute(checked)\n    state = observe(state, result)\nreturn state', ['판단과 실행을 분리', '매 step 결과 관찰', '무한 반복 금지', 'state로 감사 가능']),
      e('Day 1 완료조건을 명령으로 표현', 'python3 -m src.day1_agent\npython3 -m pytest -q\ngit status --short\ngit diff -- src tests\n\n# success: 10 passed', ['실행 결과', '테스트', '변경 범위', '설명 가능한 diff']),
      e('저장소가 말해주는 역할 분리', 'src/        # 실행 코드\ntests/      # 실패·정상 증거\nmaterials/  # 따라하기 notebook\ndata/       # 공개·합성 입력\nslides/     # 수업 화면', ['코드와 데이터 분리', '노트북과 모듈 분리', '테스트를 1급 산출물로', '장표와 파일명 연결']),
      e('강사 회의음성 Demo · 실패해도 수업은 계속', 'python3 -m src.meeting_demo \\\n  --audio data/demo_meeting.wav \\\n  --transcript data/demo_meeting_transcript.txt \\\n  --out output/day1-demo\n\n# outputs\n# transcript.json + meeting_result.json', ['오디오가 있으면 Local STT', '실패하면 같은 60초 transcript', '사전 생성 JSON 즉시 확인', '자동 메일 false·사람 승인 true']),
      e('Exit ticket도 구조화 데이터다', '{\n  \"agent_difference\": \"...\",\n  \"first_validation\": \"...\",\n  \"human_reason\": \"...\",\n  \"confidence\": 0.0\n}', ['세 문장으로 회수', '다음 날 복습 데이터', '모호한 답은 재질문', '점수가 아닌 진단']),
    ],
    labs: [
      l('실습 1 · 강사 Demo를 보고 내 업무를 고릅니다', '06 MIN', ['강사가 준비한 짧은 회의 음성을 코드에 넣습니다.', '전사문·회의 요약·할 일 JSON이 만들어지는 화면을 봅니다.', '자동 메일 발송이 차단되는 결과를 확인합니다.', '같은 형식으로 내가 자동화할 일을 한 문장으로 적습니다.'], '입력 1개 + 결과 1개 + 금지 행동 1개', {
        example: '강사 시연  |  demo_meeting.wav → transcript.json → meeting_result.json / 자동 메일 발송은 하지 않음',
        note: '구두 예시로 끝내지 않는다. 강사는 data/demo_meeting.wav 또는 본인이 녹음한 약 1분 WAV를 넣고 실제 코드 결과를 먼저 보여준다. 네트워크·모델 실패에 대비해 data/meeting_sample_ko.txt와 사전 생성 JSON을 즉시 여는 fallback을 준비한다. 온라인 개인 실습이므로 수강생에게 발표나 공개를 요구하지 않는다.',
      }),
      l('실습 2 · 오늘 사용할 예시를 혼자 정합니다', '05 MIN', ['재직자는 회사명·고객 정보를 뺀 반복 업무를 고릅니다.', '구직자는 제공된 공개·합성 예시 중 하나를 고릅니다.', '입력 자료와 원하는 결과를 한 줄씩 적습니다.', '이후 실습에서 같은 예시를 계속 사용합니다.'], '내가 사용할 예시 한 문장', {
        example: '회의 음성 → 결정·담당자·기한이 있는 회의 기록',
        note: '온라인 개인 실습이다. 선택한 업무나 구직 상태를 공개하게 하지 않고, 개인 notebook에만 적게 한다. 발표는 진행하지 않는다.',
      }),
      l('실습 3 · 최종 데모 역산', '08 MIN', ['최종 입력 한 건을 정한다.', '보여줄 출력 JSON을 그린다.', '사람이 승인할 지점을 표시한다.', 'LangSmith에서 보고 싶은 실패를 적는다.'], '입력→출력→승인 sketch'),
      l('실습 4 · 환경 신호등', '06 MIN', ['Python·VS Code·Git 설치 여부를 표시한다.', '관리자 권한 여부를 표시한다.', 'RAM·디스크 제약을 적는다.', 'GREEN/YELLOW/RED lane을 선택한다.'], '개인 환경 진단표'),
      l('실습 5 · Agent를 쉬운 말로 적기', '07 MIN', ['Chatbot을 한 문장으로 적습니다.', 'Agent가 도구를 쓰는 순간을 추가합니다.', '실패했을 때 멈추거나 다시 시도하는 행동을 추가합니다.', '내 문장을 다시 읽고 어려운 단어를 하나 줄입니다.'], 'Agent 설명 2문장', {
        example: 'Agent는 답만 만드는 것이 아니라, 필요한 도구를 고르고 결과를 확인한 뒤 다음 행동을 정합니다.',
      }),
    ],
    pitfalls: [
      f('실패 1 · 문제 범위가 너무 크다', ['전사·요약·메일·ERP를 한 번에', '사용자가 여러 명', '정답 기준 없음', '데모 입력도 미정'], ['한 사용자·한 입력', '한 구조화 출력', '한 승인 행동', '한 개의 golden example']),
      f('실패 2 · 실제 회사 데이터를 가져온다', ['고객명·이메일 포함', '비공개 회의 업로드', '회사 repo token 사용', '교육 계정에 trace 전송'], ['공개·합성 데이터', '이름·금액 범주화', 'sandbox repo', '민감 필드 masking']),
      f('실패 3 · 모델 선택부터 시작한다', ['벤치마크 순위만 비교', '큰 모델 다운로드 대기', '문제 정의 지연', '실패 조건 미정'], ['fixture로 흐름 먼저', '작은 모델은 선택', '계약과 test 우선', 'provider 교체 가능']),
      f('실패 4 · “돌아갔다”로 완료한다', ['스크린 한 장만 제출', 'test 없음', 'diff 설명 불가', '재실행 절차 없음'], ['Run All', 'pytest 결과', 'Git diff·commit', '다른 사람이 재현']),
    ],
    tracks: [
      { title: '재직자 · 현업 PoC 승인 관점', leftTitle: '현업 질문', rightTitle: '남길 증거', left: ['어떤 시간을 줄이나?', '어디서 사람이 승인하나?', '어떤 데이터가 나가나?', '장애 시 누가 복구하나?'], right: ['before/after 시간 가설', 'approval policy', 'data boundary', '운영 runbook'] },
      { title: '구직자 · 포트폴리오 평가 관점', leftTitle: '면접 질문', rightTitle: 'repo 증거', left: ['왜 Agent인가?', '실패를 어떻게 다뤘나?', '품질을 어떻게 측정했나?', '본인 기여는 무엇인가?'], right: ['problem statement', 'failure tests', 'evaluation dataset', '작은 commit history'] },
    ],
    checkpoint: { title: 'Gate 1 · 범위를 줄일 수 있습니까?', prompt: '상황: “회의 업무를 전부 자동화하자”는 요청을 받았습니다. 오늘 만들 수 있는 한 조각으로 잘라봅니다.', questions: ['사용자 한 명과 입력 한 건을 무엇으로 정할까?', 'AI가 하면 안 되는 행동을 어디까지 막을까?', '완료를 증명할 파일·test·demo는 무엇일까?'] },
  },
  {
    time: '09:00–12:00 · PART 2/3',
    short: 'TOOL CALLING',
    title: 'Tool Calling의 안전 경계',
    subtitle: '모델이 만든 호출을 바로 실행하지 않고 schema·권한·정책·오류로 감쌉니다.',
    output: 'Tool schema · SafeToolExecutor · 정상/실패 테스트',
    outcome: '허용된 도구와 인자만 실행하고, 모든 실패를 재현 가능한 error_code로 돌려주는 계약을 만듭니다.',
    accent: C.blue,
    concepts: [
      c('Tool Calling은 실행 권한의 계약', '모델의 JSON은 제안일 뿐, 실행 허가는 애플리케이션이 결정한다.', 'name·description / arguments schema / allowlist·policy'),
      c('Schema는 문서이자 방화벽', '필수 필드·타입·열거값·추가 필드 금지를 코드로 고정한다.', 'required / type·enum / additional properties'),
      c('Registry가 실행 가능한 세계를 제한한다', '모델이 아는 도구와 실제로 등록된 도구를 분리한다.', 'TOOL_SCHEMAS / TOOL_REGISTRY / unknown tool 차단'),
      c('최소 권한은 기능을 줄이는 설계', '범용 shell보다 목적별 좁은 도구가 더 안전하고 평가하기 쉽다.', 'read_public_text / 확장자 제한 / workspace 경계'),
      c('Validation은 실행 전에 끝낸다', '누락·타입·예상 밖 인자는 side effect 전에 거부한다.', 'missing / unexpected / wrong type'),
      c('오류도 정상적인 결과 형식이다', 'traceback 대신 ok·error_code·message를 downstream에 전달한다.', 'VALIDATION_ERROR / NOT_FOUND / POLICY_BLOCKED / TOOL_RUNTIME_ERROR'),
      c('Read와 Write는 위험도가 다르다', '외부 쓰기는 승인·중복 방지·감사 로그가 추가로 필요하다.', 'read: 자동 가능 / draft: 검토 / publish: 승인 필수'),
      c('Timeout과 Retry는 실패 종류를 본다', '일시 오류만 제한적으로 재시도하고 정책 오류는 즉시 중단한다.', 'transient / permanent / policy / human-needed'),
      c('Idempotency가 중복 side effect를 막는다', '같은 request_id·call_id의 성공 결과를 다시 쓰지 않는다.', 'stable key / cache / resume-safe'),
      c('Audit event가 설명 가능성을 만든다', '누가 무엇을 요청했고 무엇이 차단됐는지 구조화해 남긴다.', 'input hash / tool·args / decision·result / timestamp'),
    ],
    procedures: [
      p('Tool 호출의 4단계', ['PLAN', '도구·인자 제안'], ['VALIDATE', 'schema·policy'], ['EXECUTE', '등록 함수만'], ['OBSERVE', '결과·오류 기록']),
      p('Tool Prompt와 Schema를 만드는 순서', ['SYSTEM', '역할·허용·금지 행동'], ['TASK', '입력과 원하는 결과'], ['TOOLS', 'name·설명·인자 schema'], ['EXAMPLE', '정상 호출·차단 호출']),
      p('파일 도구의 경로 검증', ['JOIN', 'workspace+path'], ['RESOLVE', '절대경로 정규화'], ['CHECK', 'root 하위인지'], ['ALLOW', '확장자·존재']),
      p('오류 분류 결정', ['정책', '재시도 없음'], ['사용자', '입력 수정'], ['일시', '제한 retry'], ['미지', '중단·trace']),
      p('테스트 설계 순서', ['정상', 'happy path'], ['경계', '최소·최대'], ['공격', 'path traversal'], ['중복', 'cached result']),
      p('쓰기 도구의 승인 경계', ['DRAFT', '변경 내용 생성'], ['PREVIEW', 'diff·대상 표시'], ['APPROVE', '사람 event'], ['WRITE', 'idempotency key']),
    ],
    screenshots: [
      s('Ollama API · 호출 형식을 공식 문서로 확인', 'ollama-api-official.png', 'Ollama API Introduction 공식 화면', 'https://docs.ollama.com/api/introduction', ['base URL 확인', 'request/response 형식', 'timeout·stream 선택', 'adapter 뒤에 감추기']),
      s('GitHub REST · 인증은 코드와 분리', 'github-rest-auth-official.png', 'GitHub REST authentication 공식 문서', 'https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api', ['token은 환경 변수', '학생 필수 실습은 dry-run', '최소 권한 확인', '화면에 secret 노출 금지']),
      s('pytest · 실패를 재현하는 가장 작은 도구', 'pytest-getting-started-official.png', 'pytest Get Started 공식 문서', 'https://docs.pytest.org/en/stable/getting-started.html', ['test_ 함수 규칙', 'assert로 계약 고정', '정상·예외 함께', '짧은 명령으로 반복']),
      s('실제 실행 · 10 tests 통과', 'vscode-pytest-10-passed-local.png', 'VS Code 통합 터미널의 실제 pytest 결과', 'local://python3-m-pytest-q', ['.......... 10개 test', '[100%] 완료', '실행 시간 확인', '완료 증거로 캡처']),
    ],
    examples: [
      e('도구 schema · 허용 입력만', 'TOOL_SCHEMAS = {\n  \"read_public_text\": {\n    \"required\": {\"path\": str},\n    \"description\": \"공개 txt/md 읽기\"\n  }\n}', ['한 도구 한 책임', '필수 인자 명시', '설명은 모델용', '실행 함수와 분리']),
      e('예상 밖 인자를 차단', 'required = schema[\"required\"]\nmissing = [k for k in required if k not in args]\nunexpected = set(args) - set(required)\nif missing or unexpected:\n    raise ToolValidationError()', ['누락 검사', '추가 필드 금지', '실행 전 차단', '오류 코드로 변환']),
      e('경로 이탈을 막는 guard', 'root = workspace.resolve()\ncandidate = (root / path).resolve()\nif root != candidate and root not in candidate.parents:\n    raise ToolValidationError(\"outside workspace\")', ['../ 정규화 후 검사', '절대경로 비교', 'symlink 고려', '테스트로 공격 재현']),
      e('오류를 공통 result로 정규화', 'return ToolResult(\n  ok=False,\n  tool=tool_name,\n  error_code=\"POLICY_BLOCKED\",\n  message=str(exc)\n)', ['exception 경계', '안정된 error_code', '사용자 메시지', 'trace에는 상세 stack']),
      e('Tool Calling Prompt의 최소 구조', 'SYSTEM: 허용된 도구만 사용한다. 메일은 보내지 않는다.\nTASK: 회의 문서를 읽고 할 일을 찾는다.\nTOOLS: read_public_text(path: str)\nOUTPUT: 필요한 경우 tool call JSON만 반환한다.\nEXAMPLE: {\"name\":\"read_public_text\",\"arguments\":{\"path\":\"data/meeting.txt\"}}', ['역할과 금지 행동', '입력·목표', '도구 설명·schema', '정상 예시 한 건']),
      e('실패 테스트 네 가지', 'def test_unknown_tool(): ...\ndef test_missing_argument(): ...\ndef test_path_traversal(): ...\ndef test_duplicate_call_cached(): ...', ['허용되지 않은 도구', '필수 인자 누락', 'workspace 이탈', '같은 호출 중복']),
    ],
    labs: [
      l('실습 1 · 도구 한 개를 schema로', '08 MIN', ['업무 동사를 한 개 고른다.', '필수 인자를 1–2개로 제한한다.', '타입과 허용값을 적는다.', '정상 호출 예시를 JSON으로 쓴다.'], 'tool schema 1개'),
      l('실습 2 · 잘못된 호출 3개 만들기', '08 MIN', ['unknown tool 호출을 만든다.', '필수 인자를 하나 지운다.', '예상 밖 인자를 하나 넣는다.', '각 error_code를 예상한다.'], '실패 fixture 3개'),
      l('실습 3 · workspace guard 읽기', '09 MIN', ['정상 상대경로를 넣는다.', '../를 포함한 경로를 넣는다.', '.py 확장자를 넣는다.', '어느 단계에서 차단되는지 표시한다.'], '정상 1 + 차단 2'),
      l('실습 4 · ToolResult 계약 검증', '08 MIN', ['성공 result 필드를 적는다.', '실패 result 필드를 적는다.', 'downstream이 exception을 몰라도 되는 이유를 쓴다.', 'needs_human_review 조건을 정한다.'], '공통 result 표'),
      l('실습 5 · pytest 한 건 추가', '10 MIN', ['tests 파일을 연다.', '실패 사례를 함수로 추가한다.', 'pytest -q를 실행한다.', '실패→수정→통과를 캡처한다.'], '새 test 1개 + 통과 화면'),
    ],
    pitfalls: [
      f('실패 1 · 모델 JSON을 바로 실행', ['schema 검증 생략', '임의 도구 이름', '추가 인자 허용', 'side effect 직행'], ['plan은 제안', 'validator가 허가', 'registry 함수만', '쓰기 전 preview']),
      f('실패 2 · 범용 shell 도구 제공', ['rm·curl까지 가능', '명령 문자열 해석', '권한 범위 불명', '평가 불가능'], ['목적별 함수', 'typed arguments', '최소 파일 범위', '정상·실패 test']),
      f('실패 3 · 모든 오류를 retry', ['정책 오류 반복', '비용·시간 증가', '중복 쓰기', '원인 은폐'], ['오류 class 분류', '일시 오류만 retry', 'max attempts', '중단 후 사람 검토']),
      f('실패 4 · 토큰을 notebook에 기록', ['cell output 노출', 'Git commit 포함', '화면 캡처 유출', '교육 계정 공유'], ['.env.example만', '실제 값은 환경 변수', 'sandbox token', '캡처 전 비식별']),
    ],
    tracks: [
      { title: '재직자 · Tool 권한 승인표', leftTitle: '자동 허용', rightTitle: '사람 승인', left: ['공개 문서 읽기', '로컬 parsing', 'schema validation', 'draft 저장'], right: ['메일·Issue 게시', '고객정보 접근', '결제·삭제', '비공개 repo 쓰기'] },
      { title: '구직자 · Tool 설계 설명법', leftTitle: '코드만 보여주기', rightTitle: '면접에서 설명하기', left: ['함수 목록', '성공 demo', '프레임워크 이름', '모델 이름'], right: ['위험과 권한', '실패 분류', 'test evidence', '확장 trade-off'] },
    ],
    checkpoint: { title: 'Gate 2 · 이 Tool Call을 실행할까요?', prompt: '상황: 등록되지 않은 send_email 도구에 예상 밖의 admin=true 인자가 들어왔습니다.', questions: ['실행·차단·사람 검토 중 무엇을 선택할까?', 'downstream에 돌려줄 error_code는 무엇일까?', '감사 event에 어떤 요청·판단·결과를 남길까?'] },
  },
  {
    time: '09:00–12:00 · PART 3/3',
    short: 'PBL & K-DATA',
    title: '한국어 PBL 문제와 데이터',
    subtitle: '실제처럼 보이되 공개·비식별·재현 가능한 한국어 자료로 프로젝트 범위를 정합니다.',
    output: 'K-Work Copilot canvas · dataset card · golden example',
    outcome: '한국어 회의/업무 데이터를 안전하게 선택하고, 제품 가치·정답 기준·실패 비용을 한 장의 PBL canvas로 고정합니다.',
    accent: C.purple,
    concepts: [
      c('PBL은 기술 목록이 아니라 사용자 문제에서 시작', 'STT·LLM·LangGraph를 모두 쓰되, 한 사용자의 한 업무 흐름에 묶는다.', '사용자·상황 / 반복 입력 / 원하는 결정·행동'),
      c('K-Work Copilot의 공통 입력', '강사는 17분 합성 회의 전체를 보여주고, 수강생은 같은 파일의 2–3분 구간부터 검증한다.', 'meeting_sample_ko_12min.wav / timestamp transcript / expected JSON·Dataset Card'),
      c('한국어는 띄어쓰기보다 업무 맥락이 어렵다', '존칭·생략·동음어·숫자·날짜·담당자 모호성을 별도 오류로 본다.', '화자 생략 / “다음 주” 기준일 / 제품명·약어 / 책임자 추론 금지'),
      c('실제 데이터처럼 보이는 최소 조건', '자연스러운 맥락·역할·결정·마감이 있으면서 개인 식별정보는 없어야 한다.', '가상 조직 / 역할명 / 합성 금액 범주 / 공개 가능한 업무 관계'),
      c('데이터 공개와 사용 허가는 다르다', '웹에서 보인다는 사실만으로 재배포·수업 배포가 허용되지는 않는다.', '이용 조건 / 다운로드·신청 / 재배포 범위 / 출처 기록'),
      c('Dataset Card가 실습을 재현하게 한다', '출처·버전·샘플링·민감성·변환을 한 페이지에 남긴다.', 'source URL / collected_at / license·terms / preprocessing·limitations'),
      c('Transcript schema가 STT와 LLM을 연결', '텍스트만 넘기지 말고 segment·time·speaker·quality flag를 유지한다.', 'start·end / speaker / text / no_speech·language'),
      c('Evidence가 요약의 근거를 고정한다', '결정과 Action Item마다 원문 segment ID를 연결한다.', 'claim / evidence_ids / confidence / needs_review'),
      c('Golden example은 작은 평가셋의 시작', '정답 한 건을 사람이 합의하면 prompt·model·parser 회귀를 비교할 수 있다.', 'input / expected JSON / rubric / known ambiguity'),
      c('가치 지표와 품질 지표를 함께 둔다', '시간 절감만큼 누락·오인·수정량·승인율을 본다.', 'minutes saved / evidence rate / human edit distance / false publish=0'),
    ],
    procedures: [
      p('공개 데이터 선택 4단계', ['DISCOVER', '공식 원자료 찾기'], ['VERIFY', '이용 조건 확인'], ['SAMPLE', '소량·목적 적합'], ['DOCUMENT', '출처·변환 기록']),
      p('한국어 업무 Prompt의 기본 구조', ['ROLE', '회의 기록 보조자'], ['INPUT', 'segment·기준일'], ['OUTPUT', 'summary·decision·action'], ['RULE', '추론 금지·근거 필수']),
      p('비식별 처리 순서', ['DETECT', '이름·연락처·ID'], ['REPLACE', '역할·범주'], ['REVIEW', '문맥 재식별'], ['LOG', '변환 규칙']),
      p('Golden set 만드는 순서', ['TRANSCRIBE', '사람 정답'], ['ANNOTATE', '결정·행동'], ['LINK', 'evidence segment'], ['AGREE', '2인 합의']),
      p('PBL canvas 네 칸', ['USER', '누가 쓰나'], ['PAIN', '무엇이 누락되나'], ['FLOW', 'AI와 사람 역할'], ['PROOF', '무엇으로 좋아졌나']),
      p('범위 자르는 질문', ['입력 1개?', '파일·텍스트'], ['출력 1개?', 'JSON·MD'], ['승인 1개?', 'publish 전'], ['평가 1개?', 'golden set']),
    ],
    screenshots: [
      s('서울 열린데이터광장 · 한국어 공공 데이터 탐색', 'seoul-open-data-official.png', '서울 열린데이터광장 공식 화면', 'https://data.seoul.go.kr/', ['공식 제공처를 먼저', '검색어·제공기관 기록', '다운로드 형식 확인', '소량 샘플부터']),
      s('국립국어원 모두의 말뭉치 · 한국어 원자료', 'korean-corpus-official.png', '국립국어원 모두의 말뭉치 화면', 'https://kli.korean.go.kr/corpus/', ['신청·이용 조건 확인', '말뭉치 종류와 목적 구분', '원문 재배포 주의', 'dataset card에 출처']),
      s('국회 회의록 빅데이터 · 실제 발화 구조', 'nanet-speech-dataset-official.png', '국회 회의록 빅데이터 공식 화면', 'https://dataset.nanet.go.kr/', ['발언자·회의 맥락', '공개 회의 기록 사례', '페이지·첨부 공개 범위 확인', '학습용 소량 사례']),
      s('Google Meet 전사 · Managed STT의 현재 위치', 'google-meet-transcript-official.png', 'Google Meet transcript 도움말', 'https://support.google.com/meet/answer/12849897', ['계정·edition 의존', '한국어 지원 여부 확인', '원문 보존·권한 정책', '수업은 local 원리 중심']),
    ],
    examples: [
      e('회의 segment schema', 'segment = {\n  \"id\": \"s12\",\n  \"start\": 41.2,\n  \"end\": 48.7,\n  \"speaker\": \"역할1\",\n  \"text\": \"금요일까지 초안을...\",\n  \"quality_flags\": []\n}', ['timestamp 유지', 'speaker는 모르면 null', '원문 text 보존', '품질 flag 별도']),
      e('Action Item에 evidence 연결', 'action = {\n  \"task\": \"FAQ 30건 정리\",\n  \"owner\": \"역할1\",\n  \"due_date\": \"2026-08-27\",\n  \"evidence_ids\": [\"s12\"],\n  \"confidence\": 0.92\n}', ['task·owner·date', '근거 segment', 'confidence 정책', '누락 시 review']),
      e('모호한 날짜는 추론하지 않는다', 'if due_text in [\"다음 주\", \"조만간\"]:\n    return {\n      \"due_date\": None,\n      \"needs_review\": True,\n      \"reason\": \"RELATIVE_DATE\"\n    }', ['기준일 필요', 'null 허용', '모호성 코드', '사람에게 질문']),
      e('한국어 회의 Prompt · 모호하면 추론하지 않기', 'SYSTEM: 한국어 회의 기록 보조자\nRULES:\n- 원문에 없는 담당자·기한을 추론하지 않는다.\n- 모호하면 null과 needs_review를 반환한다.\nINPUT: segments[] + meeting_date\nOUTPUT: MeetingResult JSON\nEVIDENCE: 모든 결정·할 일에 evidence_ids를 연결한다.', ['역할을 한 문장으로', '금지 행동을 먼저', '출력 schema 고정', '원문 근거 요구']),
      e('Dataset card 최소 필드', 'dataset:\n  source: official_url\n  collected_at: 2026-08-22\n  purpose: classroom_demo\n  contains_pii: false\n  transformations: [sampling, anonymize]\n  limitations: [synthetic_speakers]', ['출처', '수집 시점', '민감성', '변환·제한']),
      e('PBL KPI를 계산 가능한 식으로', 'evidence_rate = linked_claims / total_claims\nschema_pass = valid_outputs / all_outputs\nhuman_edit = changed_chars / draft_chars\nfalse_publish = 0', ['근거 연결률', 'schema 통과율', '사람 수정량', '오발행 0건']),
    ],
    labs: [
      l('실습 1 · 한국어 사례 후보 3개', '08 MIN', ['공식 데이터 사이트에서 검색어를 정한다.', '사례 후보를 세 개 적는다.', '업무 흐름과 가장 가까운 한 개를 고른다.', '선택 이유를 한 문장으로 쓴다.'], '후보 3개 + 선택 1개'),
      l('실습 2 · 이용 조건 확인표', '08 MIN', ['제공 기관과 URL을 기록한다.', '다운로드·신청 필요 여부를 적는다.', '재배포 가능 여부를 확인한다.', '불확실하면 강사 fixture를 선택한다.'], 'source checklist'),
      l('실습 3 · 상세 회의에서 근거 구간 찾기', '10 MIN', ['meeting_sample_ko_12min.txt를 엽니다.', '결정 1개와 정정 발언 1개를 찾습니다.', '담당·기한 Action Item 2개를 찾습니다.', '“다음 주 중”을 needs_review로 표시합니다.'], 'evidence segment 4개'),
      l('실습 4 · Golden JSON과 비교', '10 MIN', ['내가 찾은 title·decision을 구조화합니다.', 'Action Item 두 개에 evidence ID를 연결합니다.', 'meeting_sample_ko_12min_expected.json과 비교합니다.', '다른 부분을 오류·허용 표현 차이로 나눕니다.'], '내 JSON + 기준 JSON diff'),
      l('실습 5 · PBL canvas 혼자 점검하기', '08 MIN', ['이 서비스를 사용할 사람과 불편을 적습니다.', 'AI가 할 일과 사람이 확인할 일을 나눕니다.', '시간 절감과 품질 기준을 하나씩 적습니다.', '질문 체크리스트를 보며 범위를 한 번 더 줄입니다.'], '한 장짜리 PBL canvas'),
    ],
    pitfalls: [
      f('실패 1 · 데이터가 너무 크다', ['수십 시간 audio', '수백 MB 전체 말뭉치', '전처리만 수업 소진', '정답 만들기 불가'], ['2–3분 audio', '10–30건 text', 'golden 3–5건', '확장 과제는 별도']),
      f('실패 2 · 공개 페이지를 그대로 재배포', ['이용 조건 미확인', '첨부 전체 공유', '출처 누락', '신청 계정 공유'], ['공식 링크 제공', '허용된 소량 샘플', '출처·날짜 기록', 'fixture 대체']),
      f('실패 3 · 정답 없이 prompt를 튜닝', ['좋아 보이는 출력', '기준 매번 변경', '모델 비교 불가', '오류 회귀 모름'], ['golden example', 'rubric', '고정 dataset', 'experiment 비교']),
      f('실패 4 · 담당자·날짜를 추론', ['화자 생략', '상대 날짜', '동명이인', '근거 없는 확신'], ['null 허용', 'evidence 요구', 'NEEDS_REVIEW', '사람 수정 기록']),
    ],
    tracks: [
      { title: '재직자 · 실제 업무를 안전하게 추상화', leftTitle: '가져오지 않을 것', rightTitle: '남길 관계', left: ['실명·고객번호', '계약 금액', '회사 URL', '내부 전략'], right: ['역할 간 의사결정', '업무 단계', '승인 조건', '실패 비용'] },
      { title: '구직자 · 공개 데이터 포트폴리오', leftTitle: '단순 수집', rightTitle: '제품 증거', left: ['사이트 링크만', '전사 결과만', '모델 호출만', '예쁜 화면만'], right: ['dataset card', 'golden JSON', 'failure cases', 'KPI·한계'] },
    ],
    checkpoint: { title: 'Gate 3 · 이 Action Item을 믿어도 될까요?', prompt: '상황: 요약에는 “다음 주에 민지가 배포”라고 적혔지만 원문에는 담당자와 날짜가 명확하지 않습니다.', questions: ['어떤 segment를 evidence로 다시 확인할까?', '담당자·기한을 null로 둘지 사람에게 물을지 결정하자.', '이 사례를 Golden Dataset에 어떤 실패 유형으로 남길까?'] },
  },
  {
    time: '12:00–14:00 · PART 1/2',
    short: 'FREE SETUP',
    title: '무료 환경과 Harness Engineering',
    subtitle: '모든 학습자가 완주하는 필수 경로와 Codex·Claude로 가속하는 강사 경로를 분리합니다.',
    output: 'Python·VS Code·Git·repo · 무료/선택 lane',
    outcome: 'API 종량 비용 없이 필수 실습을 실행하고, 설치 실패 시에도 fixture와 notebook으로 같은 학습목표를 유지합니다.',
    accent: C.green,
    concepts: [
      c('무료의 정의를 먼저 합의한다', '학생은 외부 LLM API 비용 없이 필수 실습을 완주할 수 있어야 한다.', 'Python·Git·VS Code / fixture·local LLM / 선택 서비스 초과 과금 주의'),
      c('필수 경로와 강사 가속 경로를 분리', '학생은 로컬·결정론적 코드, 강사는 Codex·Claude live demo를 사용한다.', '필수: 직접 실행 / 강사: 생성·수정 가속 / 공통: diff·test 검토'),
      c('Python은 실행기, VS Code는 작업 공간', 'extension이 Python 자체를 설치해 주는 것은 아니다.', 'Python interpreter / VS Code editor / Python·Jupyter extension'),
      c('가상환경은 프로젝트의 재현 경계', '전역 환경 대신 프로젝트별 dependency를 격리한다.', 'python -m venv / interpreter 선택 / requirements·pyproject'),
      c('Git과 GitHub는 변경의 증거와 검토 장소', '작은 commit을 branch와 PR로 연결하면 무엇을 바꿨고 누가 확인했는지가 남는다.', 'status·diff / branch·commit / push·draft PR / review·merge'),
      c('Jupyter는 설명과 실행의 다리', '한 셀 한 개념으로 결과를 보고, 모듈 코드는 src에 둔다.', 'Markdown 설명 / Code 실행 / output 증거 / Restart & Run All'),
      c('Secret은 코드·노트북·캡처 밖에 둔다', '실제 값은 환경 변수, 저장소에는 이름만 있는 example을 둔다.', '.env.example / .gitignore / 화면 비식별'),
      c('Harness Engineering은 PR에서 완료된다', 'Spec·허용 파일·test·review rule을 저장소에 두고 Codex 결과를 사람이 merge 전에 확인한다.', 'AGENTS.md / small diff / CI·unit test / Codex review 초안 / human approval', { sources: ['https://learn.chatgpt.com/docs/third-party/github'] }),
      c('Codex와 Claude는 산출물의 저자가 아니라 작업 파트너', '생성 결과를 diff·테스트·출처로 검증할 책임은 강사와 학습자에게 있다.', '요구사항 명료화 / 변경 검토 / 회귀 test / 민감정보 금지'),
      c('Offline lane이 수업 중단을 막는다', '다운로드·로그인·모델이 없어도 fixture로 계약과 제어를 배운다.', 'mock planner / response fixture / transcript 제공 / JSONL trace'),
    ],
    procedures: [
      p('환경 설치 순서', ['PYTHON', '버전 확인'], ['VSCODE', 'extension'], ['GIT', 'identity'], ['REPO', 'clone·open']),
      p('가상환경 준비', ['CREATE', 'python -m venv'], ['ACTIVATE', 'OS별 명령'], ['INSTALL', 'requirements'], ['VERIFY', 'python -m pip']),
      p('VS Code interpreter 선택', ['PALETTE', 'Command Palette'], ['SELECT', 'Python interpreter'], ['KERNEL', 'notebook kernel'], ['CHECK', 'sys.executable']),
      p('GitHub branch와 Draft PR 준비', ['BRANCH', '작은 목적 한 개'], ['DIFF', '변경 범위 확인'], ['PUSH', '교육용 remote'], ['DRAFT PR', '목표·test·위험']),
      p('Codex PR 검토 루프', ['SPEC', '허용 파일·완료조건'], ['CODE+TEST', '변경·unit test'], ['REVIEW', '@codex review·CI'], ['HUMAN', 'diff 확인 후 merge']),
      p('설치 실패 복구 순서', ['CLASSIFY', '권한·PATH·network'], ['LIMIT', '10분 timebox'], ['FALLBACK', 'fixture·Colab'], ['RETURN', 'checkpoint 합류']),
    ],
    screenshots: [
      s('Python 공식 다운로드 · interpreter 준비', 'python-downloads-official.png', 'Python.org Downloads 공식 화면', 'https://www.python.org/downloads/', ['OS와 버전 확인', '설치 후 새 terminal', 'python3 --version', '회사 PC는 권한 확인']),
      s('VS Code Python 튜토리얼 · 세 구성요소', 'vscode-python-tutorial-official.png', 'VS Code Python Tutorial 공식 화면', 'https://code.visualstudio.com/docs/python/python-tutorial', ['VS Code', 'Python extension', 'Python interpreter', 'virtual environment']),
      s('Git 첫 설정 · identity와 기본 확인', 'git-first-setup-official.png', 'Pro Git First-Time Git Setup', 'https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup', ['git --version', 'user.name·user.email', '회사 계정과 교육 계정 구분', '설정 범위 확인']),
      s('GitHub repository quickstart · 교육용 sandbox', 'github-repository-quickstart-official.png', 'GitHub repository quickstart 공식 화면', 'https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories', ['공개/비공개 선택 주의', 'README·.gitignore', '교육용 repo', '비공개 회사 코드 금지']),
    ],
    examples: [
      e('환경 확인 네 줄', 'python3 --version\ngit --version\ncode --version\npython3 -m pip --version', ['명령과 기대 결과', 'PATH 문제 확인', '새 terminal 재시작', '캡처에 개인정보 최소화']),
      e('가상환경 명령 · macOS/Linux', 'python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements-day1.txt\npython -c \"import sys; print(sys.executable)\"', ['.venv 생성', '활성화', 'dependency 설치', 'interpreter 경로 확인']),
      e('가상환경 명령 · Windows PowerShell', 'py -3 -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements-day1.txt\npython -c \"import sys; print(sys.executable)\"', ['ExecutionPolicy 오류 분리', 'py launcher', '같은 requirements', '경로 화면 확인']),
      e('작은 branch에서 Draft PR까지', 'git switch -c test/reject-python-file\npython3 -m pytest -q\ngit diff --check\ngit add tests/test_day1_agent.py\ngit commit -m \"test: reject python file reads\"\ngit push -u origin HEAD\ngh pr create --draft --fill', ['교육용 repo만', '관련 파일만 stage', 'test·diff 증거', 'gh가 없으면 GitHub 화면']),
      e('AGENTS.md · Codex가 볼 Review 기준', '## Code Review Rules\n\n### Safety boundary\n- workspace 밖 파일 접근을 허용하지 않는다.\n- 외부 쓰기는 사람 승인 없이 실행하지 않는다.\n\n### Tests\n- 동작 변경에는 정상·실패 unit test를 함께 둔다.', ['저장소 특화 기준', '결과 중심 규칙', '기계 검사는 CI', '최종 판단은 사람'], { sources: ['https://learn.chatgpt.com/docs/third-party/github'] }),
      e('Agent에게 주는 작업 계약', 'Objective: add one validation test\nScope: tests/test_day1_agent.py\nDo not: change src behavior\nVerify: python3 -m pytest -q\nDeliver: diff + result', ['한 번에 한 목적', '파일 범위', '금지 조건', '검증 명령']),
    ],
    labs: [
      l('실습 1 · 버전 확인 캡처', '08 MIN', ['새 terminal을 연다.', 'Python·Git 버전을 확인한다.', 'VS Code가 같은 폴더를 열었는지 확인한다.', '실패 항목을 표에 표시한다.'], '버전 3개 + 상태표'),
      l('실습 2 · 가상환경과 interpreter', '10 MIN', ['.venv를 만든다.', '가상환경을 활성화한다.', 'VS Code interpreter를 선택한다.', 'sys.executable을 출력한다.'], '가상환경 경로 출력'),
      l('실습 3 · notebook 열기', '08 MIN', ['materials/day1 notebook을 연다.', '선택한 kernel을 확인한다.', '첫 Markdown·Code 셀을 실행한다.', 'output이 남는 위치를 확인한다.'], '첫 셀 성공 화면'),
      l('실습 4 · Branch→Codex→Test→PR 준비', '12 MIN', ['교육용 branch를 만들고 변경 목표를 네 줄로 적습니다.', 'Codex에는 tests/test_day1_agent.py 한 파일만 허용합니다.', '생성된 diff를 직접 읽고 pytest를 실행합니다.', 'GitHub 연결이 되면 Draft PR, 아니면 local diff를 저장합니다.'], 'branch + test + Draft PR 또는 local diff', { note: '강사는 연결된 sandbox repo에서 push와 Draft PR을 시연한다. 수강생은 계정·권한·gh 설치가 준비된 경우에만 PR까지 따라 한다. 자동 리뷰는 @codex review로 요청할 수 있지만 결과는 참고 의견이며, CI와 사람의 diff 확인 뒤에만 merge한다.', example: 'Objective: .py 읽기 차단 test 추가 / Scope: tests/test_day1_agent.py / Do not: src 변경 / Verify: python3 -m pytest -q' }),
      l('실습 5 · Harness spec 쓰기', '08 MIN', ['작은 변경 목표를 적는다.', '허용 파일을 한 개 정한다.', '금지 행동을 한 개 적는다.', '검증 명령을 한 줄로 쓴다.'], '4줄 작업 계약'),
    ],
    pitfalls: [
      f('실패 1 · 설치를 끝없이 붙잡는다', ['한 명의 PATH에 30분', '전체 대기', '학습 목표 상실', '다운로드 경쟁'], ['10분 timebox', 'checkpoint zip', 'fixture lane', '점심 후 재합류']),
      f('실패 2 · 전역 Python에 모두 설치', ['버전 충돌', '권한 오류', '재현 불가', '다른 프로젝트 영향'], ['.venv', 'python -m pip', 'requirements 고정', 'interpreter 확인']),
      f('실패 3 · Agent에게 저장소 전체 수정 허용', ['범위 모호', '불필요 파일 변경', 'test 삭제', 'secret 접근'], ['허용 파일', '금지 조건', 'diff 우선', 'test 결과 요구']),
      f('실패 4 · Git stage를 한 번에', ['git add .', '개인 파일 포함', '대형 모델 포함', '.env 포함'], ['status 확인', '파일별 add', 'cached diff', '.gitignore']),
    ],
    tracks: [
      { title: '재직자 · 회사 PC 제약 lane', leftTitle: '제약', rightTitle: '대체', left: ['관리자 권한 없음', '외부 다운로드 차단', 'GitHub 접속 제한', 'GPU 없음'], right: ['portable/승인 절차', '사전 제공 fixture', '로컬 Git', '작은 CPU 모델·텍스트'] },
      { title: '구직자 · 포트폴리오 환경 증거', leftTitle: '보여줄 것', rightTitle: '말할 것', left: ['README 설치', 'requirements', 'Run All', 'pytest·Git log'], right: ['재현성 선택', 'fallback 설계', 'secret 관리', '협업 방식'] },
    ],
    checkpoint: { title: 'Gate 4 · 다른 PC에서도 다시 실행할 수 있을까요?', prompt: '상황: 저장소는 받았지만 .venv가 없고 Notebook이 전역 Python을 보고 있습니다.', questions: ['첫 세 명령으로 runtime과 경로를 어떻게 확인할까?', '10분 안에 설치가 안 되면 어떤 fixture로 계속할까?', '정상 상태를 어떤 commit과 캡처로 남길까?'] },
  },
  {
    time: '12:00–14:00 · PART 2/2',
    short: 'SAFE LOOP',
    title: 'Safe Tool Loop 구현',
    subtitle: '점심 전 한 시간에 결정론적 planner·validator·executor·test·Git checkpoint를 완성합니다.',
    output: '실행 가능한 src · 9 tests · 첫 commit',
    outcome: 'Framework와 외부 모델 없이도 Agent 제어 루프를 실행하고, 정상 1건과 실패 4종을 스스로 재현합니다.',
    accent: C.amber,
    concepts: [
      c('처음부터 LLM을 넣지 않는 이유', '결정론적 planner로 제어 계약을 먼저 테스트하면 모델 변동과 코드 오류를 분리할 수 있다.', '규칙 기반 plan / 고정 fixture / 같은 executor contract'),
      c('Planner는 “무엇을 할까”만 결정', '도구 이름과 인자를 제안하고 실행 권한은 갖지 않는다.', 'input parse / planned_call / no side effect'),
      c('Validator는 안전 경계를 고정', '허용 도구·필수 인자·타입·추가 필드·경로를 검사한다.', 'schema / policy / path guard / error code'),
      c('Executor는 등록 함수만 호출', '동적 eval이나 임의 import 없이 registry에서 함수 객체를 찾는다.', 'registry lookup / kwargs / exception boundary'),
      c('ToolResult는 성공과 실패의 공통 언어', 'downstream graph가 traceback 구조를 몰라도 다음 행동을 고를 수 있다.', 'ok / data / error_code / message / cached'),
      c('read_public_text는 의도적으로 좁다', 'workspace 안의 공개 txt·md만 읽는 도구로 최소 권한을 체험한다.', 'root boundary / suffix allowlist / UTF-8'),
      c('count_action_markers는 LLM 전 fixture', '한국어 행동 표현을 규칙으로 찾아 구조화 파이프라인을 먼저 연결한다.', '까지·작성·검토 / evidence line / deterministic'),
      c('call_id는 같은 호출을 알아본다', '정렬된 tool·arguments hash로 중복 요청을 cache한다.', 'canonical JSON / sha256 / cached=True'),
      c('Notebook은 모듈을 사용하는 Tutorial', '핵심 구현은 src, 설명·실행·질문은 ipynb에 둔다.', 'import module / display result / break case / reflection'),
      c('Commit은 점심 전 복구 지점', '오후 모델 연결이 실패해도 안전 loop checkpoint로 돌아올 수 있다.', 'tests pass / staged diff / day1-safe-loop tag'),
    ],
    procedures: [
      p('코드 읽기 순서', ['DATA', 'dataclass·schema'], ['POLICY', 'validate·guard'], ['EXECUTE', 'registry·result'], ['DEMO', '__main__']),
      p('Run All 순서', ['KERNEL', 'interpreter'], ['IMPORT', 'module'], ['NORMAL', 'success'], ['FAIL', '4 error cases']),
      p('실패 주입 순서', ['UNKNOWN', '도구 없음'], ['MISSING', '인자 누락'], ['TRAVERSAL', '경로 이탈'], ['DUPLICATE', 'cache 확인']),
      p('pytest 빨강→초록', ['RUN', '현재 실패'], ['READ', '첫 오류'], ['FIX', '최소 변경'], ['RERUN', '전체 10개']),
      p('Git checkpoint 만들기', ['STATUS', '변경 분리'], ['DIFF', '의도 확인'], ['STAGE', 'src·tests만'], ['COMMIT', '메시지·log']),
      p('점심 전 Gate', ['NOTEBOOK', 'Run All'], ['PYTEST', '10 passed'], ['DIFF', '설명 가능'], ['RECOVERY', '미완료 lane']),
    ],
    screenshots: [
      s('Jupyter 설치 · notebook 실행기의 공식 경로', 'jupyter-install-official.png', 'Jupyter Install 공식 화면', 'https://jupyter.org/install', ['JupyterLab·Notebook 구분', 'VS Code extension과 kernel', '프로젝트 가상환경 사용', 'Run All이 완료 증거']),
      s('VS Code Python · editor와 interpreter 연결', 'vscode-python-official.png', 'VS Code Python 공식 문서 화면', 'https://code.visualstudio.com/docs/languages/python', ['Python extension', 'interpreter 표시', 'Run Python File', 'testing·debugging 연결']),
      s('Codex CLI · 작은 spec으로 수정 가속', 'codex-cli-official.png', 'OpenAI Codex CLI 공식 화면', 'https://developers.openai.com/codex/cli/', ['허용 파일 한정', '테스트 명령 명시', '생성 결과 diff', '강사 demo 후 직접 재현']),
      s('Claude Code · 동일 repo에서 검토 루프', 'claude-code-official.png', 'Claude Code 공식 터미널 가이드 화면', 'https://docs.anthropic.com/en/docs/claude-code/terminal-guide', ['작업 폴더 확인', '변경 전 계획', '변경 후 test', '두 Agent 결과도 사람이 비교']),
    ],
    examples: [
      e('규칙 기반 planner', 'def rule_based_planner(message):\n    match = re.search(r\"([\\w./-]+\\.(txt|md))\", message)\n    if match:\n        return {\"name\": \"read_public_text\",\n                \"arguments\": {\"path\": match.group(1)}}\n    return {\"name\": \"unknown_tool\", \"arguments\": {}}', ['결정론적 plan', '파일명만 추출', 'unknown도 정상 fixture', 'Day2 model로 교체']),
      e('SafeToolExecutor의 경계', 'def execute(self, name, args):\n    try:\n        validate(name, args)\n        fn = TOOL_REGISTRY[name]\n        data = fn(**args)\n        return ToolResult(True, name, data=data)\n    except ToolValidationError as exc:\n        return ToolResult(False, name,\n          error_code=\"VALIDATION_ERROR\")', ['검증 먼저', 'registry 함수', '예외 정규화', '반환 계약']),
      e('파일 확장자 allowlist', 'if candidate.suffix.lower() not in {\".txt\", \".md\"}:\n    raise ToolValidationError(\n      \"Day 1에서는 .txt와 .md만 허용합니다.\"\n    )', ['목적에 필요한 형식만', 'binary 제외', '정책 메시지', 'POLICY_BLOCKED로 매핑']),
      e('중복 호출 cache', 'call_id = make_call_id(name, args)\nif call_id in self._cache:\n    prev = self._cache[call_id]\n    return replace(prev, cached=True)\nresult = call_tool()\nself._cache[call_id] = result', ['실행 전 조회', '성공·실패 정책 결정', 'cached 표시', '외부 쓰기에는 영속 저장']),
      e('Agent event 한 건', 'event = {\n  \"input\": user_message,\n  \"planned_call\": call,\n  \"tool_result\": result.to_dict(),\n  \"needs_human_review\": not result.ok\n}', ['입력', '결정', '결과', '사람 검토 여부']),
      e('pytest 완료 명령', 'python3 -m pytest -q\n# ..........                   [100%]\n# 10 passed in 0.05s\n\ngit diff --check\ngit status --short', ['10개 테스트', 'whitespace 검사', '변경 파일', '점심 전 checkpoint']),
    ],
    labs: [
      l('실습 1 · Notebook Run All', '12 MIN', ['올바른 kernel을 선택한다.', 'Restart Kernel을 실행한다.', 'Run All을 실행한다.', '첫 실패 셀에서 멈추고 원인을 기록한다.'], '모든 셀 성공'),
      l('실습 2 · 정상 도구 호출', '08 MIN', ['sample txt 경로를 입력한다.', 'planned_call을 확인한다.', 'ToolResult ok와 data를 확인한다.', '원문 글자 수와 경로를 검증한다.'], '정상 event 1건'),
      l('실습 3 · 실패 4종 재현', '10 MIN', ['unknown tool을 실행한다.', '필수 인자를 지운다.', '../ 경로를 넣는다.', '같은 호출을 두 번 실행한다.'], 'error_code 3개 + cached 1개'),
      l('실습 4 · pytest 10개 확인', '08 MIN', ['terminal을 연다.', 'python3 -m pytest -q를 실행한다.', '실패 시 첫 오류만 읽는다.', '10 passed 화면을 저장한다.'], '10 passed'),
      l('실습 5 · 점심 전 Git checkpoint', '10 MIN', ['git status를 확인한다.', 'src·tests diff를 읽는다.', '관련 파일만 stage한다.', 'commit 후 log 한 줄을 확인한다.'], 'commit 1개 + hash'),
    ],
    pitfalls: [
      f('실패 1 · Notebook과 module이 다른 Python', ['import error', '설치했는데 못 찾음', 'terminal은 성공', 'kernel은 실패'], ['sys.executable 비교', 'interpreter 재선택', 'kernel restart', '같은 .venv']),
      f('실패 2 · 첫 실패 뒤 계속 실행', ['연쇄 오류', '원인 혼동', 'output 오염', '시간 낭비'], ['첫 traceback', '가장 위 원인', '최소 셀 재실행', 'Restart & Run All']),
      f('실패 3 · 테스트를 통과시키려고 정책 완화', ['allowlist 제거', 'assert 삭제', 'broad except', 'expected 변경'], ['요구사항 재확인', '최소 수정', '새 regression test', '정책 유지']),
      f('실패 4 · 점심 전에 미완료를 숨김', ['오후 모델부터 진행', '기초 오류 누적', '강사 답변만 기다림', '복구 지점 없음'], ['현재 상태 기록', 'fixture로 전환', '15시 첫 10분 복구', 'checkpoint zip']),
    ],
    tracks: [
      { title: '재직자 · Safe loop를 현업 tool에 매핑', leftTitle: '교육 도구', rightTitle: '현업 예시', left: ['txt 읽기', 'marker 세기', '결과 JSON', '로컬 cache'], right: ['FAQ 조회', '티켓 분류', '검토 draft', 'request dedupe'] },
      { title: '구직자 · commit을 설명 가능한 증거로', leftTitle: '나쁜 history', rightTitle: '좋은 history', left: ['final', 'fix', '수십 파일 한 번', 'test 후첨'], right: ['feat: schema', 'test: traversal', 'refactor: result', '각 commit green'] },
    ],
    checkpoint: { title: 'Gate 5 · 14:00 점심 전 실행 증거', prompt: '지금부터 점심시간입니다. 14:55까지 돌아오면 15:00에 Local LLM 연결부터 바로 시작합니다.', questions: ['Notebook Run All 결과가 남았는가?', 'pytest 10개 통과 화면이 남았는가?', '내 commit diff에서 바뀐 경계를 한 문장으로 말할 수 있는가?'], note: '14:00에 정확히 점심을 시작하고 14:55 복귀를 공지한다. 점심 변경 사유와 사과는 오프닝 운영 장표에서 이미 전달했으므로 여기서는 반복하지 않는다.' },
  },
  {
    time: '15:00–17:30 · PART 1/3',
    short: 'LOCAL LLM',
    title: '로컬 LLM Adapter',
    subtitle: 'Ollama·LM Studio·Jan을 선택지로 두고 provider가 달라도 같은 계약을 유지합니다.',
    output: '공통 provider result · structured output · fallback',
    outcome: '로컬 모델 성공 여부와 관계없이 공통 adapter를 실행하고, 연결 실패를 예상된 결과로 처리합니다.',
    accent: C.cyan,
    concepts: [
      c('필수 목표는 “모델 설치 성공”이 아니다', 'provider가 없어도 mock·fixture로 adapter 계약과 예외 처리를 완성한다.', 'mandatory: contract / optional: local model / no score penalty'),
      c('Ollama는 CLI와 localhost API 경로', '모델 pull·serve·generate를 간단한 로컬 흐름으로 제공한다.', 'ollama pull / localhost:11434 / API key 없음'),
      c('LM Studio는 GUI와 OpenAI-compatible server', '모델 관리와 local server를 화면으로 다루기 쉬운 대안이다.', 'download model / start server / base URL'),
      c('Jan은 desktop local API 대안', 'OpenAI-compatible endpoint를 통해 기존 client를 재사용할 수 있다.', 'local server / model selection / offline-oriented'),
      c('Provider adapter가 차이를 감춘다', 'URL·인증·payload·response를 provider 내부로 모으고 앱에는 공통 result를 준다.', 'generate(prompt) / success data / normalized error'),
      c('OpenAI-compatible은 완전 동일을 뜻하지 않는다', 'model name·지원 필드·tool calling·structured output 차이를 확인한다.', 'endpoint / payload subset / model capability'),
      c('작은 모델은 출력 계약을 더 엄격히', 'JSON parse·schema validate·repair·human review를 별도 단계로 둔다.', 'extract JSON / validate / bounded repair / stop'),
      c('Temperature는 품질 버튼이 아니다', '업무 추출은 낮은 변동성과 고정 schema가 먼저다.', 'deterministic-ish / prompt clarity / sample regression'),
      c('Context 제한은 입력 설계 문제', '긴 회의는 segment·chunk·evidence를 유지하며 나눈다.', 'chunk overlap / summary merge / evidence IDs'),
      c('Fallback은 자동·수동 경계를 공개한다', '모델 실패 시 fixture로 진행하고 실제 모델 결과와 비교 기록을 남긴다.', 'OLLAMA_UNAVAILABLE / fallback_used / same downstream'),
    ],
    procedures: [
      p('로컬 provider 선택', ['CHECK', 'RAM·권한'], ['CHOOSE', 'Ollama·GUI'], ['VERIFY', 'health·model'], ['FALLBACK', 'fixture']),
      p('Ollama 최소 실행', ['INSTALL', '공식 배포'], ['PULL', '작은 모델'], ['LIST', 'model 확인'], ['GENERATE', 'API 호출']),
      p('Adapter 네 단계', ['INPUT', '공통 prompt'], ['MAP', 'provider payload'], ['CALL', 'timeout'], ['NORMALIZE', '공통 result']),
      p('Structured output 처리', ['RAW', '원문 보존'], ['PARSE', 'JSON 추출'], ['VALIDATE', 'schema'], ['REVIEW', 'repair·human']),
      p('모델 오류 분류', ['CONNECT', '서버 없음'], ['MODEL', 'tag 없음'], ['FORMAT', 'JSON 깨짐'], ['QUALITY', '근거 누락']),
      p('성공/실패 비교 실험', ['FIXTURE', '기준 결과'], ['LOCAL', '실제 생성'], ['DIFF', '필드·근거'], ['LOG', 'model·latency']),
    ],
    screenshots: [
      s('Ollama 다운로드 · OS별 설치', 'ollama-download-official.png', 'Ollama Download 공식 화면', 'https://ollama.com/download', ['공식 설치 파일', 'OS 지원 확인', '회사 PC 권한', '수업 전 미리 다운로드']),
      s('Qwen3 model library · tag 확인', 'ollama-qwen3-official.png', 'Ollama Qwen3 model library 화면', 'https://ollama.com/library/qwen3', ['모델 tag를 그대로', '크기·RAM 고려', '한 모델만', '강의 직전 tag 재확인']),
      s('LM Studio · Local LLM API server', 'lmstudio-server-official.png', 'LM Studio local server 공식 문서', 'https://lmstudio.ai/docs/developer/core/server', ['GUI 모델 관리', 'server start', 'localhost endpoint', 'OpenAI-compatible 확인']),
      s('Jan · Local API Server', 'jan-api-server-official.png', 'Jan Local API Server 공식 문서', 'https://www.jan.ai/docs/desktop/api-server', ['desktop 대안', 'server 상태', 'model selection', '공통 adapter 연결']),
    ],
    examples: [
      e('Ollama generate payload', 'payload = {\n  \"model\": \"qwen3:4b\",\n  \"prompt\": prompt,\n  \"stream\": False\n}\nPOST http://localhost:11434/api/generate', ['localhost', 'model tag', 'stream 단순화', 'timeout 필수'], { sources: ['https://docs.ollama.com/api/generate'] }),
      e('연결 실패도 result', 'try:\n    data = post_json(url, payload, timeout=60)\n    return {\"ok\": True, \"data\": data}\nexcept URLError as exc:\n    return {\"ok\": False,\n            \"error_code\": \"OLLAMA_UNAVAILABLE\",\n            \"detail\": str(exc)}', ['exception 밖으로 누출 금지', '안정된 코드', '상세 원인', 'fallback 선택']),
      e('공통 Provider protocol', 'class Provider(Protocol):\n    def generate(self, prompt: str) -> ModelResult: ...\n\nproviders = {\n  \"fixture\": FixtureProvider(),\n  \"ollama\": OllamaProvider()\n}', ['앱과 provider 분리', '같은 입력', '같은 result', 'test double']),
      e('JSON parse와 schema validate', 'raw = provider.generate(prompt)\nparsed = extract_json(raw.text)\nresult = MeetingResult.model_validate(parsed)\nif missing_evidence(result):\n    return NEEDS_REVIEW', ['raw 보존', 'parse 단계', 'typed validate', '근거 정책']),
      e('bounded repair · 한 번만', 'for attempt in range(2):\n    try:\n        return validate(parse(text))\n    except SchemaError as err:\n        if attempt == 1: break\n        text = provider.generate(repair_prompt(err, text))\nreturn NEEDS_REVIEW', ['무한 repair 금지', '오류 정보 제공', '최대 횟수', '사람 검토']),
      e('Provider 비교 로그', 'run = {\n  \"provider\": provider_name,\n  \"model\": model_name,\n  \"latency_ms\": elapsed,\n  \"schema_pass\": passed,\n  \"fallback_used\": fallback,\n  \"error_code\": error_code\n}', ['provider·model', 'latency', 'schema pass', 'fallback·error']),
    ],
    labs: [
      l('실습 1 · Ollama health 확인', '08 MIN', ['ollama list를 실행한다.', '서버 연결 여부를 확인한다.', '모델이 없으면 설치를 강행하지 않는다.', 'fixture lane을 선택해 기록한다.'], 'provider 상태 1줄'),
      l('실습 2 · 선택 provider 호출', '12 MIN', ['prompt를 짧게 입력한다.', 'timeout을 지정한다.', '성공이면 response 일부를 확인한다.', '실패면 error_code를 확인한다.'], '성공/실패 result 1건'),
      l('실습 3 · 공통 contract 비교', '08 MIN', ['fixture result 필드를 적는다.', 'local result 필드를 적는다.', '공통 필드와 provider 전용 필드를 구분한다.', 'downstream이 볼 필드를 정한다.'], 'provider 비교표'),
      l('실습 4 · 깨진 JSON 복구', '10 MIN', ['마지막 괄호가 없는 fixture를 넣는다.', 'parse 오류를 확인한다.', 'repair를 한 번 실행한다.', '두 번째 실패 시 NEEDS_REVIEW로 멈춘다.'], 'repair 1회 + stop'),
      l('실습 5 · 모델을 바꾸면 무엇이 달라질까?', '08 MIN', ['Ollama와 LM Studio 중 하나를 고릅니다.', '모델을 바꾸면 달라지는 설정을 적습니다.', '바뀌지 않는 schema·validator를 적습니다.', 'adapter가 필요한 이유를 한 문장으로 정리합니다.'], '변경/불변 표 + 한 문장'),
    ],
    pitfalls: [
      f('실패 1 · 큰 모델 다운로드를 기다림', ['수업 전체 대기', '디스크 부족', 'RAM swap', '학습 목표 상실'], ['작은 모델 하나', '사전 설치', 'fixture 즉시 전환', '모델 비교는 심화']),
      f('실패 2 · 연결 실패를 traceback으로', ['노트북 중단', '학생 원인 파악 어려움', 'graph state 유실', 'fallback 불가'], ['error_code', '사용자 메시지', 'trace detail', 'same result contract']),
      f('실패 3 · JSON처럼 보이면 통과', ['필드 누락', '타입 오류', '근거 없음', '날짜 형식 혼합'], ['typed schema', 'evidence policy', 'date validator', 'human review']),
      f('실패 4 · provider별 코드가 퍼짐', ['if ollama everywhere', '테스트 중복', 'URL 하드코딩', '교체 비용'], ['adapter 한 곳', 'config', 'provider protocol', 'contract tests']),
    ],
    tracks: [
      { title: '재직자 · 로컬 LLM 도입 질문', leftTitle: '기술 질문', rightTitle: '운영 질문', left: ['RAM·속도', 'model capability', 'API 호환', '배포 형태'], right: ['데이터 경계', '업데이트 책임', '관측·감사', 'fallback·SLA'] },
      { title: '구직자 · 모델 비교 실험', leftTitle: '단순 비교', rightTitle: '좋은 실험', left: ['느낌', '한 prompt', '응답 복붙', '모델명만'], right: ['고정 dataset', 'schema pass', 'evidence rate', 'latency·실패율'] },
    ],
    checkpoint: { title: 'Gate 6 · Local LLM이 꺼져도 계속하기', prompt: '상황: Ollama 연결이 거부되고, 교실 네트워크에서는 새 모델도 받을 수 없습니다.', questions: ['같은 Provider contract로 어떤 fallback을 연결할까?', '연결 실패를 traceback 대신 어떤 result로 돌려줄까?', 'fixture로도 끝까지 검증할 출력 계약은 무엇일까?'] },
  },
  {
    time: '15:00–17:30 · PART 2/3',
    short: 'LANGGRAPH & HITL',
    title: 'State·Retry·Human Approval',
    subtitle: '여러 단계가 실패·중단·재개되는 흐름을 LangGraph의 state와 interrupt 관점으로 설계합니다.',
    output: 'State schema · branch · approve/edit/reject event',
    outcome: '재시도와 중복 방지를 구분하고, 승인 전 side effect가 안전하게 재실행되도록 Human-in-the-loop 경계를 그립니다.',
    accent: C.blue,
    concepts: [
      c('State는 다음 행동의 근거', '대화 전체가 아니라 node가 판단에 필요한 최소 구조를 저장한다.', 'request_id·step / draft·errors / retry·approval·status'),
      c('Node는 한 가지 책임의 함수', '입력 state를 읽고 부분 update를 반환하도록 작게 나눈다.', 'transcribe / summarize / validate / review / publish'),
      c('Edge는 다음 node를 정하는 정책', '성공·오류·위험·승인 결과에 따라 명시적으로 분기한다.', 'conditional route / END / retry loop'),
      c('Checkpointer가 중단과 재개를 가능하게', '각 step의 state snapshot을 thread 단위로 저장한다.', 'checkpoint / thread_id / state history'),
      c('Interrupt는 “잠깐 멈춤”이 아니라 업무 상태다', '검토할 정보와 현재 state를 저장하고, 같은 thread에서 사람 결정 뒤 다시 시작한다.', '초안·근거를 먼저 보여주기 / approve·edit·reject 기록 / 같은 thread로 재개', {
        kicker: 'GLOBAL REFERENCE · IBM',
        visual: { image: 'ibm-langgraph-hitl.png', contentType: 'image/png', caption: 'IBM Human-in-the-loop LangGraph workflow' },
        visualBullets: ['어디에서 멈추는가', '사람이 무엇을 보는가', '같은 상태로 어떻게 재개하는가'],
        sources: ['https://www.ibm.com/think/tutorials/human-in-the-loop-ai-agent-langraph-watsonx-ai'],
      }),
      c('Approve·Edit·Reject는 다른 event', '승인은 원안 진행, 수정은 새 payload, 거절은 이유와 종료·재계획을 남긴다.', 'decision / reviewer / reason / edited payload'),
      c('Retry는 일시 오류에만', '오류 class·max attempts·backoff·stop을 state에 남긴다.', 'transient / attempts / next delay / exhausted'),
      c('Idempotency는 재실행의 안전 조건', 'interrupt 이전 node가 다시 실행될 수 있으므로 side effect를 중복 방지한다.', 'request key / outbox / cached success'),
      c('사람 승인 UI에는 근거가 함께', '원문 evidence·초안·외부 변경 대상·위험 flag 없이 승인 버튼만 두지 않는다.', 'before/after / evidence / target / risk'),
      c('LangChain·LangGraph·LangSmith 역할 분리', '조합·제어·관측을 한 라이브러리로 뭉치지 않는다.', 'LangChain: model·tool / LangGraph: state·flow / LangSmith: trace·eval'),
    ],
    procedures: [
      p('Graph 설계 순서', ['STATE', '필드·status'], ['NODES', '한 책임'], ['EDGES', '분기·END'], ['CHECK', '중단·재개']),
      p('오류 routing 순서', ['CLASSIFY', '오류 class'], ['COUNT', 'attempt'], ['ROUTE', 'retry·review'], ['STOP', 'terminal status']),
      p('Human review node', ['SHOW', 'draft·evidence'], ['DECIDE', 'A/E/R'], ['RECORD', 'review event'], ['RESUME', 'same thread']),
      p('Interrupt payload 설계', ['SUMMARY', '무엇을 하려나'], ['TARGET', '어디에 쓰나'], ['RISK', '왜 검토하나'], ['OPTIONS', '승인·수정·거절']),
      p('Idempotent publish', ['KEY', 'request_id'], ['LOOKUP', '기존 성공'], ['WRITE', '한 번 수행'], ['RECORD', 'external id']),
      p('LangSmith 연결 지점', ['RUN', 'graph 전체'], ['CHILD', 'node·LLM·tool'], ['META', 'thread·dataset'], ['FEEDBACK', 'human decision']),
    ],
    screenshots: [
      s('LangChain overview · 조합 계층', 'langchain-overview-official.png', 'LangChain overview 공식 문서', 'https://docs.langchain.com/oss/python/langchain/overview', ['model·messages·tools', 'structured output', '빠른 조합', '제어 흐름은 LangGraph']),
      s('LangGraph overview · stateful orchestration', 'langgraph-overview-official.png', 'LangGraph overview 공식 문서', 'https://docs.langchain.com/oss/python/langgraph/overview', ['state·nodes·edges', 'durable execution', 'human-in-the-loop', '장기 실행 workflow']),
      s('LangGraph interrupts · 사람 입력에서 중단', 'langgraph-interrupts-official.png', 'LangGraph Interrupts 공식 문서', 'https://docs.langchain.com/oss/python/langgraph/interrupts', ['interrupt payload', 'Command resume', 'JSON-serializable', 'side effect idempotent']),
      s('LangGraph persistence · checkpoint와 thread', 'langgraph-persistence-official.png', 'LangGraph Persistence 공식 문서', 'https://docs.langchain.com/oss/python/langgraph/persistence', ['checkpointer', 'thread_id', 'state history', 'fault tolerance']),
    ],
    examples: [
      e('State schema', 'class State(TypedDict):\n    request_id: str\n    transcript: list[dict]\n    draft: dict | None\n    errors: list[dict]\n    retry_count: int\n    approval: dict | None\n    status: str', ['다음 node에 필요한 필드', 'raw data 유지', '오류 누적', 'terminal status']),
      e('오류 route 함수', 'def route_after_validate(state):\n    if state[\"status\"] == \"READY\":\n        return \"human_review\"\n    if state[\"status\"] == \"TRANSIENT_ERROR\" and state[\"retry_count\"] < 2:\n        return \"retry\"\n    return \"failed\"', ['status 기반', 'bounded retry', '정책 오류 제외', '명시적 failed']),
      e('Interrupt로 검토 요청', 'review = interrupt({\n  \"draft\": state[\"draft\"],\n  \"evidence\": state[\"evidence\"],\n  \"target\": state[\"publish_target\"],\n  \"options\": [\"approve\", \"edit\", \"reject\"]\n})', ['검토 정보 한 화면', '직렬화 가능한 값', '버튼만 전달 금지', '결정은 event로']),
      e('Command로 같은 thread 재개', 'config = {\"configurable\": {\"thread_id\": request_id}}\nfirst = graph.invoke(input_state, config)\n# interrupt에서 멈춤\nsecond = graph.invoke(Command(resume={\"decision\": \"approve\"}), config)', ['thread_id 유지', 'checkpoint load', 'resume value', 'new thread와 구분']),
      e('승인 event', 'approval = {\n  \"decision\": \"edit\",\n  \"reviewer\": \"role-reviewer\",\n  \"reason\": \"담당자 근거 부족\",\n  \"edited_payload\": corrected,\n  \"at\": iso_time\n}', ['누가', '무슨 결정', '이유', '수정 payload·시각']),
      e('중복 publish 방지', 'if outbox.exists(request_id):\n    return outbox.result(request_id)\nexternal_id = publish(approved_payload)\noutbox.save(request_id, external_id)\nreturn external_id', ['먼저 조회', '승인 payload만', '외부 ID 저장', 'resume에도 한 번']),
    ],
    labs: [
      l('실습 1 · State 필드 설계', '08 MIN', ['입력·중간·오류·승인 필드를 나눈다.', '각 node가 읽을 필드를 표시한다.', 'terminal status를 세 개 정한다.', '불필요한 chat history를 제거한다.'], 'State schema 1개'),
      l('실습 2 · Node와 edge 카드', '10 MIN', ['transcribe부터 publish까지 카드를 놓는다.', '각 node 한 책임을 쓴다.', '성공 edge를 연결한다.', '오류·review edge를 다른 색으로 연결한다.'], 'graph sketch'),
      l('실습 3 · Retry 정책표', '08 MIN', ['오류 네 종류를 적는다.', '각 오류의 retry 여부를 정한다.', 'max attempts와 backoff를 적는다.', 'exhausted 후 상태를 정한다.'], 'retry matrix'),
      l('실습 4 · Reviewer 역할극', '12 MIN', ['A는 Agent, B는 Reviewer가 된다.', '초안과 evidence를 비교한다.', 'approve/edit/reject와 이유를 남긴다.', '역할을 바꾸고 낮은 confidence 사례를 반복한다.'], 'review event 2건'),
      l('실습 5 · Idempotency 질문', '08 MIN', ['interrupt 이전 side effect를 찾는다.', '재실행 시 중복되는 행동을 찾는다.', 'request_id 저장 위치를 정한다.', 'side effect를 interrupt 뒤로 옮길지 결정한다.'], '중복 방지 설계 1개'),
    ],
    pitfalls: [
      f('실패 1 · State에 모든 것을 저장', ['거대한 message history', 'binary audio 포함', '개인정보 장기 보존', 'node coupling'], ['최소 structured state', '원본은 보호 저장소', 'reference ID', 'node별 계약']),
      f('실패 2 · interrupt를 try/except로 감쌈', ['중단 신호를 오류 처리', '재개 불가', 'state 혼란', '반복 호출'], ['공식 interrupt 규칙', '직렬화 payload', '같은 thread', '명시적 resume'], { sources: ['https://docs.langchain.com/oss/python/langgraph/interrupts'] }),
      f('실패 3 · 승인 전에 외부 쓰기', ['재실행 중복', '오류 확산', '사람이 취소 불가', '감사 추적 부재'], ['draft·preview', 'interrupt', 'approved payload', 'idempotent publish']),
      f('실패 4 · thread_id를 매번 새로', ['checkpoint 못 찾음', '처음부터 재실행', '승인 유실', '중복 side effect'], ['stable request_id', 'same config', 'state history 확인', '새 요청만 new thread']),
    ],
    tracks: [
      { title: '재직자 · Human Approval 운영표', leftTitle: '승인 기준', rightTitle: '운영 증거', left: ['개인정보 flag', '낮은 confidence', '외부 발행', '금액·계약 영향'], right: ['reviewer role', 'SLA', 'decision reason', 'audit log'] },
      { title: '구직자 · Graph 설명 순서', leftTitle: '보여줄 그림', rightTitle: '말할 trade-off', left: ['state schema', 'nodes·edges', 'interrupt', 'retry branch'], right: ['왜 framework?', '어디서 중단?', '어떻게 재개?', '중복은 어떻게?'] },
    ],
    checkpoint: { title: 'Gate 7 · 승인 뒤 같은 요청이 다시 왔습니다', prompt: '상황: reviewer가 승인한 직후 네트워크가 끊겼고, 같은 request_id로 publish가 다시 호출됐습니다.', questions: ['어떤 State와 checkpoint에서 재개할까?', '승인 event에서 어떤 근거와 결정을 읽을까?', '새로 발행할까, 저장된 성공 결과를 돌려줄까?'] },
  },
  {
    time: '15:00–17:30 · PART 3/3',
    short: 'STT & LANGSMITH',
    title: 'STT부터 LangSmith까지 연결',
    subtitle: 'Managed 회의 기능과 local STT 원리를 구분하고, trace·dataset·evaluation으로 40시간의 평가 루프를 닫습니다.',
    output: '전체 architecture · 관측 필드 · 다음 32시간 실행 지도',
    outcome: 'STT→LLM→Validation→Human Approval→Publish 흐름에서 무엇을 관측하고 어떤 기준으로 배포를 보류할지 설명합니다.',
    accent: C.green,
    concepts: [
      c('Managed 회의 기능은 현업의 현재 출발점', 'Google Meet 등은 전사·노트 기능을 제공하지만 계정·edition·관리자 설정에 의존한다.', '빠른 활용 / 정책·보존 / 지원 언어·edition 확인'),
      c('수업의 local STT는 원리를 이해하는 최소 실습', 'faster-whisper 또는 whisper.cpp로 audio→segment contract를 직접 확인한다.', 'offline 가능 / timestamp / model·device 선택'),
      c('STT 품질은 WER 하나로 끝나지 않는다', '업무에서는 이름·숫자·날짜·Action Item 근거 오류를 별도로 본다.', 'empty·repetition / entity error / timestamp / human correction'),
      c('LangSmith trace는 실행의 계보', 'graph run 아래 node·LLM·tool의 input/output·latency·error를 연결한다.', 'parent-child / metadata / tags / error'),
      c('민감 데이터는 trace 전에 줄인다', '교육 계정에는 공개·합성 샘플만 전송하고 원문·secret을 masking한다.', 'anonymize / sampling / local JSONL / retention 확인'),
      c('Dataset이 평가 입력을 고정', 'golden example과 실패 사례를 dataset으로 만들고 experiment를 반복한다.', 'input / reference output / metadata / version'),
      c('Evaluation은 schema와 의미를 나눈다', '결정론적 검사와 사람·LLM 기반 rubric을 구분한다.', 'schema pass / evidence rate / task correctness / reviewer feedback'),
      c('Human feedback은 품질 개선 데이터', 'approve·edit·reject와 수정량·이유를 trace에 연결한다.', 'decision / edit distance / reason / failure category'),
      c('Release gate가 모니터링을 행동으로', 'baseline이 떨어지거나 오발행 위험이 있으면 prompt·model 배포를 보류한다.', 'dataset score / failure rate / cost·latency / false publish=0'),
    ],
    procedures: [
      p('전체 pipeline', ['AUDIO', 'metadata·STT'], ['DRAFT', 'LLM·schema'], ['REVIEW', 'evidence·interrupt'], ['PUBLISH', '승인·idempotency']),
      p('STT 실행 순서', ['CHECK', 'format·duration'], ['TRANSCRIBE', 'segment'], ['QUALITY', 'empty·repeat'], ['FALLBACK', '정답 transcript']),
      p('Trace 설계 순서', ['QUESTION', '무엇을 알고 싶나'], ['FIELDS', '어떤 metadata'], ['BOUNDARY', '무엇을 숨기나'], ['VIEW', 'run tree·filter']),
      p('Dataset 구축', ['SEED', 'golden 3–5건'], ['FAIL', '예외 추가'], ['VERSION', '변경 기록'], ['EXPERIMENT', '같은 입력 비교']),
      p('평가 루프', ['RUN', 'dataset'], ['SCORE', 'deterministic'], ['REVIEW', 'human rubric'], ['DECIDE', 'release gate']),
      p('40시간 누적', ['DAY2', 'STT·회의록'], ['DAY3', '코드 리뷰'], ['DAY4', 'GitHub·HITL'], ['DAY5', '통합·평가·결과 정리']),
    ],
    screenshots: [
      s('faster-whisper · Python 기반 local STT', 'faster-whisper-official.png', 'faster-whisper 공식 GitHub', 'https://github.com/SYSTRAN/faster-whisper', ['Whisper 재구현', 'model·device·compute_type', 'segments generator', '수업 전 model 준비']),
      s('whisper.cpp · 경량 local 대안', 'whisper-cpp-official.png', 'whisper.cpp 공식 GitHub', 'https://github.com/ggml-org/whisper.cpp', ['C/C++ 기반', '다양한 환경', 'CLI 실습 대안', '모델 파일 사전 준비']),
      s('Google Meet 자동 노트 · 만들기보다 통합하기', 'google-meet-notes-official.png', 'Google Meet Take notes for me 도움말', 'https://support.google.com/meet/answer/14754931', ['구독·관리자 설정 의존', '기존 전사·요약 활용', 'local은 예외·통제 학습', '지원 범위 강의 전 확인']),
      s('LangSmith observability · trace tree', 'langsmith-observability-official.png', 'LangSmith Observability 공식 화면', 'https://docs.langchain.com/langsmith/observability', ['node별 input/output', 'latency·token·error', 'metadata·tag', '공개 샘플만']),
      s('LangSmith evaluation · dataset과 experiment', 'langsmith-evaluation-official.png', 'LangSmith Evaluation 공식 화면', 'https://docs.langchain.com/langsmith/evaluation', ['offline evaluation', 'online monitoring', 'human feedback', 'baseline 비교']),
    ],
    examples: [
      e('faster-whisper 최소 호출', 'from faster_whisper import WhisperModel\nmodel = WhisperModel(\"small\", device=\"cpu\", compute_type=\"int8\")\nsegments, info = model.transcribe(audio_path, language=\"ko\")\nrows = [{\"start\": s.start, \"end\": s.end, \"text\": s.text}\n        for s in segments]', ['CPU int8 경로', 'language 명시', 'segment timestamp', 'generator 소비'], { sources: ['https://github.com/SYSTRAN/faster-whisper'] }),
      e('STT 품질 flag', 'flags = []\nif not text.strip(): flags.append(\"EMPTY\")\nif repeated_ratio(text) > 0.35: flags.append(\"REPETITION\")\nif duration > 0 and len(text) / duration < 0.5: flags.append(\"TOO_SPARSE\")\nif flags: status = \"NEEDS_REVIEW\"', ['무음', '반복', '지나치게 희소', '사람 검토']),
      e('LangSmith 환경 변수 경계', 'LANGSMITH_TRACING=true\nLANGSMITH_PROJECT=ipa-k-work-copilot\n# LANGSMITH_API_KEY is set outside notebook\n# never print or commit the key', ['프로젝트 분리', 'key 환경 변수', '교육 샘플만', 'tracing off fallback']),
      e('Trace metadata', 'metadata = {\n  \"dataset_version\": \"day2-v1\",\n  \"provider\": \"ollama\",\n  \"model\": \"qwen3:4b\",\n  \"thread_id\": request_id,\n  \"contains_pii\": False,\n  \"fallback_used\": False\n}', ['dataset version', 'provider·model', 'thread 연결', '민감성·fallback']),
      e('결정론적 evaluator', 'def evidence_rate(output):\n    claims = output[\"decisions\"] + output[\"action_items\"]\n    linked = [c for c in claims if c.get(\"evidence_ids\")]\n    return len(linked) / max(1, len(claims))\n\ndef schema_pass(output):\n    return MeetingResult.model_validate(output) is not None', ['근거 연결률', 'schema pass', '계산 재현', 'release threshold']),
      e('Release gate', 'gate = (\n  schema_pass_rate >= 0.98\n  and evidence_rate >= 0.90\n  and false_publish == 0\n  and p95_latency_ms <= target\n)\nstatus = \"READY\" if gate else \"HOLD\"', ['품질', '안전', '지연시간', '보류 상태']),
    ],
    labs: [
      l('실습 1 · Managed vs Local 선택표', '07 MIN', ['현재 조직의 회의 도구를 적는다.', '전사·요약 제공 여부를 적는다.', '계정·보존·권한 제약을 적는다.', 'local 최소 실습이 필요한 이유를 쓴다.'], 'Managed/Local 비교표'),
      l('실습 2 · STT quality policy', '08 MIN', ['무음 기준을 정한다.', '반복 기준을 정한다.', '이름·날짜 오류를 정한다.', '사람 검토로 보내는 조건을 적는다.'], 'STT review rule'),
      l('실습 3 · Trace에서 답할 질문', '08 MIN', ['가장 느린 node를 묻는다.', '가장 자주 실패한 오류를 묻는다.', '사람이 많이 수정한 필드를 묻는다.', '각 질문에 필요한 metadata를 적는다.'], '질문 3개 + 필드'),
      l('실습 4 · Evaluation dataset 설계', '10 MIN', ['정상 회의 2건을 정한다.', '무음·모호한 날짜·근거 누락 사례를 추가한다.', 'reference JSON을 정한다.', 'schema·evidence evaluator를 연결한다.'], 'dataset 5건 설계'),
      l('실습 5 · 전체 흐름을 한 장으로 연결하기', '10 MIN', ['STT부터 최종 저장까지 순서를 그립니다.', 'LangChain·LangGraph·LangSmith가 쓰이는 위치를 표시합니다.', '사람의 승인과 fallback 위치를 표시합니다.', '그림 아래에 전체 흐름을 세 문장으로 적습니다.'], '전체 흐름 1장 + 설명 3문장'),
    ],
    pitfalls: [
      f('실패 1 · STT 결과를 정답으로 간주', ['이름·숫자 오류', '무음 반복', '화자 혼동', 'timestamp 유실'], ['quality flags', '원문 audio link', '사람 correction', 'segment evidence']),
      f('실패 2 · 모든 trace에 원문 전송', ['개인정보', '회사 기밀', '보존 정책 불명', '교육 계정 혼용'], ['공개·합성 샘플', 'masking', 'metadata 최소화', 'local JSONL fallback']),
      f('실패 3 · trace만 보고 평가 완료', ['관찰은 가능', '정답 기준 없음', '회귀 판단 불가', 'release 결정 없음'], ['dataset', 'evaluator', 'baseline', 'gate·HOLD']),
      f('실패 4 · 무료 포함량을 무제한으로 오해', ['대량 trace', '장기 retention', '팀 공유', '예상치 못한 비용'], ['현재 계정 한도 확인', '수업 project 분리', '소량 dataset', 'tracing off 대체'], { sources: ['https://docs.langchain.com/langsmith/billing', 'https://docs.langchain.com/langsmith/administration-overview'] }),
    ],
    tracks: [
      { title: '재직자 · 운영 dashboard 질문', leftTitle: '매일 볼 것', rightTitle: '배포 전 볼 것', left: ['failure rate', 'review queue', 'latency', 'cost·fallback'], right: ['dataset score', 'schema·evidence', 'false publish', 'rollback 기준'] },
      { title: '구직자 · 포트폴리오 README 정리', leftTitle: 'README에 쓸 내용', rightTitle: '함께 넣을 증거', left: ['풀려는 문제', '실행 방법', '실패와 복구', '한계와 다음 단계'], right: ['audio/text', 'approved output', 'failure recovery', 'repo·tests·eval'] },
    ],
    checkpoint: { title: '17:30–18:00 · Q&A와 Exit Ticket', prompt: '오늘 막힌 부분을 먼저 복구하고, 마지막에는 내 Workflow를 READY 또는 HOLD로 판단합니다.', questions: ['내 흐름에서 자동 실행과 사람 승인의 경계는 어디인가?', '실패 뒤 다시 시작할 checkpoint와 fallback은 무엇인가?', '어떤 trace·dataset 신호가 나오면 다음 배포를 HOLD할 것인가?'], note: '17:30부터 30분을 Q&A·실습 복구·Exit Ticket에 사용한다. 여기서만 Day 1 전체 구조를 짧게 회수한다. Day2–5는 일반 점심 12:00–13:00으로 운영한다고 공지한다.' },
  },
];

const MODULE_LENSES = [
  {
    title: "AI Agent를 만드는 일은, 책임 경계를 그리는 일",
    insightLabel: "제품과 데모가 갈리는 지점",
    thesis: "모델은 계속 바뀐다. 누가 승인하고 어디서 멈추는지는 제품에 남는다.",
    question: "이 Agent가 틀렸을 때, 우리는 어디서 발견하고 어떻게 멈출 것인가?",
    glossaryTitle: "먼저 네 단어의 역할만 잡고 갑니다",
    claimLabel: "이 경력이 수업에 남긴 기준",
    tutorialTitle: "강사의 완성 흐름은 이 네 화면에서 시작합니다",
    tutorialLead: "Agent 도구 → 저장소 → 실제 코드 → test 증거로 이어지는 출발 경로",
    toolComparison: [
      ["VS Code", "IDE·주 실습 공간", "코드·터미널·Notebook·Git을 한 화면에서 연결", "PyCharm보다 가볍고 확장 기반"],
      ["Jupyter", "설명과 셀 실행", "처음 배우는 사람이 단계별 결과를 바로 확인", "Colab은 설치가 없지만 세션·자원 제약"],
      ["Git·GitHub", "버전·포트폴리오", "diff·commit·README로 완료 증거를 남김", "Drive 공유보다 변경 이력이 선명"],
      ["Codex·Claude", "Coding Agent·가속", "spec→diff→test 데모와 코드 검토를 빠르게 반복", "필수 도구가 아닌 선택적 Harness"],
    ],
    tutorialRoutes: [["작업 범위를 repo 안으로 제한", "spec·diff 확인"], ["같은 저장소에서 두 번째 검토", "변경·test 비교"], ["수업 폴더의 역할부터 찾기", "src·tests·materials"], ["제어 루프의 허용 tool 확인", "read-only 경계"]],
    fieldNotes: [
      "데모는 ‘된다’를 보여주고, 제품은 ‘안 될 때’를 설명한다.",
      "좋은 문제 정의는 기능 목록보다 금지 행동이 먼저 보인다.",
      "포트폴리오의 차이는 모델명이 아니라 실패를 다룬 증거에서 난다.",
    ],
  },
  {
    title: "Tool Calling은 실행 권한을 설계하는 일",
    insightLabel: "권한 설계의 핵심",
    thesis: "모델이 무엇을 원했는지보다, 애플리케이션이 무엇을 허용했는지가 중요하다.",
    question: "모델의 제안을 실제 행동으로 바꾸기 전에 누가 마지막으로 검사하는가?",
    glossaryTitle: "실행 전에 알아야 할 네 가지 계약",
    mapTitle: "모델의 JSON은 아직 실행이 아닙니다",
    mapSteps: [["요청", "tool name과 arguments를 분리"], ["계약", "required·type·추가 필드를 검사"], ["권한", "allowlist와 workspace 경계를 확인"], ["실행", "registry에 등록된 함수만 호출"], ["기록", "result와 audit event를 함께 남김"]],
    claimLabel: "실행 전에 고정할 경계",
    tutorialTitle: "‘실행 허가’가 생기는 화면을 순서대로 봅니다",
    tutorialLead: "API 형식 → 인증 경계 → test 규칙 → 실제 통과 화면",
    tutorialRoutes: [["요청·응답 형식 확인", "base URL·payload"], ["인증을 코드 밖으로 분리", "환경 변수·최소 권한"], ["실패를 test 함수로 고정", "assert·error code"], ["정상·예외를 한 번에 실행", "10 passed"]],
    fieldNotes: [
      "Tool schema가 친절할수록 모델은 똑똑해 보이고, allowlist가 단단할수록 제품은 안전해진다.",
      "오류 메시지도 제품 계약이다. 복구할 수 없는 오류는 관측되지 않은 오류다.",
      "외부 쓰기 권한은 기능이 아니라 책임의 이전이다.",
    ],
  },
  {
    title: "한국어 데이터의 핵심은 맥락과 책임",
    insightLabel: "한국어 업무 데이터의 함정",
    thesis: "문장이 자연스러운가보다, 누가 무엇을 언제 하기로 했는지가 보존돼야 한다.",
    question: "요약이 그럴듯해도 원문 근거를 찾지 못하면 업무 결과라고 부를 수 있는가?",
    glossaryTitle: "한국어 데이터를 읽는 네 가지 단위",
    mapTitle: "한국어 요약보다 먼저 근거 단위를 만듭니다",
    mapSteps: [["출처", "공식 원문과 이용 조건을 확인"], ["단위", "발화를 segment와 timestamp로 분리"], ["민감성", "개인정보와 회사 정보를 비식별"], ["정답", "결정·담당자·기한·근거를 연결"], ["고정", "대표 실패를 Golden Dataset에 추가"]],
    claimLabel: "업무 사고를 막는 데이터 기준",
    tutorialTitle: "데이터보다 먼저 출처와 발화 구조를 확인합니다",
    tutorialLead: "공공 데이터 → 말뭉치 → 회의록 → Managed 전사 화면",
    toolComparison: [
      ["서울 열린데이터광장", "공공·행정 데이터", "한국어 공개 데이터의 출처와 갱신 주기를 확인", "회의 발화 데이터는 별도 가공 필요"],
      ["모두의 말뭉치", "한국어 원자료", "문장·대화 자료의 언어 특성을 이해", "이용 신청과 재배포 조건 확인"],
      ["국회 회의록", "공식 회의 발화", "화자·안건·발언 구조가 실제 업무와 가까움", "목표 업무에 맞는 정답 라벨은 없음"],
      ["Google Meet", "Managed STT·노트", "현업에 이미 있는 전사·요약 기능을 활용", "구독·edition·관리자 정책 의존"],
    ],
    tutorialRoutes: [["공식 metadata와 갱신 주기 확인", "출처·이용 조건"], ["한국어 원자료 범위 확인", "말뭉치 유형"], ["실제 발화와 회의 구조 확인", "화자·안건·시각"], ["Managed 기능의 지원 경계 확인", "계정·edition·보존"]],
    fieldNotes: [
      "한국어 회의록에서 가장 비싼 오류는 문법이 아니라 사람·숫자·날짜 오류다.",
      "공개 데이터는 무료이지만, 사용할 수 있는 맥락까지 무료로 주지는 않는다.",
      "Golden Dataset은 정답 모음이 아니라 팀이 합의한 품질의 경계다.",
    ],
  },
  {
    title: "환경 구축의 목표는 설치 성공이 아니라 재현",
    insightLabel: "수업을 살리는 기준",
    thesis: "강사 컴퓨터에서 한 번 되는 것보다, 학생이 막힌 지점에서 다시 시작할 수 있어야 한다.",
    question: "설치가 실패해도 수업과 프로젝트를 계속할 수 있는 두 번째 경로가 있는가?",
    glossaryTitle: "설치보다 먼저 구분할 네 가지 환경",
    mapTitle: "같은 명령이 같은 Python을 가리켜야 합니다",
    mapSteps: [["확인", "OS·Python·Git 버전을 먼저 캡처"], ["격리", "프로젝트 .venv를 생성"], ["선택", "VS Code와 Notebook interpreter를 맞춤"], ["보호", "secret·대용량 파일을 Git 밖에 둠"], ["복구", "첫 commit과 fixture 경로를 남김"]],
    claimLabel: "학생이 다시 시작하려면 필요한 것",
    tutorialTitle: "설치 화면은 ‘어디서 받는가’보다 ‘무엇을 확인하는가’가 중요합니다",
    tutorialLead: "Python → VS Code interpreter → Git identity → sandbox repository",
    tutorialRoutes: [["내 OS에 맞는 runtime 선택", "버전·실행 경로"], ["editor가 쓸 Python 지정", ".venv interpreter"], ["Git 작성자와 기본 상태 확인", "identity·status"], ["교육용 저장소만 연결", "sandbox remote"]],
    fieldNotes: [
      "환경 문제의 절반은 패키지가 아니라 ‘지금 어떤 Python을 쓰는가’에서 시작한다.",
      "첫 commit은 저장이 아니라 복구 지점을 만드는 일이다.",
      "Harness Engineering의 출발은 좋은 프롬프트보다 깨끗한 작업공간이다.",
    ],
  },
  {
    title: "Agent는 똑똑함보다 멈출 줄 알아야 한다",
    insightLabel: "운영에서 먼저 터지는 곳",
    thesis: "planner의 화려함보다 timeout·validation·retry·stop이 제품의 신뢰도를 결정한다.",
    question: "이 실행 루프는 언제 재시도하고, 언제 사람에게 넘기고, 언제 완전히 멈추는가?",
    glossaryTitle: "Agent 실행 루프를 나누는 네 역할",
    mapTitle: "LLM을 붙이기 전에 실패 상태부터 고정합니다",
    mapSteps: [["계획", "규칙 기반 planner로 next action 선택"], ["검사", "validator가 schema와 policy 확인"], ["실행", "executor가 좁은 tool만 호출"], ["관찰", "ToolResult로 성공·실패를 정규화"], ["중단", "timeout·attempt·terminal status로 종료"]],
    claimLabel: "루프를 안정시키는 경계",
    tutorialTitle: "이 네 화면은 실행보다 복구 경로를 확인하기 위한 것입니다",
    tutorialLead: "Notebook 실행기 → interpreter → Agent 수정 → 같은 repo 검토",
    tutorialRoutes: [["Notebook kernel을 준비", "Run All 가능"], ["Terminal과 Notebook Python 맞추기", "같은 interpreter"], ["작은 spec으로 한 경계만 수정", "제한된 diff"], ["다른 Agent로 실패 조건 검토", "test 재실행"]],
    fieldNotes: [
      "무한 retry는 회복력이 아니라 장애를 늦게 발견하는 방식이다.",
      "결정론적 planner로 통과하지 못한 계약은 LLM을 넣어도 안정되지 않는다.",
      "Agent의 실력은 성공 횟수보다 실패 상태를 얼마나 잘 구분하는지에서 드러난다.",
    ],
  },
  {
    title: "무료 실습의 핵심은 교체 가능한 구조",
    insightLabel: "무료 실습의 진짜 조건",
    thesis: "Ollama가 없어도 fixture로 계속되고, provider가 바뀌어도 나머지 코드는 남아야 한다.",
    question: "특정 모델과 프로그램이 사라져도 이 실습의 핵심 계약은 그대로 실행되는가?",
    glossaryTitle: "모델을 교체하기 위한 네 가지 층",
    mapTitle: "프로그램이 달라도 generate 계약은 하나로 둡니다",
    mapSteps: [["선택", "PC 사양과 UI 선호로 provider 결정"], ["연결", "health와 base URL을 확인"], ["변환", "adapter가 요청·응답 차이를 흡수"], ["검증", "JSON parse와 schema를 순서대로 확인"], ["대체", "연결 실패 시 fixture로 계속 진행"]],
    claimLabel: "교체 가능한 구조가 남기는 것",
    tutorialTitle: "세 프로그램의 차이는 화면에서, 공통점은 adapter에서 봅니다",
    tutorialLead: "Ollama → model tag → LM Studio server → Jan API server",
    toolComparison: [
      ["Ollama", "CLI·localhost API", "명령 몇 줄로 local model과 API를 함께 실습", "GUI보다 단순하고 자동화에 유리"],
      ["LM Studio", "GUI·Local Server", "모델 탐색과 server 상태를 화면으로 확인", "초심자 친화적이나 GUI 조작이 필요"],
      ["Jan", "Desktop Local API", "OpenAI-compatible 대체 경로를 하나 더 확보", "생태계·문서 범위는 도구별 확인"],
      ["Fixture Provider", "설치 없는 고정 응답", "모델 설치가 실패해도 Schema·Graph 실습 지속", "생성 품질은 평가할 수 없는 복구 경로"],
    ],
    tutorialRoutes: [["OS별 local runner 설치", "localhost 응답"], ["작은 model tag 선택", "메모리·용량 확인"], ["GUI에서 API server 시작", "OpenAI-compatible URL"], ["대체 desktop server 연결", "같은 adapter"]],
    fieldNotes: [
      "무료는 비용 0원이 아니라 선택권이 남아 있는 구조다.",
      "adapter가 없으면 모델 교체가 곧 프로젝트 재개발이 된다.",
      "local LLM은 정답이 아니라 데이터·비용·지연시간 사이의 선택지다.",
    ],
  },
  {
    title: "LangGraph는 중단과 재시작을 설계한다",
    insightLabel: "Graph가 필요한 이유",
    thesis: "Graph의 가치는 멋진 그림이 아니라 중단·승인·재개를 같은 상태로 설명하는 데 있다.",
    question: "사람이 개입한 뒤에도 같은 요청과 같은 상태에서 안전하게 이어갈 수 있는가?",
    glossaryTitle: "중단과 재개를 설명하는 네 단어",
    mapTitle: "사람 검토를 버튼이 아니라 State 전이로 만듭니다",
    mapSteps: [["상태", "다음 node에 필요한 필드만 선언"], ["분기", "edge에 retry·review·failed 조건을 둠"], ["중단", "interrupt payload로 근거와 초안을 전달"], ["결정", "approve·edit·reject event를 저장"], ["재개", "같은 thread에서 idempotent하게 이어감"]],
    claimLabel: "Graph에 남겨야 할 상태",
    tutorialTitle: "LangChain의 조합과 LangGraph의 중단 지점을 구분해서 봅니다",
    tutorialLead: "조합 계층 → stateful orchestration → interrupt → persistence",
    toolComparison: [
      ["LangChain", "모델·Prompt·Tool 조합", "개별 AI 구성요소를 공통 인터페이스로 연결", "단순 호출은 SDK만으로도 가능"],
      ["LangGraph", "상태 기반 Workflow", "분기·중단·승인·재개를 State로 명시", "짧은 직선 흐름에는 과할 수 있음"],
      ["LangSmith", "관측·평가", "trace·dataset·experiment를 같은 실행 계보로 확인", "Local JSONL은 무료지만 UI·협업이 약함"],
      ["Pydantic·pytest", "계약·결정론적 검사", "Schema와 실패 조건을 빠르고 재현 가능하게 검증", "의미 품질 평가는 별도 rubric 필요"],
    ],
    tutorialRoutes: [["model·tool 조합 계층 확인", "LangChain 역할"], ["State와 route를 graph로 표현", "node·edge"], ["사람 입력 전에 안전하게 중단", "interrupt payload"], ["같은 thread에서 이어가기", "checkpoint·resume"]],
    fieldNotes: [
      "State에 모든 것을 넣는 순간 Graph는 기억장치가 아니라 쓰레기통이 된다.",
      "Human Approval은 버튼이 아니라 근거·결정·책임을 남기는 event다.",
      "Idempotency가 없는 resume은 자동화가 아니라 중복 사고의 예약이다.",
    ],
  },
  {
    title: "LangSmith는 배포 결정을 위한 증거다",
    insightLabel: "배포 전에 보는 신호",
    thesis: "Trace를 많이 쌓는 것보다, 어떤 실패에서 HOLD할지 미리 정하는 것이 먼저다.",
    question: "다음 버전을 배포하지 말아야 할 근거를 trace와 dataset에서 바로 찾을 수 있는가?",
    glossaryTitle: "관측과 배포 판단을 잇는 네 단어",
    mapTitle: "관측은 READY와 HOLD를 가를 때 끝납니다",
    mapSteps: [["입력", "Managed 또는 Local STT의 segment를 받음"], ["품질", "무음·반복·이름·날짜 오류를 flag"], ["계보", "node·LLM·tool을 trace tree로 연결"], ["비교", "같은 dataset으로 baseline과 candidate 실행"], ["결정", "품질·안전·지연 기준으로 READY/HOLD"]],
    claimLabel: "배포 전에 확인할 신호",
    tutorialTitle: "STT와 LangSmith 화면은 하나의 품질 루프로 연결됩니다",
    tutorialLead: "Local STT 두 경로 → Managed 노트 → trace tree → experiment",
    toolComparison: [
      ["Google Meet", "Managed 회의 STT", "이미 제공되는 전사·노트를 현업 출발점으로 사용", "Zoom·Teams도 유사하지만 구독 정책이 다름"],
      ["faster-whisper", "Python Local STT", "segment·timestamp를 코드에서 직접 다루기 쉬움", "whisper.cpp보다 Python 통합이 편함"],
      ["whisper.cpp", "경량 CLI STT", "낮은 사양·다양한 환경의 local 대안", "Python pipeline 연결은 추가 작업"],
      ["LangSmith Trace", "실행 관측", "node·LLM·tool의 지연·오류 계보를 한 화면에서 확인", "민감 데이터는 masking 또는 local trace"],
      ["LangSmith Eval", "Dataset·Experiment", "같은 입력으로 baseline과 candidate를 비교", "pytest는 구조 검사에 강하고 의미 평가는 제한"],
    ],
    tutorialRoutes: [["Python local 전사 경로 확인", "segment·timestamp"], ["경량 CLI 대안 확인", "model file·device"], ["기존 회의 노트 기능 확인", "관리자·보존 정책"], ["느린 node와 실패 계보 찾기", "run tree·metadata"], ["같은 dataset으로 버전 비교", "baseline·candidate"]],
    fieldNotes: [
      "STT가 틀리면 LLM은 틀린 입력을 더 그럴듯하게 정리한다.",
      "Trace는 과거 기록이 아니라 다음 실험 질문을 만드는 재료다.",
      "평가는 점수를 내는 일이 아니라 READY와 HOLD를 가르는 운영 결정이다.",
    ],
  },
];

const PART_GUIDES = [
  {
    partNumber: "1일차 1차시",
    partTime: "09:00-09:50",
    partSlides: "1-29",
    partTopic: "Agent와 문제 정의",
    partFlow: "09:00-09:12 강의 · 09:12-09:20 강사 시연 · 09:20-09:42 개인 실습 · 09:42-09:50 확인",
    partLearn: "Chatbot과 Agent의 차이 · 자동화 범위",
    partUnderstand: "모델보다 먼저 입력·결과·금지 행동을 정한다",
    partOutput: "자동화할 일 한 문장",
  },
  {
    partNumber: "1일차 2차시",
    partTime: "09:50-10:40",
    partSlides: "30-64",
    partTopic: "Tool Calling과 실행 권한",
    partFlow: "09:50-10:05 강의 · 10:05-10:15 코드 시연 · 10:15-10:35 개인 실습 · 10:35-10:40 확인",
    partLearn: "Tool schema · 허용 목록 · 실행 전 검사",
    partUnderstand: "모델의 제안과 실제 실행 권한은 다르다",
    partOutput: "허용할 도구와 막을 행동",
  },
  {
    partNumber: "1일차 3차시",
    partTime: "10:40-11:30",
    partSlides: "65-99",
    partTopic: "한국어 데이터와 PBL 사례",
    partFlow: "10:40-10:54 강의 · 10:54-11:04 Prompt·데이터 시연 · 11:04-11:25 개인 실습 · 11:25-11:30 저장",
    partLearn: "회의 데이터 · 담당자·기한·원문 근거",
    partUnderstand: "자연스러운 요약보다 근거가 남아야 한다",
    partOutput: "입력·결과·근거 예시",
  },
  {
    partNumber: "1일차 4차시",
    partTime: "12:00-12:50",
    partSlides: "100-134",
    partTopic: "Python·VS Code·Git 환경",
    partFlow: "12:00-12:10 강의 · 12:10-12:25 강사 세팅 시연 · 12:25-12:45 개인 실습 · 12:45-12:50 확인",
    partLearn: "Python 경로 · Interpreter · Git branch·PR · Codex review",
    partUnderstand: "설치보다 같은 명령으로 다시 실행되는 것이 중요하다",
    partOutput: "버전·경로·Draft PR 또는 local diff",
  },
  {
    partNumber: "1일차 5차시",
    partTime: "12:50-13:40",
    partSlides: "135-168",
    partTopic: "안전한 Agent 실행 루프",
    partFlow: "12:50-13:00 강의 · 13:00-13:10 코드 시연 · 13:10-13:35 개인 실습 · 13:35-13:40 확인",
    partLearn: "Planner · Validator · Executor · Test",
    partUnderstand: "LLM 전에 정상과 실패를 규칙으로 검증한다",
    partOutput: "정상·실패 test 결과",
  },
  {
    partNumber: "1일차 6차시",
    partTime: "15:00-15:40",
    partSlides: "169-202",
    partTopic: "무료·로컬 LLM과 Adapter",
    partFlow: "15:00-15:08 강의 · 15:08-15:18 연결 시연 · 15:18-15:35 개인 실습 · 15:35-15:40 확인",
    partLearn: "Ollama · LM Studio · Fixture Provider",
    partUnderstand: "모델이 없어도 같은 구조로 실습을 계속한다",
    partOutput: "성공 또는 예상된 실패 결과",
  },
  {
    partNumber: "1일차 7차시",
    partTime: "15:40-16:20",
    partSlides: "203-236",
    partTopic: "LangGraph와 사람 승인",
    partFlow: "15:40-15:48 강의 · 15:48-16:00 Graph 시연 · 16:00-16:15 개인 실습 · 16:15-16:20 확인",
    partLearn: "State · Node · Checkpoint · 승인·수정·거절",
    partUnderstand: "중요한 행동 전에는 멈추고 사람이 결정한다",
    partOutput: "승인·수정·거절 상태",
  },
  {
    partNumber: "1일차 8차시",
    partTime: "16:20-17:00",
    partSlides: "237-269",
    partTopic: "STT와 LangSmith",
    partFlow: "16:20-16:28 강의 · 16:28-16:38 Trace 시연 · 16:38-16:53 개인 실습 · 16:53-17:00 판단",
    partLearn: "STT 품질 · Trace · Dataset · 평가",
    partUnderstand: "실행 기록으로 READY와 HOLD를 결정한다",
    partOutput: "STT 품질 기준 + READY/HOLD 결정",
  },
];

const MODULE_TARGETS = [29, 35, 35, 35, 34, 34, 34, 34];

function moduleSelection(index, mod) {
  const conceptCount = index < 4 ? 8 : index < 7 ? 7 : 6;
  const conceptIndexes = index === 0
    ? [0, 2]
    : index === 1
      ? [0, 1, 2, 3, 4, 5, 6, 9]
      : Array.from({ length: conceptCount }, (_, i) => i);
  return {
    glossaries: GLOSSARIES[index],
    concepts: conceptIndexes.map((i) => mod.concepts[i]),
    procedures: index === 0
      ? mod.procedures.slice(0, 4)
      : mod.procedures.slice(0, 5),
    screenshots: mod.screenshots,
    examples: mod.examples.slice(0, 5),
    labs: mod.labs.slice(0, 4),
    pitfalls: mod.pitfalls.slice(0, 3),
    tracks: mod.tracks.slice(0, 1)
  };
}

function validateModuleCounts() {
  for (const [index, mod] of MODULES.entries()) {
    const selected = moduleSelection(index, mod);
    const count = 2 + (index === 0 ? 1 : 0) + 1 + selected.concepts.length + selected.procedures.length + 1 +
      selected.screenshots.length + selected.examples.length + selected.labs.length + selected.pitfalls.length + selected.tracks.length + 1;
    if (count !== MODULE_TARGETS[index]) throw new Error(`Module ${index + 1} has ${count} slides, expected ${MODULE_TARGETS[index]}.`);
  }
}

async function renderModule(mod, index) {
  const framed = { ...mod, ...MODULE_LENSES[index], ...PART_GUIDES[index] };
  const selected = moduleSelection(index, framed);
  if (index === 0) coverSlide(framed);
  else sectionSlide(framed);
  moduleMap(framed, index);
  if (index === 0) dayTimetableSlide(framed);
  let conceptsToRender = selected.concepts;
  if (index === 0 && selected.concepts[0]?.profileCareer) {
    profileCareerSlide(framed, selected.concepts[0]);
    conceptsToRender = selected.concepts.slice(1);
  }
  glossaryTableSlide(framed, selected.glossaries);
  for (const [i, item] of conceptsToRender.entries()) {
    const middle = Math.floor((conceptsToRender.length - 1) / 2);
    const insight = i === 0 ? framed.fieldNotes[0] : i === middle ? framed.fieldNotes[1] : i === conceptsToRender.length - 1 ? framed.fieldNotes[2] : null;
    if (item.profileCareer) {
      profileCareerSlide(framed, item);
    } else if (item.visualPair) {
      await referencePairSlide(framed, item);
    } else if (item.visual) {
      await referenceVisualSlide(framed, item);
    } else if (i % 2 === 0) {
      statementSlide(framed, item, i === 0 ? MODULE_ICONS[index] : null, insight);
    } else {
      keyPointsSlide(framed, {
        title: item.title,
        lead: item.claim,
        bullets: bulletParts(item.support),
        kicker: item.kicker,
        sources: item.sources,
        note: item.note,
        bulletSize: item.bulletSize,
        height: item.height ?? 60,
        gap: item.gap,
        bottom: insight ? `${framed.insightLabel}  |  ${insight}` : item.bottom,
      });
    }
  }
  selected.procedures.forEach((item) => item.variant ? openingGuidanceSlide(framed, item) : processSlide(framed, item));
  tutorialMapSlide({ ...framed, screenshots: selected.screenshots });
  for (const [screenshotIndex, item] of selected.screenshots.entries()) {
    await screenshotSlide(framed, { ...item, kicker: `TUTORIAL ${screenshotIndex + 1}/${selected.screenshots.length} · ACTUAL SCREEN` });
  }
  selected.examples.forEach((item) => codeSlide(framed, item));
  selected.labs.forEach((item) => exerciseSlide(framed, item));
  selected.pitfalls.forEach((item) => compareSlide(framed, item));
  selected.tracks.forEach((item) => compareSlide(framed, { ...item, kicker: 'CAREER TRACK' }));
  checkpointSlide(framed, framed.checkpoint);
}

validateModuleCounts();
for (const [index, mod] of MODULES.entries()) await renderModule(mod, index);
if (deck.slides.items.length !== 270) throw new Error('Expected 270 slides, got ' + deck.slides.items.length + '.');

await fs.mkdir(path.dirname(OUT), { recursive: true });
const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log('Wrote ' + deck.slides.items.length + ' slides to ' + OUT);
