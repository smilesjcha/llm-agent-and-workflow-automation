import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import { MUSINSA_PPT, MUSINSA_REFERENCE, makeCoursePalette } from "../../design-system/ppt/cha-sungjae-musinsa-lecture/design-system.mjs";
import { CODEX_OFFICIAL_SOURCE, COURSE_DAYS, DAY_TIMES, OPENAI_CODEX_DOCS } from "./days2_5_content.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const argIndex = process.argv.indexOf("--day");
const day = Number(argIndex >= 0 ? process.argv[argIndex + 1] : process.env.COURSE_DAY);
if (![2, 3, 4, 5].includes(day)) throw new Error("--day must be one of 2, 3, 4, 5");

const config = COURSE_DAYS[day];
const outPath = path.join(ROOT, `slides/IPA_LLM_Agent_업무자동화_Day${day}_MUSINSA_DRAFT_240p.pptx`);
const C = makeCoursePalette();
const FONT = "AppleGothic";
const deck = Presentation.create({ slideSize: MUSINSA_PPT.slide });
const screenshotBytes = new Map();

function addShape(slide, geometry, position, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({ geometry, position, fill, line: { style: "solid", fill: lineFill, width: lineWidth } });
}

function addText(slide, text, position, options = {}) {
  const box = addShape(slide, "textbox", position, options.fill ?? "none", options.lineFill ?? "none", options.lineWidth ?? 0);
  box.text = String(text).replace(/[–—]/g, "-");
  box.text.style = {
    fontSize: options.size ?? 20,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    typeface: FONT,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.1,
    insets: options.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

function addNotes(slide, teachingJob, sources = []) {
  const allSources = [...new Set([MUSINSA_REFERENCE, ...sources])];
  slide.speakerNotes.textFrame.setText([
    `이 장표의 역할: ${teachingJob}`,
    "진행: 제목을 먼저 읽고 화면의 근거를 위에서 아래로 확인한다.",
    "온라인 진행: 발표를 요구하지 않는다. 실행 결과나 첫 오류 한 줄만 채팅으로 확인한다.",
    "",
    "[Sources]",
    ...allSources.map((source) => `- ${source}`),
    "[/Sources]",
  ].join("\n"));
  slide.speakerNotes.setVisible(true);
}

function partNumber(index) {
  return index + 1;
}

function partTime(index) {
  return DAY_TIMES[index][0];
}

function accumulatedBreak(index) {
  return index < 3 ? "쉬는 시간 11:30-12:00" : "쉬는 시간 17:10-17:40";
}

function addFooter(slide, periodIndex, page) {
  addShape(slide, "line", { left: 64, top: 674, width: 1152, height: 0 }, "none", C.faint, 1);
  addText(slide, `DAY ${day} · ${config.service}`, { left: 64, top: 684, width: 430, height: 16 }, { size: 10, bold: true, color: C.muted });
  addText(slide, `${partTime(periodIndex)} · ${partNumber(periodIndex)}차시`, { left: 494, top: 684, width: 300, height: 16 }, { size: 10, color: C.ink, align: "center" });
  addText(slide, String(page).padStart(3, "0"), { left: 1120, top: 684, width: 96, height: 16 }, { size: 10, bold: true, color: C.muted, align: "right" });
}

function addHeader(slide, title, periodIndex, label = "") {
  const page = deck.slides.items.length;
  slide.background.fill = C.paper;
  if (label) addText(slide, label, { left: 64, top: 38, width: 560, height: 18 }, { size: 11, bold: true, color: C.muted });
  addText(slide, title, { left: 64, top: label ? 72 : 54, width: 1152, height: 74 }, { size: 36, bold: true, color: C.ink, valign: "top" });
  addFooter(slide, periodIndex, page);
}

function addBullets(slide, bullets, position, options = {}) {
  const rowHeight = options.rowHeight ?? 72;
  bullets.forEach((item, index) => {
    const y = position.top + index * rowHeight;
    addText(slide, String(index + 1).padStart(2, "0"), { left: position.left, top: y + 4, width: 36, height: 28 }, { size: 13, bold: true, color: C.muted });
    addShape(slide, "line", { left: position.left + 46, top: y + 17, width: 34, height: 0 }, "none", C.black, 2);
    addText(slide, item, { left: position.left + 96, top: y, width: position.width - 96, height: rowHeight - 10 }, { size: options.size ?? 21, bold: options.bold ?? false, color: C.ink });
  });
}

function addCover(period, periodIndex) {
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  addShape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  addText(slide, periodIndex === 0 ? "IPA · LLM AGENT & 업무자동화 40H" : `DAY ${day} · ${partNumber(periodIndex)}차시`, { left: 84, top: 62, width: 720, height: 26 }, { size: 14, bold: true, color: C.white });
  addText(slide, `${partTime(periodIndex)}  (${accumulatedBreak(periodIndex)})`, { left: 84, top: 108, width: 840, height: 34 }, { size: 20, bold: true, color: C.blue });
  addText(slide, period.title, { left: 84, top: 176, width: 1080, height: 142 }, { size: 54, bold: true, color: C.white, lineSpacing: 0.98, valign: "middle" });
  addText(slide, period.outcome, { left: 88, top: 340, width: 1040, height: 70 }, { size: 25, bold: true, color: C.faint });
  addShape(slide, "line", { left: 84, top: 448, width: 1092, height: 0 }, "none", C.blue, 3);
  const columns = [
    ["진행", period.mode],
    ["사용 파일", period.files.slice(0, 2).join("\n")],
    ["확인할 결과", period.artifact],
  ];
  columns.forEach(([label, value], index) => {
    const x = 84 + index * 364;
    addText(slide, label, { left: x, top: 476, width: 330, height: 22 }, { size: 12, bold: true, color: C.gray300 });
    addText(slide, value, { left: x, top: 510, width: 330, height: 84 }, { size: 18, bold: true, color: C.white });
  });
  addText(slide, `${config.deckTitle} · ${partNumber(periodIndex)}차시`, { left: 84, top: 640, width: 1092, height: 20 }, { size: 11, bold: true, color: C.gray300, align: "right" });
  addNotes(slide, `${partNumber(periodIndex)}차시의 목표와 실행 결과를 먼저 공유한다.`, ["local:IPA_40H_상세_커리큘럼_및_무료실습_설계.md"]);
}

function addTimetable(periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, `${day}일차는 여덟 개 차시로 하나의 서비스를 완성합니다`, periodIndex, "하루 전체 시간표");
  addText(slide, "오전 3개 차시 뒤 30분 휴식, 12:00-13:00 점심, 오후 5개 차시 뒤 휴식과 Q&A로 마무리합니다.", { left: 64, top: 136, width: 1152, height: 30 }, { size: 17, bold: true, color: C.muted });
  const widths = [170, 92, 426, 264, 200];
  const labels = ["시간", "차시", "배우는 내용", "진행", "확인할 결과"];
  let x = 64;
  labels.forEach((label, index) => {
    addShape(slide, "rect", { left: x, top: 180, width: widths[index], height: 38 }, C.black);
    addText(slide, label, { left: x + 10, top: 188, width: widths[index] - 20, height: 20 }, { size: 12, bold: true, color: C.white, valign: "middle" });
    x += widths[index];
  });
  config.periods.forEach((period, index) => {
    let xx = 64;
    const y = 218 + index * 50;
    const cells = [DAY_TIMES[index][0], `${index + 1}차시`, period.title, "강의 12\n시연 10\n소프트웨어 실습 23\n확인 5분", period.artifact];
    cells.forEach((value, cellIndex) => {
      addShape(slide, "rect", { left: xx, top: y, width: widths[cellIndex], height: 50 }, index % 2 ? C.gray025 : C.white, C.faint, 1);
      addText(slide, value, { left: xx + 10, top: y + 7, width: widths[cellIndex] - 20, height: 36 }, { size: cellIndex === 2 ? 13 : 11, bold: cellIndex === 0 || cellIndex === 1, color: C.ink, valign: "middle" });
      xx += widths[cellIndex];
    });
  });
  addText(slide, "11:30-12:00 쉬는 시간 · 12:00-13:00 점심시간 · 17:10-17:40 쉬는 시간 · 17:40-18:00 Q&A·실행 복구", { left: 64, top: 630, width: 1152, height: 24 }, { size: 13, bold: true, color: C.ink, align: "center" });
  addNotes(slide, "수강생이 현재 차시와 강의·시연·소프트웨어 실습 비중을 한 번에 확인한다.", ["local:IPA_40H_상세_커리큘럼_및_무료실습_설계.md"]);
}

function addPositionMap(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, `${partNumber(periodIndex)}차시는 앞의 결과를 이어받아 다음 상태를 만듭니다`, periodIndex, "현재 위치");
  const prev = config.periods[periodIndex - 1];
  const next = config.periods[periodIndex + 1];
  const items = [
    ["입력", prev ? prev.artifact : "Day 1 검증 결과"],
    ["이번 차시", period.title],
    ["결과", period.artifact],
    ["다음 연결", next ? next.title : "Q&A·실행 복구·release 판단"],
  ];
  items.forEach(([label, value], index) => {
    const y = 164 + index * 112;
    addText(slide, label, { left: 72, top: y + 18, width: 120, height: 28 }, { size: 14, bold: true, color: C.muted });
    addShape(slide, "line", { left: 206, top: y + 31, width: 80, height: 0 }, "none", index === 1 ? C.blue : C.black, index === 1 ? 4 : 2);
    addText(slide, value, { left: 316, top: y, width: 836, height: 72 }, { size: 25, bold: index === 1, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "앞 차시의 결과 파일이 이번 차시 입력으로 이어지는 구조를 확인한다.", ["local:IPA_40H_상세_커리큘럼_및_무료실습_설계.md"]);
}

function addClaim(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, period.why, periodIndex);
  addText(slide, period.outcome, { left: 80, top: 210, width: 1040, height: 116 }, { size: 38, bold: true, color: C.ink, valign: "middle", align: "center" });
  addShape(slide, "line", { left: 384, top: 376, width: 512, height: 0 }, "none", C.blue, 4);
  addText(slide, `이번 차시의 확인 결과: ${period.artifact}`, { left: 180, top: 418, width: 920, height: 46 }, { size: 19, bold: true, color: C.muted, align: "center" });
  addNotes(slide, "이번 차시가 필요한 이유를 한 문장으로 먼저 이해시킨다.");
}

function addOutcome(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "이 차시가 끝나면 세 가지를 설명하고 실행할 수 있습니다", periodIndex);
  addBullets(slide, [
    period.outcome,
    `${period.failure} 왜 위험한지 설명한다.`,
    `${period.artifact}에서 정상과 실패 상태를 직접 확인한다.`,
  ], { left: 96, top: 190, width: 1060 }, { rowHeight: 122, size: 24 });
  addNotes(slide, "학습 결과를 설명·실행·검증의 세 수준으로 나눈다.");
}

function addTermTable(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "처음 보는 용어는 이 네 가지 역할만 구분합니다", periodIndex, "용어 풀이");
  const left = 80;
  const widths = [260, 820];
  [["용어", "이 수업에서 쓰는 뜻"], ...period.terms].forEach((row, rowIndex) => {
    let x = left;
    row.forEach((value, colIndex) => {
      const y = 158 + rowIndex * 90;
      addShape(slide, "rect", { left: x, top: y, width: widths[colIndex], height: 90 }, rowIndex === 0 ? C.black : rowIndex % 2 ? C.gray025 : C.white, rowIndex === 0 ? C.black : C.faint, 1);
      addText(slide, value, { left: x + 18, top: y + 18, width: widths[colIndex] - 36, height: 54 }, { size: rowIndex === 0 ? 14 : colIndex === 0 ? 23 : 20, bold: rowIndex === 0 || colIndex === 0, color: rowIndex === 0 ? C.white : C.ink, valign: "middle" });
      x += widths[colIndex];
    });
  });
  addNotes(slide, "영문 약어보다 업무에서 맡는 역할과 concrete example을 먼저 설명한다.");
}

