export const MUSINSA_PPT = Object.freeze({
  slide: Object.freeze({ width: 1280, height: 720 }),
  colors: Object.freeze({
    black: "#000000",
    ink: "#191919",
    gray900: "#2D2D2D",
    gray700: "#555555",
    gray500: "#888888",
    gray300: "#C7C7C7",
    gray200: "#E0E0E0",
    gray100: "#F0F0F0",
    gray050: "#F5F5F5",
    gray025: "#FAFAFA",
    white: "#FFFFFF",
    navy: "#0B1F3A",
    blue: "#2563EB",
    blueSoft: "#E0F0FE"
  }),
  fonts: Object.freeze({
    korean: "Apple SD Gothic Neo",
    english: "Helvetica Neue",
    mono: "Menlo"
  }),
  type: Object.freeze({
    deckTitle: 52,
    sectionTitle: 46,
    slideTitle: 32,
    lead: 25,
    body: 19,
    caption: 11,
    minimum: 16
  }),
  space: Object.freeze({
    base: 4,
    left: 64,
    right: 64,
    top: 40,
    bottom: 42,
    columnGap: 24,
    sectionGap: 32
  }),
  shape: Object.freeze({ radius: 0, radiusMax: 4, border: 1, rule: 2 })
});

export const MUSINSA_REFERENCE = "https://www.oppadu.com/tools/design-systems-site/brand/musinsa.html";

export function makeCoursePalette() {
  const p = MUSINSA_PPT.colors;
  return {
    black: p.black,
    ink: p.ink,
    muted: p.gray700,
    faint: p.gray200,
    gray300: p.gray300,
    paper: p.white,
    white: p.white,
    navy: p.navy,
    blue: p.blue,
    blueSoft: p.blueSoft,
    cyan: p.blue,
    green: p.blue,
    greenSoft: p.blueSoft,
    amber: p.navy,
    amberSoft: p.gray050,
    red: p.black,
    redSoft: p.gray050,
    purple: p.navy,
    purpleSoft: p.gray050
  };
}
