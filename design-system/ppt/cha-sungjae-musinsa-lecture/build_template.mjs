import { Presentation, PresentationFile } from "@oai/artifact-tool";
import { MUSINSA_PPT, MUSINSA_REFERENCE } from "./design-system.mjs";

const OUT = "/Users/sungjae-cha/sungjae-cha/llm-agent-and-workflow-automation/design-system/ppt/cha-sungjae-musinsa-lecture/IPA_MUSINSA_LECTURE_TEMPLATE.pptx";
const T = MUSINSA_PPT;
const C = T.colors;
const deck = Presentation.create({ slideSize: T.slide });

function shape(slide, geometry, position, fill = "none", lineFill = "none", lineWidth = 0) {
  return slide.shapes.add({ geometry, position, fill, line: { style: "solid", fill: lineFill, width: lineWidth } });
}

function text(slide, value, position, options = {}) {
  const box = shape(slide, "textbox", position, options.fill ?? "none", options.line ?? "none", options.lineWidth ?? 0);
  box.text = value;
  box.text.style = {
    fontSize: options.size ?? T.type.body,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    typeface: options.font ?? T.fonts.korean,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    autoFit: options.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.1,
    insets: options.insets ?? { left: 0, right: 0, top: 0, bottom: 0 }
  };
  return box;
}

function notes(slide, role) {
  slide.speakerNotes.textFrame.setText(`${role}\n\n[Sources]\n- ${MUSINSA_REFERENCE}\n[/Sources]`);
  slide.speakerNotes.setVisible(true);
}

function footer(slide, index, label = "LECTURE TEMPLATE") {
  shape(slide, "line", { left: 64, top: 674, width: 1152, height: 0 }, "none", C.gray200, 1);
  text(slide, "CHA SUNGJAE · PPT DESIGN SYSTEM", { left: 64, top: 684, width: 430, height: 18 }, { size: 10, bold: true, color: C.gray700 });
  text(slide, label, { left: 496, top: 684, width: 340, height: 18 }, { size: 10, bold: true, color: C.blue, align: "center" });
  text(slide, String(index).padStart(2, "0"), { left: 1156, top: 684, width: 60, height: 18 }, { size: 10, bold: true, color: C.gray700, align: "right" });
}

function header(slide, index, kicker, title) {
  slide.background.fill = C.white;
  text(slide, kicker, { left: 64, top: 38, width: 400, height: 20 }, { size: 11, bold: true, color: C.blue });
  text(slide, title, { left: 64, top: 78, width: 1152, height: 64 }, { size: T.type.slideTitle, bold: true, color: C.ink, valign: "top" });
  footer(slide, index);
}

{
  const slide = deck.slides.add();
  slide.background.fill = C.black;
  shape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, C.blue);
  text(slide, "IPA · 40H PROJECT BASED LEARNING", { left: 84, top: 68, width: 720, height: 26 }, { size: 13, bold: true, color: C.white });
  text(slide, "LLM Agent &\n업무자동화", { left: 84, top: 162, width: 1080, height: 178 }, { size: 62, bold: true, color: C.white, lineSpacing: 0.96 });
  shape(slide, "line", { left: 84, top: 420, width: 1092, height: 0 }, "none", C.blue, 3);
  text(slide, "차성재 · 무신사 Agentic AI Side PM", { left: 84, top: 544, width: 720, height: 34 }, { size: 22, bold: true, color: C.white });
  text(slide, "COVER · BLACK / WHITE / BLUE", { left: 858, top: 548, width: 318, height: 26 }, { size: 12, bold: true, color: C.gray300, align: "right" });
  notes(slide, "Layout 01 · Minimal cover. Use one title, one rule, one identity line.");
}