function addInputOutput(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "입력·처리·결과·검증을 분리하면 문제가 빨리 보입니다", periodIndex);
  const items = [
    ["INPUT", period.files[0]],
    ["PROCESS", period.pipeline.slice(0, 3).join(" → ")],
    ["OUTPUT", period.artifact],
    ["VERIFY", `${period.normalTest}\n${period.boundaryTest}`],
  ];
  items.forEach(([label, value], index) => {
    const x = 72 + (index % 2) * 568;
    const y = 166 + Math.floor(index / 2) * 214;
    addText(slide, label, { left: x, top: y, width: 520, height: 22 }, { size: 12, bold: true, color: C.muted });
    addShape(slide, "line", { left: x, top: y + 40, width: 520, height: 0 }, "none", C.black, 2);
    addText(slide, value, { left: x, top: y + 62, width: 520, height: 112 }, { size: 21, bold: index === 2, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "오류가 입력·처리·결과·검증 중 어디에서 생겼는지 구분한다.");
}

function addProcess(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "실행 흐름은 다섯 단계로 고정합니다", periodIndex, "업무 흐름");
  period.pipeline.forEach((value, index) => {
    const x = 72 + index * 226;
    addText(slide, String(index + 1).padStart(2, "0"), { left: x, top: 190, width: 72, height: 52 }, { size: 35, bold: true, color: index === 0 ? C.blue : C.ink });
    addShape(slide, "line", { left: x, top: 264, width: 190, height: 0 }, "none", C.black, 2);
    addText(slide, value, { left: x, top: 292, width: 190, height: 116 }, { size: 21, bold: true, color: C.ink });
  });
  addText(slide, `마지막 판단은 ${period.artifact}에서 사람이 확인합니다.`, { left: 160, top: 486, width: 960, height: 58 }, { size: 23, bold: true, color: C.ink, align: "center" });
  addNotes(slide, "각 단계의 입력과 다음 상태를 연결해 실행 순서를 설명한다.");
}

function addContract(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "코드보다 먼저 성공·실패 계약을 정합니다", periodIndex);
  const rows = [
    ["정상", period.normalTest],
    ["경계", period.boundaryTest],
    ["외부 쓰기", "기본값 false · dry-run과 사람 승인 뒤에만 별도 adapter 호출"],
    ["기록", `status·error_code·입력 식별자·${period.artifact}`],
  ];
  rows.forEach(([label, value], index) => {
    const y = 160 + index * 112;
    addText(slide, label, { left: 80, top: y + 20, width: 150, height: 30 }, { size: 15, bold: true, color: C.muted });
    addShape(slide, "line", { left: 246, top: y + 34, width: 62, height: 0 }, "none", C.black, 2);
    addText(slide, value, { left: 340, top: y, width: 820, height: 72 }, { size: 22, bold: index === 0, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "정상 결과와 가장 중요한 실패 결과를 같은 수준의 제품 계약으로 설명한다.");
}

function addFiles(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "어떤 파일을 열고 어디에서 결과를 확인하는지 먼저 봅니다", periodIndex, "저장소 지도");
  const roles = ["입력·fixture", "구현 코드", "검증·test", "따라하기 notebook"];
  period.files.forEach((file, index) => {
    const y = 158 + index * 112;
    addText(slide, roles[index], { left: 72, top: y + 18, width: 190, height: 28 }, { size: 14, bold: true, color: C.muted });
    addShape(slide, "rect", { left: 286, top: y, width: 860, height: 72 }, index % 2 ? C.gray025 : C.white, C.faint, 1);
    addText(slide, file, { left: 310, top: y + 18, width: 810, height: 36 }, { size: 22, bold: true, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "수강생이 notebook·src·tests·data의 역할을 혼동하지 않게 실행 전에 경로를 확인한다.", period.files.map((file) => `local:${file}`));
}

function addConcept(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, period.title, periodIndex, "개념을 코드로 연결하기");
  addText(slide, period.why, { left: 72, top: 164, width: 760, height: 128 }, { size: 30, bold: true, color: C.ink });
  addShape(slide, "rect", { left: 870, top: 158, width: 290, height: 350 }, C.black);
  addText(slide, "이 차시에서\n버릴 오해", { left: 902, top: 194, width: 226, height: 74 }, { size: 18, bold: true, color: C.gray300, align: "center" });
  addText(slide, period.failure, { left: 906, top: 298, width: 218, height: 164 }, { size: 20, bold: true, color: C.white, align: "center", valign: "middle" });
  addText(slide, period.recovery, { left: 72, top: 350, width: 760, height: 142 }, { size: 23, bold: true, color: C.ink });
  addNotes(slide, "흔한 오해와 안전한 복구 원칙을 한 화면에서 대조한다.");
}

function addComparison(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "비슷해 보이는 선택도 책임과 검증 범위가 다릅니다", periodIndex, "선택 기준");
  const rows = [
    [period.terms[0][0], period.terms[0][1], "결정론 test로 먼저 확인"],
    [period.terms[1][0], period.terms[1][1], "adapter 경계를 확인"],
    [period.terms[2][0], period.terms[2][1], "비용·지연·권한을 확인"],
    [period.terms[3][0], period.terms[3][1], "사람 판단과 운영 기록을 확인"],
  ];
  const widths = [250, 480, 410];
  [["구분", "역할", "이번 차시의 판단 기준"], ...rows].forEach((row, rowIndex) => {
    let x = 70;
    row.forEach((value, colIndex) => {
      const y = 158 + rowIndex * 92;
      addShape(slide, "rect", { left: x, top: y, width: widths[colIndex], height: 92 }, rowIndex === 0 ? C.black : rowIndex % 2 ? C.gray025 : C.white, rowIndex === 0 ? C.black : C.faint, 1);
      addText(slide, value, { left: x + 16, top: y + 16, width: widths[colIndex] - 32, height: 60 }, { size: rowIndex === 0 ? 13 : 18, bold: rowIndex === 0 || colIndex === 0, color: rowIndex === 0 ? C.white : C.ink, valign: "middle" });
      x += widths[colIndex];
    });
  });
  addNotes(slide, "용어를 나열하지 않고 역할과 선택 기준을 비교한다.");
}

function addFailure(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "가장 먼저 재현할 실패는 이것입니다", periodIndex, "실패 사례");
  addShape(slide, "rect", { left: 72, top: 170, width: 496, height: 348 }, C.black);
  addText(slide, "실패", { left: 104, top: 202, width: 160, height: 30 }, { size: 14, bold: true, color: C.gray300 });
  addText(slide, period.failure, { left: 104, top: 260, width: 432, height: 184 }, { size: 26, bold: true, color: C.white, valign: "middle" });
  addText(slide, "사용자 영향", { left: 628, top: 202, width: 180, height: 30 }, { size: 14, bold: true, color: C.muted });
  addText(slide, period.why, { left: 628, top: 260, width: 506, height: 184 }, { size: 25, bold: true, color: C.ink, valign: "middle" });
  addText(slide, "실패가 재현돼야 복구 코드와 회귀 test를 만들 수 있습니다.", { left: 160, top: 568, width: 960, height: 34 }, { size: 18, bold: true, color: C.ink, align: "center" });
  addNotes(slide, "대표 실패를 숨기지 않고 사용자 영향까지 연결한다.");
}

function addRecovery(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "복구는 재시도보다 먼저 중단 조건을 정합니다", periodIndex, "복구 경로");
  addBullets(slide, [
    `탐지: ${period.boundaryTest}`,
    `중단: ${period.failure}`,
    `복구: ${period.recovery}`,
    `증거: ${period.artifact}과 test 결과를 함께 남긴다.`,
  ], { left: 88, top: 158, width: 1080 }, { rowHeight: 105, size: 22 });
  addNotes(slide, "재시도·fallback·사람 검토·완전 중단 중 어느 경로를 선택하는지 설명한다.");
}

async function addCodexReference(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "Codex는 코드를 대신 쓰는 도구보다 검증 루프에 가깝습니다", periodIndex, "Codex 활용");
  const [file, source] = period.screenshot;
  const imagePath = path.join(ROOT, "assets/screenshots", file);
  try {
    if (!screenshotBytes.has(imagePath)) screenshotBytes.set(imagePath, await fs.readFile(imagePath));
    slide.images.add({
      blob: screenshotBytes.get(imagePath),
      contentType: file.endsWith(".jpg") ? "image/jpeg" : "image/png",
      alt: `${period.title} 참고 화면`,
      fit: "contain",
      position: { left: 526, top: 156, width: 650, height: 438 },
      geometry: "rect",
      borderRadius: 0,
    });
  } catch {
    addShape(slide, "rect", { left: 526, top: 156, width: 650, height: 438 }, C.gray025, C.faint, 1);
    addText(slide, file, { left: 566, top: 330, width: 570, height: 50 }, { size: 18, bold: true, color: C.muted, align: "center" });
  }
  addText(slide, period.codex, { left: 72, top: 180, width: 402, height: 182 }, { size: 27, bold: true, color: C.ink });
  addText(slide, "저장소 이해\n→ 허용 범위 변경\n→ focused test\n→ diff 리뷰\n→ 사람 merge", { left: 72, top: 406, width: 402, height: 158 }, { size: 21, bold: true, color: C.muted, lineSpacing: 1.24 });
  addNotes(slide, "Codex의 공식 use case를 현재 차시의 코드·test·review 흐름에 연결한다.", [source, CODEX_OFFICIAL_SOURCE, OPENAI_CODEX_DOCS]);
}

