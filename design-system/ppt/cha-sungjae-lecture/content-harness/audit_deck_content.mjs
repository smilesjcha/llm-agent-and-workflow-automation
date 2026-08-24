import fs from "node:fs/promises";
import path from "node:path";

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

const inspectPath = arg("--inspect");
const mapPath = arg("--map");
const outDir = arg("--out-dir", ".build/content-audit");

if (!inspectPath || !mapPath) {
  throw new Error("Usage: node audit_deck_content.mjs --inspect <pptx.inspect.ndjson> --map <message-map.json> --out-dir <dir>");
}

const normalize = (value) => String(value ?? "")
  .normalize("NFKC")
  .replace(/[“”‘’'\"`]/g, "")
  .replace(/[·•|→←↔:：,，.。!?！？()\[\]{}<>/\\\-–—_]+/g, " ")
  .replace(/\s+/g, " ")
  .trim()
  .toLowerCase();

function charNgrams(text, n = 3) {
  const value = normalize(text).replace(/\s+/g, "");
  const grams = new Set();
  for (let i = 0; i <= value.length - n; i += 1) grams.add(value.slice(i, i + n));
  return grams;
}

function diceSimilarity(a, b) {
  const left = charNgrams(a);
  const right = charNgrams(b);
  if (!left.size || !right.size) return 0;
  let overlap = 0;
  for (const gram of left) if (right.has(gram)) overlap += 1;
  return (2 * overlap) / (left.size + right.size);
}

const [raw, messageMap] = await Promise.all([
  fs.readFile(inspectPath, "utf8"),
  fs.readFile(mapPath, "utf8").then(JSON.parse),
]);

const records = raw.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
const slides = new Map();
for (const record of records) {
  if (!record.slide) continue;
  if (!slides.has(record.slide)) slides.set(record.slide, { slide: record.slide, title: "", textboxes: [] });
  const target = slides.get(record.slide);
  if (record.kind === "slide") target.inspectTitle = record.title ?? "";
  if (record.kind === "textbox") target.textboxes.push({ text: record.text ?? "", bbox: record.bbox ?? [] });
}

function chooseHeadline(slide) {
  const candidates = slide.textboxes.filter(({ text, bbox }) => {
    const [left = 0, top = 0, width = 0, height = 0] = bbox;
    if (!text.trim() || width < 700 || height < 38) return false;
    if (top < 70 || top > 240 || left > 140) return false;
    if (/CHA SUNGJAE|LLM AGENT & 업무자동화/.test(text)) return false;
    return true;
  });
  candidates.sort((a, b) => a.bbox[1] - b.bbox[1] || b.bbox[2] - a.bbox[2]);
  return candidates[0]?.text.replace(/\s+/g, " ").trim() || slide.inspectTitle || `Slide ${slide.slide}`;
}

for (const slide of slides.values()) slide.headline = chooseHeadline(slide);

const exactGroups = new Map();
for (const slide of slides.values()) {
  const key = normalize(slide.headline);
  if (!exactGroups.has(key)) exactGroups.set(key, []);
  exactGroups.get(key).push({ slide: slide.slide, headline: slide.headline });
}
const allowedExact = new Set((messageMap.audit.allowedExactHeadlines ?? []).map(normalize));
const exactHeadlineDuplicates = [...exactGroups.entries()]
  .filter(([key, items]) => key && items.length > 1 && !allowedExact.has(key))
  .map(([, items]) => items);

const nearHeadlineDuplicates = [];
const slideList = [...slides.values()].sort((a, b) => a.slide - b.slide);
const threshold = messageMap.audit.nearHeadlineThreshold ?? 0.8;
for (let i = 0; i < slideList.length; i += 1) {
  for (let j = i + 1; j < slideList.length; j += 1) {
    const a = slideList[i];
    const b = slideList[j];
    if (normalize(a.headline) === normalize(b.headline)) continue;
    if (normalize(a.headline).length < 10 || normalize(b.headline).length < 10) continue;
    const lengthRatio = Math.min(normalize(a.headline).length, normalize(b.headline).length) / Math.max(normalize(a.headline).length, normalize(b.headline).length);
    if (lengthRatio < 0.65) continue;
    const similarity = diceSimilarity(a.headline, b.headline);
    if (similarity >= threshold) {
      nearHeadlineDuplicates.push({ slides: [a.slide, b.slide], headlines: [a.headline, b.headline], similarity: Number(similarity.toFixed(3)) });
    }
  }
}

const allowedLines = new Set((messageMap.audit.allowedRepeatedLines ?? []).map(normalize));
const allowedPatterns = (messageMap.audit.allowedRepeatedLinePatterns ?? []).map((value) => new RegExp(value, "i"));
const repeatedLineIndex = new Map();
for (const slide of slideList) {
  const seenOnSlide = new Set();
  for (const box of slide.textboxes) {
    const [left = 0, top = 0] = box.bbox;
    if (top < 145 || top > 660) continue;
    for (const rawLine of box.text.split(/\r?\n/)) {
      const line = rawLine.replace(/\s+/g, " ").trim();
      const key = normalize(line);
      if (key.length < 18 || allowedLines.has(key) || allowedPatterns.some((pattern) => pattern.test(line))) continue;
      if (/CHA SUNGJAE|LLM AGENT & 업무자동화/.test(line)) continue;
      if (left >= 500 && /[:={}\[\]();]|\b(def|return|if|for|python|pytest|git|pip|raise|from|import)\b/i.test(line)) continue;
      if (seenOnSlide.has(key)) continue;
      seenOnSlide.add(key);
      if (!repeatedLineIndex.has(key)) repeatedLineIndex.set(key, { line, slides: [] });
      repeatedLineIndex.get(key).slides.push(slide.slide);
    }
  }
}
const repeatedNarrativeLines = [...repeatedLineIndex.values()]
  .filter((item) => item.slides.length > 1)
  .sort((a, b) => b.slides.length - a.slides.length || a.slides[0] - b.slides[0]);

const summaryPatterns = (messageMap.audit.summaryHeadlinePatterns ?? []).map((value) => new RegExp(value, "i"));
const finalSlides = new Set(messageMap.deck.finalSynthesisSlides ?? []);
const summaryLikeOutsideFinal = slideList
  .filter((slide) => !finalSlides.has(slide.slide) && summaryPatterns.some((pattern) => pattern.test(slide.headline)))
  .map((slide) => ({ slide: slide.slide, headline: slide.headline }));

function blockForSlide(slideNo) {
  return messageMap.blocks.find((block) => slideNo >= block.range[0] && slideNo <= block.range[1]);
}

const ownershipMentions = {};
for (const [keyword, allowedBlocks] of Object.entries(messageMap.audit.ownershipKeywords ?? {})) {
  const mentions = [];
  for (const slide of slideList) {
    const fullText = slide.textboxes.map((box) => box.text).join("\n");
    if (!fullText.toLowerCase().includes(keyword.toLowerCase())) continue;
    const block = blockForSlide(slide.slide);
    mentions.push({ slide: slide.slide, block: block?.id ?? "OUTSIDE", allowed: allowedBlocks.includes(block?.id) });
  }
  ownershipMentions[keyword] = mentions;
}

const report = {
  generatedAt: new Date().toISOString(),
  inspectPath: path.resolve(inspectPath),
  messageMap: path.resolve(mapPath),
  slideCount: slides.size,
  gates: {
    exactHeadlineDuplicates: exactHeadlineDuplicates.length === 0,
    repeatedNarrativeLines: repeatedNarrativeLines.length === 0,
    summaryOnlyAtFinal: summaryLikeOutsideFinal.length === 0,
  },
  counts: {
    exactHeadlineDuplicateGroups: exactHeadlineDuplicates.length,
    nearHeadlineDuplicatePairs: nearHeadlineDuplicates.length,
    repeatedNarrativeLines: repeatedNarrativeLines.length,
    summaryLikeOutsideFinal: summaryLikeOutsideFinal.length,
  },
  exactHeadlineDuplicates,
  nearHeadlineDuplicates,
  repeatedNarrativeLines,
  summaryLikeOutsideFinal,
  ownershipMentions,
  headlines: slideList.map(({ slide, headline }) => ({ slide, headline })),
};

const lines = [
  `CONTENT AUDIT · ${path.basename(inspectPath)}`,
  `slides: ${report.slideCount}`,
  `exact headline duplicate groups: ${report.counts.exactHeadlineDuplicateGroups}`,
  `near headline duplicate pairs: ${report.counts.nearHeadlineDuplicatePairs}`,
  `repeated narrative lines: ${report.counts.repeatedNarrativeLines}`,
  `summary-like slides outside final synthesis: ${report.counts.summaryLikeOutsideFinal}`,
  "",
  "[EXACT HEADLINE DUPLICATES]",
  ...(exactHeadlineDuplicates.length ? exactHeadlineDuplicates.map((group) => group.map((item) => `${item.slide}:${item.headline}`).join(" | ")) : ["none"]),
  "",
  "[NEAR HEADLINE DUPLICATES]",
  ...(nearHeadlineDuplicates.length ? nearHeadlineDuplicates.map((item) => `${item.slides.join("/")} · ${item.similarity} · ${item.headlines.join(" <> ")}`) : ["none"]),
  "",
  "[REPEATED NARRATIVE LINES]",
  ...(repeatedNarrativeLines.length ? repeatedNarrativeLines.map((item) => `${item.slides.join(",")} · ${item.line}`) : ["none"]),
  "",
  "[SUMMARY-LIKE OUTSIDE FINAL]",
  ...(summaryLikeOutsideFinal.length ? summaryLikeOutsideFinal.map((item) => `${item.slide} · ${item.headline}`) : ["none"]),
];

await fs.mkdir(outDir, { recursive: true });
await Promise.all([
  fs.writeFile(path.join(outDir, "content-audit.json"), JSON.stringify(report, null, 2) + "\n"),
  fs.writeFile(path.join(outDir, "content-audit.txt"), lines.join("\n") + "\n"),
]);

console.log(lines.slice(0, 6).join("\n"));
if (report.slideCount !== messageMap.deck.slideCount) process.exitCode = 2;