{
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  text(slide, "02", { left: 72, top: 68, width: 120, height: 72 }, { size: 48, bold: true, color: C.blue });
  text(slide, "SECTION TITLE", { left: 72, top: 214, width: 1080, height: 92 }, { size: 54, bold: true, color: C.white });
  text(slide, "이 시간에 학습자가 손에 남길 결과를 한 문장으로 씁니다.", { left: 76, top: 356, width: 980, height: 70 }, { size: 25, color: C.gray200 });
  shape(slide, "line", { left: 72, top: 594, width: 1128, height: 0 }, "none", C.blue, 3);
  notes(slide, "Layout 02 · Section divider. Navy is allowed only as a secondary dark field.");
}

{
  const slide = deck.slides.add();
  header(slide, 3, "BEGINNER DEFINITION", "Agent — 목표를 받아 도구를 선택하는 실행 구조");
  text(slide, "한 줄 뜻", { left: 64, top: 184, width: 180, height: 28 }, { size: 16, bold: true, color: C.blue });
  text(slide, "모델이 답만 만드는 것이 아니라, 상태를 보고 필요한 행동을 고르고 결과를 확인하는 구조입니다.", { left: 64, top: 226, width: 1080, height: 92 }, { size: 30, bold: true });
  shape(slide, "line", { left: 64, top: 356, width: 1152, height: 0 }, "none", C.black, 2);
  text(slide, "왜 필요한가", { left: 64, top: 392, width: 200, height: 28 }, { size: 16, bold: true, color: C.gray700 });
  text(slide, "업무 자동화는 답변보다 파일 읽기, 승인, 기록, 실패 복구가 더 중요하기 때문입니다.", { left: 64, top: 434, width: 520, height: 104 }, { size: 22 });
  text(slide, "예시", { left: 660, top: 392, width: 120, height: 28 }, { size: 16, bold: true, color: C.gray700 });
  text(slide, "회의록을 읽고 → Action Item을 구조화하고 → 사람이 승인하면 → 문서에 기록", { left: 660, top: 434, width: 500, height: 104 }, { size: 22, bold: true });
  notes(slide, "Layout 03 · Definition before first use of an unfamiliar term.");
}

{
  const slide = deck.slides.add();
  header(slide, 4, "CORE IDEA", "좋은 Agent의 첫 기준은 정확도가 아니라 통제 가능성입니다");
  shape(slide, "rect", { left: 64, top: 184, width: 10, height: 340 }, C.black);
  text(slide, "실패해도 안전하게 멈추고, 사람이 확인한 뒤, 같은 지점에서 다시 시작할 수 있어야 합니다.", { left: 112, top: 196, width: 1010, height: 180 }, { size: 40, bold: true, valign: "middle" });
  text(slide, "허용 도구 · 입력 Schema · Timeout · Retry · Human Approval · Trace", { left: 116, top: 430, width: 1010, height: 70 }, { size: 23, color: C.gray700 });
  notes(slide, "Layout 04 · One claim and one short support line.");
}

{
  const slide = deck.slides.add();
  header(slide, 5, "KEY POINTS", "처음에는 네 가지만 구분하면 됩니다");
  const rows = [
    ["INPUT", "Agent가 받는 원문·파일·요청"],
    ["ACTION", "모델이나 도구가 수행하는 한 단계"],
    ["OUTPUT", "구조화된 결과와 상태"],
    ["EVIDENCE", "결과가 맞는지 확인할 근거"]
  ];
  rows.forEach((row, index) => {
    const y = 182 + index * 94;
    shape(slide, "line", { left: 64, top: y + 72, width: 1152, height: 0 }, "none", C.gray200, 1);
    text(slide, row[0], { left: 64, top: y, width: 180, height: 54 }, { size: 16, bold: true, color: index === 3 ? C.blue : C.black, valign: "middle" });
    text(slide, row[1], { left: 260, top: y, width: 880, height: 54 }, { size: 25, bold: true, valign: "middle" });
  });
  notes(slide, "Layout 05 · Four editorial rows instead of cards.");
}