function addCodexTask(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "Codex에게는 목표보다 완료 조건을 더 구체적으로 줍니다", periodIndex, "작업 요청 예시");
  const task = [
    ["목표", period.codex],
    ["허용 경로", period.files.slice(1, 3).join("\n")],
    ["완료 조건", `${period.normalTest}\n${period.boundaryTest}`],
    ["금지", "secret 출력 · workspace 밖 변경 · test 약화 · 사람 승인 없는 외부 쓰기"],
  ];
  task.forEach(([label, value], index) => {
    const y = 150 + index * 118;
    addText(slide, label, { left: 72, top: y + 16, width: 150, height: 28 }, { size: 14, bold: true, color: C.muted });
    addShape(slide, "rect", { left: 240, top: y, width: 920, height: 84 }, index === 2 ? C.gray025 : C.white, C.faint, 1);
    addText(slide, value, { left: 266, top: y + 16, width: 868, height: 52 }, { size: 19, bold: index === 0, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "목표·허용 범위·test·금지 행동을 한 요청 안에 묶는 Harness 작성법을 보여준다.", [CODEX_OFFICIAL_SOURCE, OPENAI_CODEX_DOCS, "local:AGENTS.md"]);
}

function addCodexReview(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "생성된 patch는 diff와 test 증거를 보고 사람이 결정합니다", periodIndex, "Codex 검증 루프");
  const checks = [
    ["01", "Scope", "허용 경로 밖 파일이 바뀌지 않았는가"],
    ["02", "Focused test", period.normalTest],
    ["03", "Boundary test", period.boundaryTest],
    ["04", "Human merge", "Codex 리뷰와 test 통과는 자동 승인이 아니다"],
  ];
  checks.forEach(([number, label, value], index) => {
    const y = 158 + index * 112;
    addText(slide, number, { left: 76, top: y + 12, width: 50, height: 28 }, { size: 14, bold: true, color: C.muted });
    addText(slide, label, { left: 150, top: y, width: 220, height: 56 }, { size: 24, bold: true, color: C.ink, valign: "middle" });
    addShape(slide, "line", { left: 392, top: y + 28, width: 60, height: 0 }, "none", C.black, 2);
    addText(slide, value, { left: 486, top: y, width: 672, height: 62 }, { size: 20, bold: false, color: C.ink, valign: "middle" });
  });
  addNotes(slide, "Codex 실행 결과를 사람이 merge하기 전 확인할 네 가지 증거를 설명한다.", [CODEX_OFFICIAL_SOURCE, "local:AGENTS.md"]);
}

function addDemoSetup(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "강사가 먼저 정상 경로를 끝까지 실행합니다", periodIndex, "강사 시연");
  addBullets(slide, [
    `열기: ${period.files[0]}`,
    `구현 확인: ${period.files[1]}`,
    `실행: ${period.command}`,
    `성공 신호: ${period.normalTest}`,
  ], { left: 92, top: 160, width: 1060 }, { rowHeight: 104, size: 22 });
  addNotes(slide, "수강생 실행 전에 입력·코드·명령·성공 신호를 강사가 한 번 연결해 보여준다.", period.files.slice(0, 2).map((file) => `local:${file}`));
}

