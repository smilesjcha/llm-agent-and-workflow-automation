// Content ordering and teaching-time checks do not require a slide runtime.
export function insertLessonAdditions(lessons, groups) {
  for (const {period, after, slides} of groups) {
    const lesson = lessons[period];
    if (!lesson || !Array.isArray(slides) || slides.length === 0) throw Error('INVALID_DAY4_ADDITION');
    const anchor = lesson.findIndex(slide => slide.title === after);
    if (anchor < 0) throw Error(`DAY4_ANCHOR_MISSING: ${period + 1} ${after}`);
    const names = new Set(lessons.flat().map(slide => slide.title));
    for (const slide of slides) {
      if (names.has(slide.title)) throw Error(`DAY4_DUPLICATE_TITLE: ${slide.title}`);
      names.add(slide.title);
    }
    lesson.splice(anchor + 1, 0, ...slides.map(slide => ({...slide, expanded: true})));
  }
}

function allocate(items, minutes, phase) {
  const eligible = items.map((d, i) => ({d, i})).filter(x => !x.d.reference && x.d.phase === phase);
  const result = new Map();
  if (!eligible.length && minutes) throw Error(`MISSING_TIMING_PHASE: ${phase}`);
  eligible.forEach(x => result.set(x.i, .5));
  let remain = minutes - .5 * eligible.length;
  if (remain < 0) throw Error(`TOO_MANY_SLIDES_FOR_TIMING: ${phase}`);
  const weights = {task: 6, prompt: 4, code: 2, image: 2};
  const order = [...eligible].sort((a, b) => (weights[b.d.type] ?? 1) - (weights[a.d.type] ?? 1));
  let i = 0;
  while (remain > 0) {
    const index = order[i++ % order.length].i;
    result.set(index, result.get(index) + .5);
    remain -= .5;
  }
  return result;
}

export function buildDay4Plan(opening, lessons, periods) {
  if (opening.length !== 7 || lessons.length !== 8 || periods.length !== 8) throw Error('DAY4_STRUCTURE_CHANGED');
  const plan = [], ranges = [];
  opening.forEach((d, i) => plan.push({d, p: null, minutes: [.5, .5, 1, 1, 1, .5, .5][i]}));
  lessons.forEach((items, p) => {
    const start = plan.length + 1;
    plan.push({d: {type: 'section', title: periods[p].title}, p, minutes: .5});
    // Opening five minutes belong to period 1, not an additional lecture slot.
    const budgets = {theory: periods[p].theory - .5 - (p === 0 ? 3 : 0),
      demo: periods[p].demo - (p === 0 ? 2 : 0), lab: periods[p].lab, check: periods[p].check};
    const times = {};
    for (const [phase, minutes] of Object.entries(budgets)) {
      for (const [index, value] of allocate(items, minutes, phase)) times[index] = value;
    }
    items.forEach((d, i) => plan.push({d, p, minutes: times[i] ?? 0}));
    ranges.push([start, plan.length]);
    if (p === 2) plan.push({d: {type: 'break', title: '쉬는 시간 · 점심시간', label: '오전 수업 종료',
      time: '11:30–13:00', body: '쉬는 시간 11:30–12:00\n점심시간 12:00–13:00'}, p, minutes: 0});
    if (p === 4) plan.push({d: {type: 'break', title: '쉬는 시간', label: '4·5차시 수업 종료',
      time: '14:40–15:00', body: '파일 저장 · 15시 수업 시작'}, p, minutes: 0});
  });
  plan.push({d: {type: 'break', title: '쉬는 시간 · Q&A', label: '4주차 수업 종료',
    time: '17:30–18:00', body: '질문 · 실행 오류 복구 · 다음 주 개인 과제'}, p: 7, minutes: 0});
  const total = plan.reduce((sum, item) => sum + item.minutes, 0);
  if (total !== 400) throw Error(`TIMING_NOT_400: ${total}`);
  for (let p = 0; p < 8; p++) {
    const minutes = plan.filter(item => (item.p ?? 0) === p).reduce((sum, item) => sum + item.minutes, 0);
    if (minutes !== 50) throw Error(`PERIOD_NOT_50: ${p + 1}`);
  }
  return {plan, ranges, total};
}