{
  const slide = deck.slides.add();
  header(slide, 6, "WORKFLOW", "작업은 네 단계로 작게 쪼갭니다");
  const steps = [["01", "READ", "원문 확인"], ["02", "PLAN", "도구 선택"], ["03", "EXECUTE", "한 번 실행"], ["04", "VERIFY", "증거 확인"]];
  steps.forEach((step, index) => {
    const x = 64 + index * 288;
    shape(slide, "line", { left: x, top: 238, width: 252, height: 0 }, "none", index === 3 ? C.blue : C.black, 3);
    text(slide, step[0], { left: x, top: 184, width: 60, height: 32 }, { size: 15, bold: true, color: C.blue });
    text(slide, step[1], { left: x, top: 274, width: 244, height: 42 }, { size: 26, bold: true });
    text(slide, step[2], { left: x, top: 334, width: 244, height: 74 }, { size: 19, color: C.gray700 });
  });
  text(slide, "다음 단계로 넘어가기 전에 성공 신호 한 줄을 확인합니다.", { left: 64, top: 516, width: 1120, height: 52 }, { size: 24, bold: true });
  notes(slide, "Layout 06 · Flat horizontal process with rules.");
}

{
  const slide = deck.slides.add();
  header(slide, 7, "TUTORIAL MAP", "설치 화면부터 성공 화면까지 같은 순서로 따라갑니다");
  const steps = ["공식 다운로드 화면", "설치·권한 확인", "VS Code에서 Interpreter 선택", "명령 실행", "성공 문구 저장"];
  steps.forEach((step, index) => {
    const y = 176 + index * 78;
    text(slide, String(index + 1).padStart(2, "0"), { left: 64, top: y, width: 72, height: 48 }, { size: 18, bold: true, color: index === 4 ? C.blue : C.black, valign: "middle" });
    shape(slide, "line", { left: 144, top: y + 24, width: 74, height: 0 }, "none", C.gray300, 1);
    text(slide, step, { left: 246, top: y, width: 620, height: 48 }, { size: 24, bold: true, valign: "middle" });
    text(slide, index === 4 ? "완료 증거" : "다음 화면", { left: 1000, top: y, width: 164, height: 48 }, { size: 15, bold: true, color: index === 4 ? C.blue : C.gray500, align: "right", valign: "middle" });
  });
  notes(slide, "Layout 07 · Tutorial roadmap before actual screenshots.");
}

{
  const slide = deck.slides.add();
  header(slide, 8, "STEP 03 / ACTUAL SCREEN", "VS Code에서 프로젝트의 Python을 선택합니다");
  text(slide, "화면에서 찾을 것", { left: 64, top: 176, width: 320, height: 28 }, { size: 16, bold: true, color: C.blue });
  text(slide, "1. 상태 표시줄의 Python\n2. Select Interpreter\n3. .venv 경로\n4. 새 Terminal 재시작", { left: 64, top: 226, width: 364, height: 250 }, { size: 22, bold: true, lineSpacing: 1.45 });
  shape(slide, "rect", { left: 470, top: 166, width: 746, height: 438 }, C.gray050, C.gray200, 1);
  text(slide, "ACTUAL SCREENSHOT AREA\n16:9 OR WIDE CROP\nNO COLOR OVERLAY", { left: 520, top: 314, width: 646, height: 110 }, { size: 26, bold: true, color: C.gray500, align: "center", valign: "middle" });
  notes(slide, "Layout 08 · Untinted screenshot with step number and exact visual targets.");
}

{
  const slide = deck.slides.add();
  header(slide, 9, "LIVE CODE", "명령은 복사보다 성공 신호를 함께 읽어야 합니다");
  text(slide, "읽는 순서", { left: 64, top: 176, width: 320, height: 28 }, { size: 16, bold: true, color: C.blue });
  text(slide, "① 실행 위치\n② 명령\n③ 예상 출력\n④ 실패 시 복구", { left: 64, top: 226, width: 350, height: 220 }, { size: 23, bold: true, lineSpacing: 1.45 });
  shape(slide, "rect", { left: 470, top: 166, width: 746, height: 438 }, C.black, C.black, 1);
  shape(slide, "rect", { left: 470, top: 166, width: 6, height: 438 }, C.blue);
  text(slide, "python3 -m pytest -q\n# ......... [100%]\n# 9 passed in 0.02s", { left: 508, top: 214, width: 650, height: 210 }, { size: 19, bold: false, color: C.white, font: T.fonts.mono, lineSpacing: 1.3 });
  notes(slide, "Layout 09 · Black code field with a single blue rule.");
}