function addCommand(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "같은 저장소에서 이 명령을 실행합니다", periodIndex, "실행 명령");
  addShape(slide, "rect", { left: 72, top: 190, width: 1136, height: 242 }, C.black);
  addText(slide, "$", { left: 112, top: 250, width: 36, height: 40 }, { size: 27, bold: true, color: C.blue });
  addText(slide, period.command, { left: 166, top: 236, width: 980, height: 92 }, { size: 23, bold: true, color: C.white, valign: "middle" });
  addText(slide, "실행 전 확인", { left: 86, top: 488, width: 190, height: 24 }, { size: 14, bold: true, color: C.muted });
  addText(slide, "현재 경로가 repository root인지 · Python 3.12 환경인지 · .env가 출력되지 않는지", { left: 300, top: 478, width: 840, height: 58 }, { size: 20, bold: true, color: C.ink, valign: "middle" });
  addNotes(slide, "명령을 복사하기 전에 실행 경로와 environment를 확인한다.", period.files.map((file) => `local:${file}`));
}

function addExpected(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "완료 여부는 화면이 아니라 결과 계약으로 확인합니다", periodIndex, "예상 결과");
  addText(slide, "STATUS", { left: 80, top: 176, width: 220, height: 26 }, { size: 13, bold: true, color: C.muted });
  addText(slide, "SUCCESS 또는 EXPECTED_FAILURE", { left: 80, top: 220, width: 520, height: 64 }, { size: 30, bold: true, color: C.ink });
  addText(slide, "ARTIFACT", { left: 80, top: 336, width: 220, height: 26 }, { size: 13, bold: true, color: C.muted });
  addText(slide, period.artifact, { left: 80, top: 380, width: 520, height: 64 }, { size: 30, bold: true, color: C.ink });
  addShape(slide, "rect", { left: 668, top: 166, width: 470, height: 330 }, C.gray025, C.faint, 1);
  addText(slide, "사람이 확인할 세 줄", { left: 702, top: 200, width: 400, height: 30 }, { size: 16, bold: true, color: C.muted });
  addText(slide, `1. ${period.normalTest}\n\n2. ${period.boundaryTest}\n\n3. external_write=false`, { left: 702, top: 258, width: 400, height: 196 }, { size: 19, bold: true, color: C.ink });
  addNotes(slide, "실행 성공을 파일·status·boundary 결과로 확인한다.");
}

