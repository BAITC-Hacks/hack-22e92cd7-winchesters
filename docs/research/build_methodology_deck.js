/**
 * "Their methodology vs our approach" deck for the call with inVision U.
 *
 *   NODE_PATH=<scratchpad>/node_modules node docs/research/build_methodology_deck.js
 *
 * Slides in Russian for the client. Speaker notes in English carry the argument
 * and the caveats, so whoever presents knows which claims are solid and which
 * are ours to defend.
 *
 * Scope: Stage 1 only. The item bank with its scoring, the exact competency
 * weights, the cut-off thresholds and the anonymized history all arrive at the
 * implementation stage, so nothing here assumes them.
 */

const pptxgen = require("pptxgenjs");

const INK = "141414";
const PAPER = "FFFFFF";
const SURFACE = "F1F1EE";
const LIME = "C1F11D";
const MUTED = "6E6E68";
const RUST = "A8412F";
const OLIVE = "5C7A1E";

const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Winchesters";
pres.title = "Методология inVision U и наш подход";

function slideTitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: 0.62, y: opts.y || 0.42, w: 12.1, h: 0.75,
    fontFace: HEAD, fontSize: opts.fontSize || 30, bold: true,
    color: opts.color || INK, margin: 0, isTextBox: true,
  });
}

function eyebrow(slide, text, color) {
  slide.addText(text, {
    x: 0.62, y: 0.17, w: 12.1, h: 0.28,
    fontFace: BODY, fontSize: 10.5, bold: true, color: color || MUTED,
    charSpacing: 1.6, margin: 0, isTextBox: true,
  });
}

// ── 1. Title ──────────────────────────────────────────────────────

const s1 = pres.addSlide();
s1.background = { color: INK };
s1.addText("СРАВНЕНИЕ ПОДХОДОВ · ПЕРВЫЙ ЭТАП", {
  x: 0.9, y: 1.45, w: 11.5, h: 0.4,
  fontFace: BODY, fontSize: 13, color: LIME, charSpacing: 3, margin: 0, isTextBox: true,
});
s1.addText("Ваша методология\nи наш подход", {
  x: 0.9, y: 1.95, w: 11.5, h: 1.9,
  fontFace: HEAD, fontSize: 44, bold: true, color: PAPER, lineSpacing: 50, margin: 0, isTextBox: true,
});
s1.addText("Мы не заменяем ваши инструменты. Мы нашли одно место, где их не хватает.", {
  x: 0.9, y: 4.0, w: 11, h: 0.5,
  fontFace: BODY, fontSize: 17, color: "C9C9C4", margin: 0, isTextBox: true,
});
s1.addShape(pres.ShapeType.line, { x: 0.9, y: 4.85, w: 2.2, h: 0, line: { color: LIME, width: 2 } });
s1.addText("Команда Winchesters · разговор до Demo Day", {
  x: 0.9, y: 5.15, w: 8, h: 0.4,
  fontFace: BODY, fontSize: 14, color: "9A9A94", margin: 0, isTextBox: true,
});
s1.addNotes(
  "Frame from the start: this is not a pitch that our thing is better than their thing. Their two " +
  "instruments are well built and we are not proposing to replace either.\n\n" +
  "The whole deck argues one narrow claim: every instrument they have asks the candidate to report on " +
  "themselves, and none of them watches the candidate do anything. That gap is the only place a live " +
  "exercise earns its place.\n\n" +
  "Everything here is Stage-1 scoped. The 95-item bank with its scoring, the competency weights, the " +
  "cut-offs and the anonymized history are closed until implementation, and nothing in this deck assumes " +
  "them."
);

// ── 2. Their three instruments ────────────────────────────────────

const s2 = pres.addSlide();
s2.background = { color: PAPER };
eyebrow(s2, "КАК МЫ ЭТО ПРОЧИТАЛИ");
slideTitle(s2, "На чём стоит ваша оценка кандидата");