{
  const slide = deck.slides.add();
  header(slide, 10, "FOLLOW ALONG", "실습은 단계와 완료 증거가 같은 화면에 있어야 합니다");
  text(slide, "08 MIN", { left: 64, top: 178, width: 180, height: 54 }, { size: 34, bold: true });
  shape(slide, "line", { left: 64, top: 250, width: 180, height: 0 }, "none", C.blue, 3);
  const steps = ["새 Terminal을 연다", "명령을 한 줄씩 실행한다", "첫 오류만 읽는다", "성공 화면을 저장한다"];
  steps.forEach((step, index) => {
    const y = 178 + index * 80;
    text(slide, String(index + 1), { left: 320, top: y, width: 44, height: 44 }, { size: 19, bold: true, color: C.blue, valign: "middle" });
    text(slide, step, { left: 390, top: y, width: 730, height: 44 }, { size: 24, bold: true, valign: "middle" });
    shape(slide, "line", { left: 390, top: y + 57, width: 730, height: 0 }, "none", C.gray200, 1);
  });
  shape(slide, "rect", { left: 320, top: 522, width: 836, height: 64 }, C.blueSoft);
  text(slide, "완료 증거  |  pytest 9 passed 화면", { left: 344, top: 538, width: 788, height: 34 }, { size: 19, bold: true, color: C.navy });
  notes(slide, "Layout 10 · Exercise with a visible artifact and recovery route.");
}

{
  const slide = deck.slides.add();
  header(slide, 11, "FAILURE / RECOVERY", "오류는 숨기지 않고 분류한 뒤 다음 행동을 정합니다");
  text(slide, "실패 패턴", { left: 64, top: 174, width: 440, height: 40 }, { size: 24, bold: true, color: C.black });
  text(slide, "복구 원칙", { left: 680, top: 174, width: 440, height: 40 }, { size: 24, bold: true, color: C.blue });
  shape(slide, "line", { left: 620, top: 174, width: 0, height: 390 }, "none", C.gray200, 1);
  text(slide, "설치를 계속 반복\n오류 전체를 한꺼번에 읽음\n같은 명령을 무제한 재시도\n성공 여부를 느낌으로 판단", { left: 64, top: 246, width: 480, height: 260 }, { size: 22, bold: true, lineSpacing: 1.55 });
  text(slide, "첫 오류 한 줄을 분류\nOS·버전·경로 확인\n최대 재시도 횟수 고정\n파일·테스트로 완료 확인", { left: 680, top: 246, width: 480, height: 260 }, { size: 22, bold: true, lineSpacing: 1.55 });
  notes(slide, "Layout 11 · Failure is black; the recovery decision is blue.");
}

{
  const slide = deck.slides.add();
  header(slide, 12, "CHECKPOINT", "다음 단계로 넘어가기 전에 세 가지를 설명합니다");
  const qs = ["방금 실행한 입력과 출력은 무엇인가?", "성공을 증명하는 화면·파일·테스트는 무엇인가?", "같은 오류가 나면 어디에서 다시 시작하는가?"];
  qs.forEach((q, index) => {
    const y = 190 + index * 126;
    text(slide, String(index + 1).padStart(2, "0"), { left: 64, top: y, width: 70, height: 60 }, { size: 21, bold: true, color: index === 2 ? C.blue : C.black, valign: "middle" });
    text(slide, q, { left: 170, top: y, width: 930, height: 60 }, { size: 27, bold: true, valign: "middle" });
    shape(slide, "line", { left: 170, top: y + 76, width: 930, height: 0 }, "none", C.gray200, 1);
  });
  notes(slide, "Layout 12 · Checkpoint with three explanation prompts.");
}

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(OUT);
console.log(`Wrote ${deck.slides.items.length} template slides to ${OUT}`);