function addDemoFailure(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "강사는 실패 한 건도 바로 재현하고 복구합니다", periodIndex, "실패 시연");
  addText(slide, "재현", { left: 80, top: 170, width: 180, height: 30 }, { size: 14, bold: true, color: C.muted });
  addText(slide, period.failure, { left: 80, top: 224, width: 500, height: 152 }, { size: 28, bold: true, color: C.ink });
  addShape(slide, "line", { left: 630, top: 174, width: 0, height: 360 }, "none", C.faint, 1);
  addText(slide, "복구", { left: 688, top: 170, width: 180, height: 30 }, { size: 14, bold: true, color: C.muted });
  addText(slide, period.recovery, { left: 688, top: 224, width: 478, height: 152 }, { size: 28, bold: true, color: C.ink });
  addText(slide, `확인: ${period.boundaryTest}`, { left: 160, top: 492, width: 960, height: 64 }, { size: 21, bold: true, color: C.ink, align: "center" });
  addNotes(slide, "정상 화면만 보여주지 않고 대표 실패와 안전한 복구 경로를 이어서 시연한다.");
}

function addLabSetup(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "이제 같은 코드를 각자 실행하고 한 줄만 바꿉니다", periodIndex, "소프트웨어 실습");
  addText(slide, "열 파일", { left: 80, top: 174, width: 150, height: 26 }, { size: 14, bold: true, color: C.muted });
  addText(slide, period.files[3], { left: 260, top: 164, width: 860, height: 50 }, { size: 25, bold: true, color: C.ink });
  addText(slide, "수정 범위", { left: 80, top: 280, width: 150, height: 26 }, { size: 14, bold: true, color: C.muted });
  addText(slide, "notebook의 실습 변수 또는 fixture 한 줄 · src 전체를 복사해 바꾸지 않음", { left: 260, top: 270, width: 860, height: 74 }, { size: 23, bold: true, color: C.ink });
  addText(slide, "완료 기준", { left: 80, top: 410, width: 150, height: 26 }, { size: 14, bold: true, color: C.muted });
  addText(slide, `${period.normalTest}\n${period.artifact} 저장`, { left: 260, top: 400, width: 860, height: 84 }, { size: 23, bold: true, color: C.ink });
  addNotes(slide, "생각 활동이 아니라 직접 IDE·notebook·terminal에서 실행하는 구간임을 분명히 한다.", [`local:${period.files[3]}`]);
}