const pillars = [
  ["01", "Модель компетенций KFLA", "Ценности разложены в 3–6 поведенческих индикаторов, каждый смэппирован на компетенции Lominger. Принцип: «оценивается наблюдаемое поведение, а не самоописание»."],
  ["02", "Ипсативный forced-choice тест", "Блок из 4 утверждений, выровненных по социальной желательности. Кандидат выбирает «больше похоже на меня» и «меньше похоже на меня». IRT."],
  ["03", "Интервью по модели ATOLA", "Единая структура и единая шкала для всех кандидатов. Уровни разнесены по поведенчески якоренным шкалам BARS."],
];
pillars.forEach((p, i) => {
  const x = 0.62 + i * 4.09;
  s2.addShape(pres.ShapeType.roundRect, {
    x, y: 1.5, w: 3.84, h: 3.5, rectRadius: 0.08,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  s2.addText(p[0], {
    x: x + 0.3, y: 1.75, w: 1.2, h: 0.45,
    fontFace: HEAD, fontSize: 24, bold: true, color: LIME, margin: 0, isTextBox: true,
  });
  s2.addText(p[1], {
    x: x + 0.3, y: 2.25, w: 3.25, h: 0.75,
    fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  s2.addText(p[2], {
    x: x + 0.3, y: 3.05, w: 3.25, h: 1.75, valign: "top",
    fontFace: BODY, fontSize: 12.5, color: "44443F", margin: 0, isTextBox: true,
  });
});

s2.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 5.25, w: 12.1, h: 1.1, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});
s2.addText(
  "Девять компетенций. Три уровня проявления. Purpose-driven и Wounded leadership вы сами называете " +
  "самыми сложными для автоматизации и самыми ценными для отбора.",
  {
    x: 1.0, y: 5.5, w: 11.3, h: 0.65,
    fontFace: BODY, fontSize: 14.5, color: "C9C9C4", margin: 0, isTextBox: true,
  },
);
s2.addNotes(
  "Read this slide out loud almost verbatim. It is their own deck, summarised back to them, and it earns " +
  "the right to say something critical two slides later.\n\n" +
  "The quoted line on card 01 matters: 'оценивается наблюдаемое поведение, а не самоописание' is their " +
  "stated principle, and it is the standard the next slides measure everything against, including our " +
  "own work."
);

// ── 3. Coverage table ─────────────────────────────────────────────

const s3 = pres.addSlide();
s3.background = { color: PAPER };
eyebrow(s3, "ЧЕСТНАЯ КАРТА ПОКРЫТИЯ");
slideTitle(s3, "Кто что сейчас измеряет");

const YES = { text: "да", options: { color: OLIVE, bold: true, align: "center" } };
const NO = { text: "—", options: { color: "B4B4AE", align: "center" } };
const PART = (t) => ({ text: t, options: { color: RUST, align: "center" } });

const head = ["Компетенция", "Ваши тест\nи интервью", "Наш ledger\n(эссе, презентация)", "Feynman\nсейчас", "Сценарий\n(предложение)"];
const body = [
  ["1. Мотивация на университет", YES, YES, NO, NO],
  ["2. Мотивация на специальность", YES, YES, NO, NO],
  ["3. Лидерские способности", YES, YES, NO, YES],
  ["4. Работа в команде", YES, YES, PART("слабо"), YES],
  ["5. Ценности", YES, YES, NO, YES],
  ["6. Предыдущий реальный опыт", YES, YES, NO, PART("teach-back")],
  ["7. Интеллект", YES, YES, PART("слабо"), YES],
  ["8. Purpose-driven leadership", YES, PART("флаги"), NO, PART("наблюдение")],
  ["9. Wounded leadership", YES, PART("флаги"), NO, PART("наблюдение")],
];

const rows = [
  head.map((h) => ({
    text: h,
    options: { bold: true, color: PAPER, fill: { color: INK }, fontSize: 10.5, align: "center", valign: "middle" },
  })),
];
body.forEach((r, i) => {
  const fill = i % 2 === 0 ? PAPER : SURFACE;
  rows.push(
    r.map((cell, c) => {
      const base = typeof cell === "string" ? { text: cell, options: { align: "left" } } : cell;
      return { text: base.text, options: { ...base.options, fill: { color: fill }, fontSize: 11.5, valign: "middle" } };
    }),
  );
});

s3.addTable(rows, {
  x: 0.62, y: 1.42, w: 12.1,
  colW: [4.3, 1.95, 2.55, 1.6, 1.7],
  rowH: 0.44,
  border: { type: "solid", color: "E2E2DE", pt: 1 },
  fontFace: BODY, color: INK,
  margin: [3, 6, 3, 6],
});

s3.addText(
  "«Флаги» значит: модель показывает, что кандидат сказал, но оценку не ставит. По блокам 8 и 9 оценку ставит человек.",
  {
    x: 0.62, y: 6.3, w: 12.1, h: 0.4,
    fontFace: BODY, fontSize: 12.5, italic: true, color: MUTED, margin: 0, isTextBox: true,
  },
);
s3.addNotes(
  "Do not skip past our own empty column. The Feynman challenge as it stands covers almost nothing on " +
  "their competency list, and saying that first is what makes the rest of the deck credible.\n\n" +
  "The ledger column is also honest: it reads what the candidate already submitted, so it covers the " +
  "same ground their interview covers, faster and earlier, but it is the same kind of evidence. It is " +
  "not a new measurement.\n\n" +
  "If they ask why the scenario column has gaps too: a fifteen-minute exercise cannot tell you why " +
  "someone chose this university or this major. Those belong in the interview and we are not trying to " +
  "take them."
);

// ── 4. The core difference ────────────────────────────────────────

const s4 = pres.addSlide();
s4.background = { color: PAPER };
eyebrow(s4, "ГЛАВНОЕ РАЗЛИЧИЕ", RUST);
slideTitle(s4, "Все три инструмента спрашивают о прошлом");

const layers = [
  ["Ипсативный тест", "«больше похоже на меня»", "Это самоописание. Формат защищает от приукрашивания, но кандидат всё равно рассказывает о себе."],
  ["Интервью ATOLA", "«что конкретно вы сделали?»", "Это самоотчёт о прошлом. Интервьюер видит, как человек рассказывает, но не видит самого события."],
  ["Наш ledger", "эссе, презентация, заявка", "То же самое, только читает машина: быстрее и раньше, но это тот же тип свидетельства."],
];
layers.forEach((l, i) => {
  const y = 1.45 + i * 1.06;
  s4.addShape(pres.ShapeType.roundRect, {
    x: 0.62, y, w: 12.1, h: 0.92, rectRadius: 0.06,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  s4.addText(l[0], {
    x: 0.95, y: y + 0.14, w: 2.9, h: 0.32,
    fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  s4.addText(l[1], {
    x: 0.95, y: y + 0.48, w: 2.9, h: 0.3,
    fontFace: BODY, fontSize: 12, italic: true, color: RUST, margin: 0, isTextBox: true,
  });
  s4.addText(l[2], {
    x: 4.1, y: y + 0.22, w: 8.3, h: 0.55, valign: "middle",
    fontFace: BODY, fontSize: 13, color: "44443F", margin: 0, isTextBox: true,
  });
});

s4.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 4.78, w: 12.1, h: 1.75, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});
s4.addText("Ни один из них не смотрит, как кандидат действует.", {
  x: 1.0, y: 5.0, w: 11.3, h: 0.45,
  fontFace: HEAD, fontSize: 22, bold: true, color: LIME, margin: 0, isTextBox: true,
});
s4.addText(
  "Ваш же принцип в модели KFLA: «оценивается наблюдаемое поведение, а не самоописание». " +
  "Отрепетировать рассказ о конфликте можно. Отрепетировать конфликт, который разворачивается прямо " +
  "сейчас, нельзя — и это прямой ответ на проблему социально желаемых ответов из вашей презентации.",
  {
    x: 1.0, y: 5.5, w: 11.3, h: 0.85,
    fontFace: BODY, fontSize: 14, color: "C9C9C4", margin: 0, isTextBox: true,
  },
);
s4.addNotes(
  "This is the argument of the whole deck, and it has to be delivered as a question about their design, " +
  "not as a correction of it.\n\n" +
  "The evidence is their own wording, which is why the previous slide quoted it. The KFLA card says " +
  "observable behaviour rather than self-description. The test asks what is more like me, which is " +
  "self-description by definition. Every ATOLA question is in the past tense. The interviewer genuinely " +
  "observes behaviour, but it is interview behaviour, not the competency in action.\n\n" +
  "Be fair about the forced-choice format: it is specifically designed to make self-report robust, and " +
  "meta-analytic work finds it resists faking far better than ordinary self-report scales. The point is " +
  "not that it is weak. The point is that it is still a report.\n\n" +
  "Include our own ledger in the list. We are describing a gap in the whole system, ours included, not " +
  "selling around one."
);

// ── 5. Feynman, honestly ──────────────────────────────────────────

const s5 = pres.addSlide();
s5.background = { color: PAPER };
eyebrow(s5, "НАША ЖЕ РАЗРАБОТКА, ЧЕСТНО");
slideTitle(s5, "Feynman-задание: что работает и что нет");

s5.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 1.45, w: 5.9, h: 2.25, rectRadius: 0.08,
  fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
});
s5.addText("Что работает", {
  x: 0.95, y: 1.68, w: 5.2, h: 0.35,
  fontFace: HEAD, fontSize: 17, bold: true, color: OLIVE, margin: 0, isTextBox: true,
});
s5.addText(
  [
    { text: "Единственное место во всей системе, где мы видим живое поведение", options: { bullet: true, breakLine: true } },
    { text: "Кандидат не знает «правильного» ответа заранее", options: { bullet: true, breakLine: true } },
    { text: "Асинхронно, не тратит часы комиссии", options: { bullet: true } },
  ],
  {
    x: 0.95, y: 2.12, w: 5.2, h: 1.45, valign: "top",
    fontFace: BODY, fontSize: 13, color: INK, paraSpaceAfter: 7, margin: 0, isTextBox: true,
  },
);

s5.addShape(pres.ShapeType.roundRect, {
  x: 6.82, y: 1.45, w: 5.9, h: 2.25, rectRadius: 0.08,
  fill: { color: "F7EAE6" }, line: { color: "F7EAE6", width: 0 },
});
s5.addText("Что не работает", {
  x: 7.15, y: 1.68, w: 5.2, h: 0.35,
  fontFace: HEAD, fontSize: 17, bold: true, color: RUST, margin: 0, isTextBox: true,
});
s5.addText(
  [
    { text: "Объяснить школьную тему ИИ-ребёнку не ложится ни на одну из девяти компетенций", options: { bullet: true, breakLine: true } },
    { text: "Награждает беглость речи и скорость печати — ровно преимущество «отполированного» кандидата", options: { bullet: true, breakLine: true } },
    { text: "Квиз измеряет понимание модели не меньше, чем качество объяснения", options: { bullet: true } },
  ],
  {
    x: 7.15, y: 2.12, w: 5.2, h: 1.45, valign: "top",
    fontFace: BODY, fontSize: 13, color: INK, paraSpaceAfter: 7, margin: 0, isTextBox: true,
  },
);

s5.addText("Три варианта", {
  x: 0.62, y: 3.95, w: 12.1, h: 0.35,
  fontFace: HEAD, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true,
});
const options = [
  ["A", "Оставить как есть", "Запоминается на демо, но методологически не защищается.", SURFACE, INK],
  ["B", "Переанкорить", "Кандидат объясняет свой собственный проект: блоки 6 и 7.", SURFACE, INK],
  ["C", "Заменить сценарием", "Живая ситуация с напарниками: блоки 3, 4, 5 и наблюдение для 8 и 9.", INK, PAPER],
];
options.forEach((o, i) => {
  const x = 0.62 + i * 4.09;
  s5.addShape(pres.ShapeType.roundRect, {
    x, y: 4.42, w: 3.84, h: 1.55, rectRadius: 0.08,
    fill: { color: o[3] }, line: { color: o[3], width: 0 },
  });
  s5.addText(o[0], {
    x: x + 0.3, y: 4.6, w: 0.8, h: 0.35,
    fontFace: HEAD, fontSize: 18, bold: true, color: o[3] === INK ? LIME : MUTED, margin: 0, isTextBox: true,
  });
  s5.addText(o[1], {
    x: x + 0.3, y: 4.98, w: 3.25, h: 0.32,
    fontFace: HEAD, fontSize: 15, bold: true, color: o[4], margin: 0, isTextBox: true,
  });
  s5.addText(o[2], {
    x: x + 0.3, y: 5.34, w: 3.25, h: 0.6, valign: "top",
    fontFace: BODY, fontSize: 12, color: o[3] === INK ? "C9C9C4" : "44443F", margin: 0, isTextBox: true,
  });
});
s5.addText("Наша рекомендация: C, с коротким teach-back из B в конце сценария.", {
  x: 0.62, y: 6.15, w: 12.1, h: 0.4,
  fontFace: BODY, fontSize: 13.5, italic: true, color: INK, margin: 0, isTextBox: true,
});
s5.addNotes(
  "Lead with our own weaknesses. If they remember one thing from our Stage-1 demo it is the AI child, so " +
  "criticising it ourselves is more persuasive than defending it.\n\n" +
  "The second weakness is the one that should land with them specifically: a chat exercise rewards fast, " +
  "fluent typing, which is exactly the polished-city-candidate advantage their deck says selection must " +
  "stop rewarding. We built something that works against their own problem statement 5.\n\n" +
  "Do not oversell option C. It is unvalidated, it is currently weighted at zero in our system, and it " +
  "stays at zero until agreement with committee ratings can be measured on the historical data at the " +
  "implementation stage. Say that before they ask."
);

// ── 6. What only a live sample gives ──────────────────────────────

const s6 = pres.addSlide();
s6.background = { color: PAPER };
eyebrow(s6, "ЧТО ДОБАВЛЯЕТ ЖИВОЙ СЦЕНАРИЙ");
slideTitle(s6, "Одно наблюдение, которое иначе не получить");

s6.addText(
  "Кандидат ведёт проект. Два ИИ-напарника спорят. Кому-то предлагают срезать угол. " +
  "Один из напарников говорит что-то обидное. Всё это разворачивается в реальном времени.",
  {
    x: 0.62, y: 1.4, w: 12.1, h: 0.6,
    fontFace: BODY, fontSize: 15, color: INK, margin: 0, isTextBox: true,
  },
);

const gains = [
  ["Работа в команде, блок 4", "Вы уже описали эту ситуацию в примере ипсативного вопроса: «когда в группе начинается спор, я…». В сценарии это не выбор из четырёх вариантов, а то, что человек реально делает."],
  ["Ценности, блок 5", "Срезать угол или нет — выбор, а не утверждение о себе."],
  ["Wounded leadership, блок 9", "Высокий уровень у вас описан как «глубокая эмпатия к боли других» и «не уходит в жёсткость, контроль или жертвенность». Это можно увидеть по реакции на обиженного напарника — не спрашивая подростка про его собственную травму."],
];
gains.forEach((g, i) => {
  const y = 2.2 + i * 1.22;
  s6.addShape(pres.ShapeType.ellipse, {
    x: 0.65, y: y + 0.12, w: 0.18, h: 0.18,
    fill: { color: LIME }, line: { color: LIME, width: 0 },
  });
  s6.addText(g[0], {
    x: 1.05, y, w: 11.6, h: 0.35,
    fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  s6.addText(g[1], {
    x: 1.05, y: y + 0.38, w: 11.6, h: 0.72, valign: "top",
    fontFace: BODY, fontSize: 13, color: "44443F", margin: 0, isTextBox: true,
  });
});

s6.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 5.95, w: 12.1, h: 1.0, rectRadius: 0.08,
  fill: { color: "F7EAE6" }, line: { color: "F7EAE6", width: 0 },
});
s6.addText(
  [
    { text: "Риски, о которых мы говорим сами. ", options: { bold: true, color: RUST } },
    { text: "Насколько ИИ-напарник ведёт себя как живой человек — не доказано. Сценарий близок к ситуации из вашего закрытого банка, значит может стать подсказкой. Вес в скоринге — ноль, пока не проверим на ваших исторических данных.", options: { color: "44443F" } },
  ],
  {
    x: 0.95, y: 6.15, w: 11.45, h: 0.65, valign: "middle",
    fontFace: BODY, fontSize: 12.5, margin: 0, isTextBox: true,
  },
);
s6.addNotes(
  "The third row is the strongest idea we have and it is worth slowing down for.\n\n" +
  "Their own high anchor for wounded leadership is deep empathy toward other people's pain, and not " +
  "sliding into harshness, control or a victim position. Those are behavioural consequences. You cannot " +
  "ask a 16-year-old to narrate trauma in an application form, and we refused to build a form that does. " +
  "But you can watch how someone responds when a teammate is hurt, which observes the consequence " +
  "without touching the cause.\n\n" +
  "Be explicit that this produces an observation for their interviewer, never a rating. Our system does " +
  "not assign a level for blocks 8 or 9 under any circumstances.\n\n" +
  "The leakage risk is real and we should name it before they do. Their example ipsative item is about " +
  "a group argument, so a scenario about a group argument sits close to their bank. The mitigation is " +
  "that Talent Craft co-authors or reviews the scenario and it rotates."
);


// ── 7. Questions about their two instruments ──────────────────────

const s7q = pres.addSlide();
s7q.background = { color: PAPER };
eyebrow(s7q, "ВСТРЕЧНЫЕ ВОПРОСЫ");
slideTitle(s7q, "Вопросы к вашим двум инструментам");

function questionColumn(slide, x, heading, subtitle, items, accent) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y: 1.45, w: 5.9, h: 4.05, rectRadius: 0.08,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  slide.addText(heading, {
    x: x + 0.33, y: 1.68, w: 5.25, h: 0.35,
    fontFace: HEAD, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  slide.addText(subtitle, {
    x: x + 0.33, y: 2.04, w: 5.25, h: 0.3,
    fontFace: BODY, fontSize: 12, italic: true, color: accent, margin: 0, isTextBox: true,
  });
  items.forEach((item, i) => {
    const y = 2.48 + i * 0.99;
    slide.addText(String(i + 1), {
      x: x + 0.33, y, w: 0.3, h: 0.28,
      fontFace: HEAD, fontSize: 14, bold: true, color: accent, margin: 0, isTextBox: true,
    });
    slide.addText(item[0], {
      x: x + 0.68, y, w: 4.9, h: 0.3,
      fontFace: BODY, fontSize: 13, bold: true, color: INK, margin: 0, isTextBox: true,
    });
    slide.addText(item[1], {
      x: x + 0.68, y: y + 0.32, w: 4.9, h: 0.6, valign: "top",
      fontFace: BODY, fontSize: 11.5, color: "5A5A55", margin: 0, isTextBox: true,
    });
  });
}

questionColumn(s7q, 0.62, "Ипсативный тест", "формат уже защищает от приукрашивания — вопросы про другое", [
  ["Суммы баллов или IRT-оценки?", "От этого зависит, можно ли вообще сравнивать двух кандидатов по одной компетенции, или только смотреть профиль одного."],
  ["Банк проверяли на реальных абитуриентах?", "На исследовательской выборке приукрашивают меньше, чем когда на кону грант."],
  ["Отдаёт ли платформа время и паттерны выбора?", "Одинаковая позиция варианта, слишком быстрые блоки, расхождения внутри одной компетенции. Мы посчитаем эти флаги без всякого ИИ."],
], RUST);

questionColumn(s7q, 6.82, "Видеопрезентация", "прежде чем её анализировать, стоит спросить, зачем она", [
  ["Что видео измеряет, чего нет в эссе и интервью?", "Если ответ «навык презентации» — это манера речи, а её ваши же критерии запрещают учитывать."],
  ["Кто его смотрит сегодня и сколько?", "Если смотрит человек — это часы комиссии, которые можно вернуть. Если не смотрит никто — зачем собирать."],
  ["Что происходит при плохой записи?", "Сейчас кандидата это как-то задевает? Возможна ли пересдача или письменная замена?"],
], RUST);

s7q.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 5.72, w: 12.1, h: 1.1, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});
s7q.addText(
  [
    { text: "Наша позиция. ", options: { bold: true, color: LIME } },
    { text: "Качество звука — это про телефон и комнату, то есть про доход семьи. Поэтому у нас ничего не оценивается по записи и по манере речи. Для казахской спонтанной речи плохое распознавание — не редкий случай, а норма, и ошибки концентрируются на сельских кандидатах.", options: { color: "C9C9C4" } },
  ],
  {
    x: 1.0, y: 5.92, w: 11.35, h: 0.72, valign: "middle",
    fontFace: BODY, fontSize: 12.5, margin: 0, isTextBox: true,
  },
);
s7q.addNotes(
  "These are the questions the team wanted to raise, sharpened so they do not sound like we skipped their " +
  "deck.\n\n" +
  "On faking: do NOT open with 'can candidates just lie'. Their slide on the test already answers that: " +
  "all four options are socially acceptable so the right answer is not readable. Meta-analytic work agrees " +
  "the format resists faking far better than ordinary self-report, and quasi-ipsative designs resist it " +
  "most, though no format is immune and effects are larger in real applicant samples than in research " +
  "ones. So the useful questions are scoring type, validation sample, and response quality.\n\n" +
  "Why the scoring-type question matters: classical forced-choice scoring gives everyone the same total, " +
  "which distorts profiles and limits comparison between people. Their published bands look like summed " +
  "option weights, while the deck says items were built with Item Response Theory. Those are different " +
  "claims and we need to know which one the per-competency numbers are, because it decides whether " +
  "ranking two candidates on one competency is even legitimate.\n\n" +
  "The third test question is an offer, not a complaint. Straight-lining, implausibly fast blocks and " +
  "inconsistency across blocks measuring the same competency are all detectable arithmetic. It needs no " +
  "model and it is theirs to keep.\n\n" +
  "On the video: the real question is what it is for. If nobody watches it, collecting it costs applicants " +
  "effort for nothing. If a human watches every one, that is committee time we could protect. If it is " +
  "meant to measure presentation skill, that collides head-on with their own rule about manner of speech, " +
  "and it is better to hear them say it than for us to assume.\n\n" +
  "Keep the audio point on the fairness ground, not the technical one. It is not that transcription is " +
  "annoying. It is that transcription error rises with accent, code-switching and a cheap microphone, so " +
  "the noise lands on exactly the applicants the university exists to find."
);


// ── 8. What we can do ourselves ───────────────────────────────────

const s8a = pres.addSlide();
s8a.background = { color: PAPER };
eyebrow(s8a, "НЕ ТОЛЬКО ВОПРОСЫ");
slideTitle(s8a, "Что мы можем сделать сами");

function mitigationColumn(slide, x, heading, ours, theirs) {
  slide.addText(heading, {
    x: x + 0.05, y: 1.4, w: 5.8, h: 0.35,
    fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  slide.addShape(pres.ShapeType.roundRect, {
    x, y: 1.85, w: 5.9, h: 3.05, rectRadius: 0.08,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  slide.addText("МОЖЕМ САМИ", {
    x: x + 0.33, y: 2.05, w: 5.25, h: 0.25,
    fontFace: BODY, fontSize: 10, bold: true, color: OLIVE, charSpacing: 1.2, margin: 0, isTextBox: true,
  });
  ours.forEach((item, i) => {
    const y = 2.4 + i * 0.83;
    slide.addText(item[0], {
      x: x + 0.33, y, w: 5.25, h: 0.28,
      fontFace: BODY, fontSize: 12.5, bold: true, color: INK, margin: 0, isTextBox: true,
    });
    slide.addText(item[1], {
      x: x + 0.33, y: y + 0.28, w: 5.25, h: 0.5, valign: "top",
      fontFace: BODY, fontSize: 11, color: "5A5A55", margin: 0, isTextBox: true,
    });
  });
  slide.addShape(pres.ShapeType.roundRect, {
    x, y: 5.02, w: 5.9, h: 1.2, rectRadius: 0.08,
    fill: { color: "F7EAE6" }, line: { color: "F7EAE6", width: 0 },
  });
  slide.addText("НУЖНО РЕШЕНИЕ ОТ ВАС", {
    x: x + 0.33, y: 5.2, w: 5.25, h: 0.25,
    fontFace: BODY, fontSize: 10, bold: true, color: RUST, charSpacing: 1.2, margin: 0, isTextBox: true,
  });
  slide.addText(theirs, {
    x: x + 0.33, y: 5.48, w: 5.25, h: 0.6, valign: "top",
    fontFace: BODY, fontSize: 11.5, color: INK, margin: 0, isTextBox: true,
  });
}

mitigationColumn(s8a, 0.62, "Если кандидат приукрашивает себя", [
  ["Триангуляция теста и материалов", "Тест говорит «очень высокая работа в команде», а в материалах ни одного «мы» — это расхождение. Не минус баллов, а вопрос интервьюеру."],
  ["Живой сценарий", "Анкету можно отрепетировать. Ситуацию, которая идёт прямо сейчас, — нет."],
  ["Предупреждение в начале заявки", "«Ваши примеры будут обсуждаться на интервью». Единственная мера с доказанным эффектом на приукрашивание."],
], "Поэлементные данные теста: время на блок и паттерны выбора. Без них флаги качества ответов посчитать нельзя.");

mitigationColumn(s8a, 6.82, "Если запись плохо слышно", [
  ["Порог уверенности распознавания", "Ниже порога транскрипт помечается «в оценке не используется» и служит только навигацией по аудио для человека."],
  ["Два распознавателя вместо одного", "Согласие между ними и есть мера уверенности, которую видно комиссии."],
  ["Не оценивать с записи вообще", "Это то, что у нас уже сделано: видео остаётся для людей."],
], "Что предпочтительнее: короткий письменный вариант в заявке, или возможность кандидату поправить свой транскрипт после загрузки?");

s8a.addText(
  "Ни один из этих пунктов не требует менять вашу методологию. Первые три в каждой колонке — наша работа, не ваша.",
  {
    x: 0.62, y: 6.42, w: 12.1, h: 0.4,
    fontFace: BODY, fontSize: 13, italic: true, color: MUTED, margin: 0, isTextBox: true,
  },
);
s8a.addNotes(
  "Bring solutions, not only questions. This slide is what separates a team that read the deck from a team " +
  "that is doing the work.\n\n" +
  "Triangulation is the important one and it is already built: we ingest the test result in their own " +
  "bands, compare it against what the written materials actually show, and emit a discrepancy. Say " +
  "clearly that a discrepancy never changes a score. Its direction is ambiguous, because a modest " +
  "candidate and an exaggerating one produce the same gap, so the only honest use is a probe for the " +
  "interviewer.\n\n" +
  "The honesty prime is one line of form copy and it is the one intervention with published evidence " +
  "behind it: warning candidates that answers will be verified reduces deceptive impression management. " +
  "Detecting lies from language does not work, so we are not proposing it.\n\n" +
  "On the transcript correction option: it is worth floating because it is smaller than adding a writing " +
  "task, and the applicant owns their own words. The catch to mention if they like it is that we would " +
  "keep both versions, because an applicant who rewrites rather than corrects has produced a polished " +
  "text, and polish is what we are trying not to reward."
);

// ── 7. What we do not know yet ────────────────────────────────────

const s7 = pres.addSlide();
s7.background = { color: PAPER };
eyebrow(s7, "ПЕРВЫЙ ЭТАП");
slideTitle(s7, "Чего мы не знаем — и почему это не блокирует");

s7.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 1.45, w: 5.9, h: 3.6, rectRadius: 0.08,
  fill: { color: "F7EAE6" }, line: { color: "F7EAE6", width: 0 },
});
s7.addText("Закрыто до этапа внедрения", {
  x: 0.95, y: 1.7, w: 5.2, h: 0.38,
  fontFace: HEAD, fontSize: 17, bold: true, color: RUST, margin: 0, isTextBox: true,
});
s7.addText(
  [
    { text: "Банк из 95 вопросов с разметкой баллов", options: { bullet: true, breakLine: true } },
    { text: "Точные веса компетенций и пороги отсечения", options: { bullet: true, breakLine: true } },
    { text: "Антипримеры и «ловушки» в вариантах ответов", options: { bullet: true, breakLine: true } },
    { text: "Обезличенные данные предыдущих оценок", options: { bullet: true } },
  ],
  {
    x: 0.95, y: 2.2, w: 5.2, h: 2.6, valign: "top",
    fontFace: BODY, fontSize: 13.5, color: INK, paraSpaceAfter: 9, margin: 0, isTextBox: true,
  },
);

s7.addShape(pres.ShapeType.roundRect, {
  x: 6.82, y: 1.45, w: 5.9, h: 3.6, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});
s7.addText("Как мы к этому построились", {
  x: 7.15, y: 1.7, w: 5.2, h: 0.38,
  fontFace: HEAD, fontSize: 17, bold: true, color: LIME, margin: 0, isTextBox: true,
});
s7.addText(
  [
    { text: "Рубрика версионируется. Семь из девяти шкал помечены как черновые и заменяются целиком", options: { bullet: true, breakLine: true } },
    { text: "Весов и порогов у нас нет вообще: это конфигурация, которую даёте вы", options: { bullet: true, breakLine: true } },
    { text: "Результат теста мы принимаем и показываем в ваших же полосах. Не пересчитываем", options: { bullet: true, breakLine: true } },
    { text: "Каждая оценка помечена версией рубрики, поэтому сравнима только внутри версии", options: { bullet: true } },
  ],
  {
    x: 7.15, y: 2.2, w: 5.2, h: 2.6, valign: "top",
    fontFace: BODY, fontSize: 13, color: PAPER, paraSpaceAfter: 9, margin: 0, isTextBox: true,
  },
);

s7.addText(
  "Закрытая часть подключается, а не переписывается. Когда придут настоящие шкалы, меняется содержимое, а не код.",
  {
    x: 0.62, y: 5.35, w: 12.1, h: 0.5,
    fontFace: HEAD, fontSize: 18, italic: true, color: INK, margin: 0, isTextBox: true,
  },
);
s7.addNotes(
  "This slide answers the disclosure slide in their own deck, and it is the one that makes us look like " +
  "we plan to still be here in November.\n\n" +
  "The honest position: we built against the two competency scales they published in full and drafted the " +
  "other seven from the one-line descriptions, marked provisional. Swapping them is content, not " +
  "engineering.\n\n" +
  "The line about weights is worth saying slowly. We ship none. A tool that quietly invented the " +
  "committee's cut-offs would be taking ownership of the methodology, and that ownership is theirs."
);

// ── 8. The open question ──────────────────────────────────────────

const s8 = pres.addSlide();
s8.background = { color: INK };
s8.addText("Открытый вопрос", {
  x: 0.9, y: 0.8, w: 11.5, h: 0.75,
  fontFace: HEAD, fontSize: 34, bold: true, color: PAPER, margin: 0, isTextBox: true,
});
s8.addText(
  "Мы не будем менять методологию без вас. Четыре вещи, по которым нужно ваше мнение:",
  {
    x: 0.9, y: 1.65, w: 11.5, h: 0.4,
    fontFace: BODY, fontSize: 15.5, color: "C9C9C4", margin: 0, isTextBox: true,
  },
);

const asks = [
  ["Нужен ли живой замер поведения вообще?", "Если тест и интервью вас устраивают, мы уберём Feynman и сосредоточимся на ledger'е. Это нормальный ответ."],
  ["Если нужен — кто пишет сценарий?", "Мы даём движок и редактор. Содержание должно прийти от вас или Talent Craft, иначе это не ваша методология."],
  ["Приемлемо ли наблюдать реакцию вместо вопроса про травму?", "По блоку 9 это единственный способ, который мы нашли, не спрашивая подростка о тяжёлом опыте в анкете."],
  ["Новый инструмент или аккуратная реализация вашего?", "Нам называли креативность среди критериев, но в шести опубликованных её нет. Сценарий — наша ставка на неё. Скажете «лучше ваша методология, сделанная хорошо» — уберём сценарий и вложим эти дни в ledger."],
];
asks.forEach((a, i) => {
  const y = 2.05 + i * 1.12;
  s8.addShape(pres.ShapeType.ellipse, {
    x: 0.92, y: y + 0.11, w: 0.17, h: 0.17,
    fill: { color: LIME }, line: { color: LIME, width: 0 },
  });
  s8.addText(a[0], {
    x: 1.32, y, w: 11, h: 0.38,
    fontFace: HEAD, fontSize: 17.5, bold: true, color: PAPER, margin: 0, isTextBox: true,
  });
  s8.addText(a[1], {
    x: 1.32, y: y + 0.4, w: 11, h: 0.66, valign: "top",
    fontFace: BODY, fontSize: 12.5, color: "AFAFA9", margin: 0, isTextBox: true,
  });
});

s8.addShape(pres.ShapeType.roundRect, {
  x: 0.9, y: 6.62, w: 11.55, h: 0.72, rectRadius: 0.08,
  fill: { color: "232320" }, line: { color: "232320", width: 0 },
});
s8.addText(
  "До этапа внедрения мы ничего не взвешиваем. Сценарий идёт с весом ноль, пока не проверим на ваших данных.",
  {
    x: 1.25, y: 6.79, w: 10.9, h: 0.4,
    fontFace: BODY, fontSize: 13.5, color: LIME, margin: 0, isTextBox: true,
  },
);
s8.addNotes(
  "End on a real question, not a proposal. The first ask is genuinely open: if they say a live exercise " +
  "is not wanted, that is a clean answer and we drop it and spend the time on the ledger instead. Say " +
  "that and mean it.\n\n" +
  "The second ask is where the methodology ownership line sits. We provide the engine and an editor; the " +
  "content has to come from them, or we have quietly written assessment content for a methodology we do " +
  "not own.\n\n" +
  "The third ask needs care in the room. Do not describe it as extracting trauma signals. Describe it as " +
  "watching how someone treats a person who is upset, which is the behaviour their own anchor names.\n\n" +
  "The fourth ask is about where we spend the next ten days. Creativity was named to us as a judging " +
  "criterion but it is not among the six published on their own criteria slide, so asking what it means " +
  "in practice is fair rather than gamey. Ask it as a direction question, never as 'how do we score " +
  "points'. And mean the offer: if they say a well-executed version of their own methodology is worth " +
  "more than a new instrument, dropping the scenario is the right call and we should say so on the spot."
);

pres.writeFile({ fileName: "docs/inVisionU_methodology_comparison.pptx" }).then((f) => {
  console.log("wrote", f);
});