function addLabStep(period, periodIndex, stepIndex) {
  const slide = deck.slides.add();
  const steps = [
    ["입력과 설정을 확인합니다", `파일: ${period.files[0]}\n변수: 실행 경로·provider·dry-run 여부`],
    ["정상 경로를 실행합니다", `${period.command}\n성공 신호: ${period.normalTest}`],
    ["경계값을 바꿔 실패를 확인합니다", `${period.boundaryTest}\n복구: ${period.recovery}`],
  ];
  const [title, body] = steps[stepIndex];
  addHeader(slide, `STEP ${stepIndex + 1} · ${title}`, periodIndex, "소프트웨어 실습");
  addText(slide, body, { left: 100, top: 200, width: 1080, height: 176 }, { size: 30, bold: true, color: C.ink, valign: "middle", align: "center" });
  addShape(slide, "line", { left: 320, top: 422, width: 640, height: 0 }, "none", C.blue, 3);
  addText(slide, stepIndex === 2 ? `결과에 error_code와 external_write=false가 보이면 완료` : `결과 파일: ${period.artifact}`, { left: 180, top: 466, width: 920, height: 52 }, { size: 20, bold: true, color: C.muted, align: "center" });
  addNotes(slide, `소프트웨어 실습 ${stepIndex + 1}단계를 수강생이 직접 실행한다.`, period.files.map((file) => `local:${file}`));
}

function addTest(period, periodIndex, isBoundary) {
  const slide = deck.slides.add();
  const title = isBoundary ? "가장 중요한 실패 조건을 test로 고정합니다" : "정상 case를 focused test로 확인합니다";
  addHeader(slide, title, periodIndex, "실행 확인");
  addShape(slide, "rect", { left: 72, top: 164, width: 1136, height: 126 }, C.black);
  addText(slide, isBoundary ? "BOUNDARY" : "NORMAL", { left: 104, top: 194, width: 160, height: 24 }, { size: 13, bold: true, color: C.gray300 });
  addText(slide, isBoundary ? period.boundaryTest : period.normalTest, { left: 294, top: 188, width: 850, height: 66 }, { size: 24, bold: true, color: C.white, valign: "middle" });
  addBullets(slide, isBoundary ? [
    "raw traceback 대신 stable error_code가 남는가",
    "외부 쓰기·자동 메일이 false인가",
    "실패가 다음 차시에서 재현 가능한가",
  ] : [
    "입력 fixture와 실행 command가 기록됐는가",
    "결과 schema가 validate되는가",
    "focused test가 실제로 통과했는가",
  ], { left: 96, top: 342, width: 1060 }, { rowHeight: 84, size: 20 });
  addNotes(slide, `${isBoundary ? "실패" : "정상"} case를 실제 test 증거로 확인한다.`, ["local:tests/test_course_services.py"]);
}

function addCareer(period, periodIndex, kind) {
  const slide = deck.slides.add();
  const incumbent = kind === "incumbent";
  addHeader(slide, incumbent ? "재직자는 작은 운영 문제 한 곳에 먼저 적용합니다" : "구직자는 제품 판단과 검증 증거를 함께 보여줍니다", periodIndex, incumbent ? "재직자 적용" : "구직자 포트폴리오");
  addText(slide, period.serviceCase, { left: 90, top: 170, width: 1100, height: 116 }, { size: 31, bold: true, color: C.ink, valign: "middle", align: "center" });
  const bullets = incumbent ? [
    "실제 업무 데이터 대신 합성·비식별 sample로 먼저 실행",
    "현재 수작업 시간과 오류를 baseline으로 기록",
    "사람 승인 전에는 외부 시스템을 바꾸지 않음",
    `${period.artifact}을 운영 검토 자료로 사용`,
  ] : [
    "문제와 사용자 영향을 한 문장으로 설명",
    "정상 demo와 대표 실패 demo를 함께 준비",
    "Codex가 만든 diff와 직접 검토한 test 증거를 구분",
    `${period.artifact}과 README 재현 절차를 제출`,
  ];
  addBullets(slide, bullets, { left: 130, top: 342, width: 1020 }, { rowHeight: 70, size: 19 });
  addNotes(slide, `${incumbent ? "재직자" : "구직자"} 관점에서 같은 기술을 다른 증거로 연결한다.`);
}

function addOperations(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, "서비스로 운영하려면 이 네 가지 질문에 답해야 합니다", periodIndex, "운영 점검");
  const questions = [
    ["품질", `무엇을 ${period.normalTest}로 정의하는가`],
    ["안전", "어디에서 사람 승인과 external_write=false를 확인하는가"],
    ["복구", period.recovery],
    ["관측", `${period.artifact}에서 어떤 status·error_code를 보는가`],
  ];
  questions.forEach(([label, value], index) => {
    const x = 72 + (index % 2) * 568;
    const y = 160 + Math.floor(index / 2) * 218;
    addText(slide, label, { left: x, top: y, width: 120, height: 28 }, { size: 14, bold: true, color: C.muted });
    addShape(slide, "line", { left: x, top: y + 44, width: 516, height: 0 }, "none", C.black, 2);
    addText(slide, value, { left: x, top: y + 72, width: 516, height: 100 }, { size: 22, bold: true, color: C.ink });
  });
  addNotes(slide, "품질·안전·복구·관측을 서비스 운영 질문으로 바꾼다.");
}

function addCheckpoint(period, periodIndex) {
  const slide = deck.slides.add();
  addHeader(slide, `${partNumber(periodIndex)}차시를 마치기 전에 세 가지를 확인합니다`, periodIndex, "차시 마무리");
  addBullets(slide, [
    `설명: ${period.title}이 필요한 이유를 한 문장으로 말할 수 있다.`,
    `실행: ${period.command}`,
    `증거: ${period.artifact}과 정상·실패 test 결과가 남아 있다.`,
  ], { left: 96, top: 178, width: 1060 }, { rowHeight: 122, size: 23 });
  const next = config.periods[periodIndex + 1];
  addText(slide, next ? `다음 차시: ${next.title}` : "17:10-17:40 쉬는 시간 · 17:40-18:00 Q&A·실행 복구", { left: 160, top: 566, width: 960, height: 38 }, { size: 18, bold: true, color: C.ink, align: "center" });
  addNotes(slide, "차시의 설명·실행·증거를 확인하고 다음 입력으로 넘긴다.");
}

async function buildPeriod(period, periodIndex) {
  addCover(period, periodIndex);                        // 1
  if (periodIndex === 0) addTimetable(periodIndex);     // 2
  else addPositionMap(period, periodIndex);             // 2
  addClaim(period, periodIndex);                        // 3
  addOutcome(period, periodIndex);                      // 4
  addTermTable(period, periodIndex);                    // 5
  addInputOutput(period, periodIndex);                  // 6
  addProcess(period, periodIndex);                      // 7
  addContract(period, periodIndex);                     // 8
  addFiles(period, periodIndex);                        // 9
  addConcept(period, periodIndex);                      // 10
  addComparison(period, periodIndex);                   // 11
  addFailure(period, periodIndex);                      // 12
  addRecovery(period, periodIndex);                     // 13
  await addCodexReference(period, periodIndex);         // 14
  addCodexTask(period, periodIndex);                    // 15
  addCodexReview(period, periodIndex);                  // 16
  addDemoSetup(period, periodIndex);                    // 17
  addCommand(period, periodIndex);                      // 18
  addExpected(period, periodIndex);                     // 19
  addDemoFailure(period, periodIndex);                  // 20
  addLabSetup(period, periodIndex);                     // 21
  addLabStep(period, periodIndex, 0);                   // 22
  addLabStep(period, periodIndex, 1);                   // 23
  addLabStep(period, periodIndex, 2);                   // 24
  addTest(period, periodIndex, false);                  // 25
  addTest(period, periodIndex, true);                   // 26
  addCareer(period, periodIndex, "incumbent");         // 27
  addCareer(period, periodIndex, "jobseeker");         // 28
  addOperations(period, periodIndex);                   // 29
  addCheckpoint(period, periodIndex);                   // 30
}

for (const [index, period] of config.periods.entries()) {
  await buildPeriod(period, index);
}

if (deck.slides.items.length !== 240) {
  throw new Error(`Expected 240 slides, got ${deck.slides.items.length}`);
}

await fs.mkdir(path.dirname(outPath), { recursive: true });
const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(outPath);
console.log(JSON.stringify({ day, slides: deck.slides.items.length, outPath }));
