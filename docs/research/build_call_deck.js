/**
 * Builds the question deck for the call with inVision U.
 *
 *   node docs/research/build_call_deck.js
 *
 * Slides are in Russian because the audience is a methodology or admissions
 * person at the client, not an engineer on our side. Speaker notes are in
 * English and carry the reason each question is on the list, so whoever
 * presents knows what the answer changes.
 *
 * Scope: only questions that affect work between now and Demo Day on 1-3
 * October. Everything that needs the Stage-2 data drop is deliberately absent.
 */

const pptxgen = require("pptxgenjs");

const INK = "141414";
const PAPER = "FFFFFF";
const SURFACE = "F1F1EE";
const LIME = "C1F11D";
const MUTED = "6E6E68";
const RUST = "A8412F";

const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Winchesters";
pres.title = "AI Leader ID — вопросы к методологии";

/** A numbered disc, the one motif repeated on every content slide. */
function disc(slide, x, y, n, opts = {}) {
  const size = opts.size || 0.44;
  slide.addShape(pres.ShapeType.ellipse, {
    x, y, w: size, h: size,
    fill: { color: opts.fill || INK },
    line: { color: opts.fill || INK, width: 0 },
  });
  slide.addText(String(n), {
    x, y, w: size, h: size,
    align: "center", valign: "middle", margin: 0,
    fontFace: BODY, fontSize: opts.fontSize || 14, bold: true,
    color: opts.color || LIME, isTextBox: true,
  });
}

function slideTitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: 0.62, y: opts.y || 0.45, w: 12.1, h: 0.8,
    fontFace: HEAD, fontSize: opts.fontSize || 32, bold: true,
    color: opts.color || INK, margin: 0, isTextBox: true,
  });
}

// ── 1. Title ──────────────────────────────────────────────────────

const s1 = pres.addSlide();
s1.background = { color: INK };
s1.addText("AI Leader ID", {
  x: 0.9, y: 1.5, w: 11.5, h: 0.6,
  fontFace: BODY, fontSize: 16, color: LIME, charSpacing: 3, margin: 0, isTextBox: true,
});
s1.addText("9 вопросов к методологии", {
  x: 0.9, y: 2.1, w: 11.5, h: 1.3,
  fontFace: HEAD, fontSize: 48, bold: true, color: PAPER, margin: 0, isTextBox: true,
});
s1.addText("Три из них уже заложены в код. Поменять сейчас дешевле, чем в ноябре.", {
  x: 0.9, y: 3.5, w: 10.5, h: 0.5,
  fontFace: BODY, fontSize: 17, color: "C9C9C4", margin: 0, isTextBox: true,
});
s1.addShape(pres.ShapeType.line, {
  x: 0.9, y: 4.45, w: 2.2, h: 0, line: { color: LIME, width: 2 },
});
s1.addText(
  [
    { text: "Команда Winchesters", options: { bold: true, breakLine: true } },
    { text: "Разговор до Demo Day, 1–3 октября", options: {} },
  ],
  {
    x: 0.9, y: 4.75, w: 7, h: 0.9,
    fontFace: BODY, fontSize: 14, color: "9A9A94", margin: 0, isTextBox: true,
  },
);
s1.addNotes(
  "Open with one sentence: we rebuilt the tool around your nine competencies and your BARS scales, " +
  "and that forced decisions that belong to you rather than to us.\n\n" +
  "Then show two things on screen for 30 seconds each before any question: a committee card where a " +
  "rating expands into the exact quote and the anchor it matched, and the invariance table where school " +
  "type, grades, hardship wording and language all move the score by 0.0.\n\n" +
  "Scope note for us: every question here affects work before Demo Day. Anything needing the Stage-2 " +
  "data drop is deliberately left out of this call."
);

// ── 2. What changed ───────────────────────────────────────────────

const s2 = pres.addSlide();
s2.background = { color: PAPER };
slideTitle(s2, "Что изменилось после первого этапа");

const colY = 1.55;
const colH = 3.1;
s2.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: colY, w: 5.85, h: colH, rectRadius: 0.08,
  fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
});
s2.addShape(pres.ShapeType.roundRect, {
  x: 6.85, y: colY, w: 5.85, h: colH, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});

s2.addText("БЫЛО НА ПЕРВОМ ЭТАПЕ", {
  x: 1.0, y: colY + 0.3, w: 5.1, h: 0.35,
  fontFace: BODY, fontSize: 11, bold: true, color: MUTED, charSpacing: 1.5, margin: 0, isTextBox: true,
});
s2.addText(
  [
    { text: "5 наших собственных измерений, балл 0–100", options: { bullet: true, breakLine: true } },
    { text: "Балл зависел от типа школы и от оценок", options: { bullet: true, breakLine: true } },
    { text: "Детектор «эссе написал ИИ»", options: { bullet: true } },
  ],
  {
    x: 1.0, y: colY + 0.78, w: 5.1, h: 2.4, valign: "top",
    fontFace: BODY, fontSize: 15, color: INK, paraSpaceAfter: 10, margin: 0, isTextBox: true,
  },
);

s2.addText("СТАЛО СЕЙЧАС", {
  x: 7.23, y: colY + 0.3, w: 5.1, h: 0.35,
  fontFace: BODY, fontSize: 11, bold: true, color: LIME, charSpacing: 1.5, margin: 0, isTextBox: true,
});
s2.addText(
  [
    { text: "Ваши 9 компетенций и 3 уровня BARS", options: { bullet: true, breakLine: true } },
    { text: "Каждая оценка раскрывается в точную цитату кандидата", options: { bullet: true, breakLine: true } },
    { text: "Бэкграунд не влияет на балл, и это проверяется автотестом", options: { bullet: true } },
  ],
  {
    x: 7.23, y: colY + 0.78, w: 5.1, h: 2.4, valign: "top",
    fontFace: BODY, fontSize: 15, color: PAPER, paraSpaceAfter: 10, margin: 0, isTextBox: true,
  },
);

s2.addText("Пересборка заставила нас принять решения, которые принадлежат вам. Отсюда девять вопросов.", {
  x: 0.62, y: 5.35, w: 12.1, h: 0.5,
  fontFace: HEAD, fontSize: 18, italic: true, color: INK, margin: 0, isTextBox: true,
});
s2.addNotes(
  "This slide exists so the questions land. Without it they sound like second-guessing; with it they " +
  "are the natural consequence of adopting the client's own methodology.\n\n" +
  "Say the invariance point out loud: it is not a promise, it is a test that runs on every change, and " +
  "it currently reads 0.0 for school type, grades, hardship wording and language."
);

// ── 3. Two deletions ──────────────────────────────────────────────

const s3 = pres.addSlide();
s3.background = { color: PAPER };
slideTitle(s3, "Мы удалили две функции из нашей демо");

function deletionCard(slide, x, n, heading, why, question) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y: 1.55, w: 5.85, h: 4.9, rectRadius: 0.08,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  disc(slide, x + 0.38, 1.9, n, { fill: RUST, color: PAPER });
  slide.addText(heading, {
    x: x + 0.95, y: 1.88, w: 4.6, h: 0.55,
    fontFace: HEAD, fontSize: 19, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  slide.addText("ПОЧЕМУ УБРАЛИ", {
    x: x + 0.38, y: 2.62, w: 5.1, h: 0.28,
    fontFace: BODY, fontSize: 10, bold: true, color: MUTED, charSpacing: 1.2, margin: 0, isTextBox: true,
  });
  slide.addText(why, {
    x: x + 0.38, y: 2.92, w: 5.1, h: 1.7,
    fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true,
  });
  slide.addShape(pres.ShapeType.roundRect, {
    x: x + 0.38, y: 4.92, w: 5.1, h: 1.25, rectRadius: 0.06,
    fill: { color: PAPER }, line: { color: "DEDEDA", width: 1 },
  });
  slide.addText(question, {
    x: x + 0.58, y: 5.06, w: 4.7, h: 1.0,
    fontFace: BODY, fontSize: 13.5, bold: true, color: INK, margin: 0, isTextBox: true,
  });
}

deletionCard(
  s3, 0.62, 1,
  "Детектор «эссе написал ИИ»",
  "Такие детекторы массово ошибаются на тех, кто пишет не на родном языке. По казахскому их никто не калибровал. Ложные срабатывания попадали бы ровно на сельских кандидатов.",
  "Вопрос: подойдёт ли вместо детектора подсказка интервьюеру — попросить кандидата пересказать свой абзац своими словами?",
);
deletionCard(
  s3, 6.85, 2,
  "Траектория по типу школы",
  "Стартовый уровень зависел от школы. Даже когда это в пользу кандидата, это всё равно оценка по бэкграунду. «Плюс двенадцать за село» невозможно защитить перед родителем.",
  "Вопрос: правильно ли показывать контекст комиссии рядом с оценкой, но не внутри неё?",
);
s3.addNotes(
  "Raise these before they notice. Both were headline features in our Stage-1 pitch, so if the person " +
  "remembers our demo, they remember these.\n\n" +
  "Why question 1 is on the list: published measurements put some detectors near a 100% false-positive " +
  "rate on non-native academic writing, and there is no Kazakh benchmark at all, so any number we printed " +
  "for a Kazakh essay was uncalibrated by construction. Those errors land on the exact group the " +
  "university exists to find. Frame the replacement as their choice, because it is their reputation on a " +
  "wrong flag.\n\n" +
  "Why question 2 is on the list: this is the mechanism that failed publicly in the UK in 2020, where a " +
  "school-level prior moved individual results and was reversed within days. Say that if they push back. " +
  "Growth is still assessed, but from what the candidate describes doing over time, in their own words."
);

// ── 4. The rule we invented ───────────────────────────────────────

const s4 = pres.addSlide();
s4.background = { color: PAPER };
slideTitle(s4, "Правило, которое мы написали за вас");
disc(s4, 12.06, 0.5, 3, { size: 0.62, fontSize: 20 });

s4.addText(
  "В блоке «Лидерские способности» пять индикаторов. Интервьюер оценивает каждый. " +
  "Но как из пяти оценок получается одна оценка блока?",
  {
    x: 0.62, y: 1.42, w: 11.3, h: 0.75,
    fontFace: BODY, fontSize: 16, color: INK, margin: 0, isTextBox: true,
  },
);

s4.addText("ПРАВИЛО, КОТОРОЕ СЕЙЧАС РАБОТАЕТ В КОДЕ. ЕГО ПРИДУМАЛИ МЫ, А НЕ ВЫ", {
  x: 0.62, y: 2.3, w: 11.3, h: 0.3,
  fontFace: BODY, fontSize: 10.5, bold: true, color: MUTED, charSpacing: 1.2, margin: 0, isTextBox: true,
});

const rules = [
  ["два и больше «высоко», ни одного «слабо»", "ВЫСОКО"],
  ["есть «слабо», нет «высоко»", "СЛАБО"],
  ["во всех остальных случаях", "НОРМАЛЬНО"],
];
rules.forEach((r, i) => {
  const x = 0.62 + i * 4.05;
  s4.addShape(pres.ShapeType.roundRect, {
    x, y: 2.68, w: 3.8, h: 1.35, rectRadius: 0.06,
    fill: { color: SURFACE }, line: { color: SURFACE, width: 0 },
  });
  s4.addText(r[0], {
    x: x + 0.25, y: 2.85, w: 3.3, h: 0.6,
    fontFace: BODY, fontSize: 13, color: INK, margin: 0, isTextBox: true,
  });
  s4.addText("→  " + r[1], {
    x: x + 0.25, y: 3.5, w: 3.3, h: 0.38,
    fontFace: BODY, fontSize: 14, bold: true, color: INK, margin: 0, isTextBox: true,
  });
});

s4.addShape(pres.ShapeType.roundRect, {
  x: 0.62, y: 4.35, w: 12.1, h: 1.55, rectRadius: 0.08,
  fill: { color: INK }, line: { color: INK, width: 0 },
});
s4.addText("Вопрос: как это правило звучит у вас?", {
  x: 1.0, y: 4.58, w: 11.3, h: 0.45,
  fontFace: HEAD, fontSize: 21, bold: true, color: LIME, margin: 0, isTextBox: true,
});
s4.addText(
  "Если правила нет и решает интервьюер — это и есть проблема калибровки со слайда 5 вашей презентации: " +
  "два интервьюера из одинаковых наблюдений получают разные оценки блока.",
  {
    x: 1.0, y: 5.06, w: 11.3, h: 0.7,
    fontFace: BODY, fontSize: 14, color: "C9C9C4", margin: 0, isTextBox: true,
  },
);
s4.addNotes(
  "The single most important question on the list, which is why it has a slide to itself.\n\n" +
  "Why it is here: we had to invent a roll-up rule to ship anything at all, and it is currently running " +
  "in the code. It decides what every committee card shows. It is their scale, so it should be their rule.\n\n" +
  "Two possible answers, both useful. If they have a written rule, we implement it verbatim and delete " +
  "ours in an afternoon. If they say the interviewer decides, we have just surfaced a real inconsistency " +
  "in their own process, and it is the calibration problem their own deck names. Deliver that gently and " +
  "offer to help measure it rather than scoring a point.\n\n" +
  "Do not leave the call without an answer or a named person who owns it."
);

// ── 5. Three decisions we took ourselves ──────────────────────────

const s5 = pres.addSlide();
s5.background = { color: PAPER };
slideTitle(s5, "Три решения, которые мы приняли сами");

const rows = [
  [4, "«Слабо» и «не наблюдалось» — это разное?",
   "Мы считаем это разными состояниями. Отказ с формулировкой «поведения по индикатору не наблюдали» выдерживает апелляцию. «Слабо», когда кандидат просто не поднял тему, — нет."],
  [5, "По компетенциям 8 и 9 модель не ставит оценку вообще",
   "Только показывает интервьюеру, что кандидат сказал. Оценку ставит человек. Форма заявки не спрашивает про тяжёлый опыт — этот вопрос задаётся вживую. Это правильная граница или мы перестраховались?"],
  [6, "Оценки успеваемости больше не влияют на скоринг",
   "В вашей презентации сказано, что успеваемость не измеряет лидерский потенциал. К тому же оценка в сельской школе и в лицее — это разные измерения. Правильно ли мы прочитали?"],
];
rows.forEach((row, i) => {
  const y = 1.55 + i * 1.62;
  disc(s5, 0.62, y + 0.06, row[0]);
  s5.addText(row[1], {
    x: 1.25, y, w: 11.4, h: 0.4,
    fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  s5.addText(row[2], {
    x: 1.25, y: y + 0.45, w: 11.4, h: 0.85,
    fontFace: BODY, fontSize: 13.5, color: "44443F", margin: 0, isTextBox: true,
  });
});
s5.addText("Все три уже работают в коде. Изменить их сейчас — день работы.", {
  x: 0.62, y: 6.55, w: 12.1, h: 0.4,
  fontFace: BODY, fontSize: 14, italic: true, color: MUTED, margin: 0, isTextBox: true,
});
s5.addNotes(
  "Why question 4: if their historical ratings collapse 'weak' and 'not observed' into one value, then " +
  "the data arriving on 5 October cannot tell them apart either. We need to know that before we report " +
  "agreement numbers, not after.\n\n" +
  "Why question 5: their own deck calls purpose-driven and wounded leadership the hardest to automate and " +
  "the most valuable. Research on post-traumatic growth also finds that a narrative which sounds like " +
  "growth is weak evidence that growth happened. And asking a 16-year-old to write about hardship in a " +
  "form creates pressure to produce a trauma essay, which is why the form does not ask.\n\n" +
  "Why question 6: slide 12 says Intellect is understanding the complex and applying it, not grades, and " +
  "slide 5 says academic performance does not measure leadership potential. But there is still an academic " +
  "block at step 3 of their process, so we may have read it too aggressively. Worth naming the second " +
  "reason too: grades from a village school and a lyceum are not the same measurement, so including them " +
  "is a background proxy as well as an irrelevant one."
);

// ── 6. Two decisions with a deadline ──────────────────────────────

const s6 = pres.addSlide();
s6.background = { color: PAPER };
slideTitle(s6, "Три вопроса, которые влияют на Demo Day");

const rows2 = [
  [7, "До интервью: оценка или доказательства и направление?",
   "Наш выбор: интервьюер видит доказательства и подсказку, что копать, но не видит оценку модели, пока не запишет свою. Причина — эффект якоря."],
  [8, "Письменный вариант презентации в заявке",
   "Распознавание спонтанной казахской речи слишком неточное, чтобы строить на нём оценку. Короткий письменный вариант убирает проблему, а видео остаётся для людей. Это меняет форму заявки, поэтому решение срочное."],
  [9, "Сценарий вместо обучения ИИ-ребёнка",
   "В демо кандидат объяснял школьную тему ИИ-ребёнку. Это не ложится ни на одну из девяти компетенций. Замена — короткий сценарий с конфликтом в команде. Не станет ли это подсказкой к вашему закрытому банку?"],
];
rows2.forEach((row, i) => {
  const y = 1.55 + i * 1.62;
  disc(s6, 0.62, y + 0.06, row[0]);
  s6.addText(row[1], {
    x: 1.25, y, w: 11.4, h: 0.4,
    fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true,
  });
  s6.addText(row[2], {
    x: 1.25, y: y + 0.45, w: 11.4, h: 0.85,
    fontFace: BODY, fontSize: 13.5, color: "44443F", margin: 0, isTextBox: true,
  });
});
s6.addText("Вопрос 8 — с дедлайном: он меняет то, что кандидат заполняет.", {
  x: 0.62, y: 6.55, w: 12.1, h: 0.4,
  fontFace: BODY, fontSize: 14, italic: true, color: RUST, margin: 0, isTextBox: true,
});
s6.addNotes(
  "Why question 7: this tests our whole premise. Our design hides the AI rating from the interviewer " +
  "until they record their own, because an interviewer who sees 'high' before the conversation tends to " +
  "find high. If they actually want a single number to sort by before the interview, we need to hear it " +
  "now rather than in November.\n\n" +
  "Why question 8: it is the only item here that changes something on their side, so it has the longest " +
  "lead time. We will not let a rating depend on a Kazakh transcript, because error rates on spontaneous " +
  "speech are high enough that the noise would concentrate on rural applicants with cheap microphones. " +
  "Asking for a short written version removes the dependency instead of patching it.\n\n" +
  "Why question 9: do not pitch the scenario. Describe it in one sentence and then ask the question that " +
  "would kill it, which is test-bank leakage. A teamwork conflict scenario sits close to a situation in " +
  "their closed bank, so it could become coaching material for the next cohort. If they are interested, " +
  "the real ask is whether Talent Craft will co-author or review it."
);

// ── 7. Close ──────────────────────────────────────────────────────

const s7 = pres.addSlide();
s7.background = { color: INK };
s7.addText("Что нам нужно сегодня", {
  x: 0.9, y: 0.75, w: 11.5, h: 0.8,
  fontFace: HEAD, fontSize: 34, bold: true, color: PAPER, margin: 0, isTextBox: true,
});

const asks = [
  ["Ответы на вопросы 3, 4 и 5", "Они уже работают в коде. Менять сейчас — день, в ноябре — неделя."],
  ["Решение по вопросу 8", "Письменный вариант презентации меняет форму заявки, поэтому нужен ответ раньше остальных."],
  ["Кто владелец методологии", "Вы или Talent Craft? Если решение не за вами, нам нужен один звонок с владельцем до 5 октября."],
];
asks.forEach((a, i) => {
  const y = 1.85 + i * 1.12;
  s7.addShape(pres.ShapeType.ellipse, {
    x: 0.92, y: y + 0.09, w: 0.16, h: 0.16,
    fill: { color: LIME }, line: { color: LIME, width: 0 },
  });
  s7.addText(a[0], {
    x: 1.32, y, w: 11, h: 0.38,
    fontFace: HEAD, fontSize: 19, bold: true, color: PAPER, margin: 0, isTextBox: true,
  });
  s7.addText(a[1], {
    x: 1.32, y: y + 0.4, w: 11, h: 0.5,
    fontFace: BODY, fontSize: 14, color: "AFAFA9", margin: 0, isTextBox: true,
  });
});

s7.addShape(pres.ShapeType.roundRect, {
  x: 0.9, y: 5.5, w: 11.55, h: 1.25, rectRadius: 0.08,
  fill: { color: "232320" }, line: { color: "232320", width: 0 },
});
s7.addText("Мы хотим, чтобы вы с чем-то из этого не согласились.", {
  x: 1.25, y: 5.68, w: 10.9, h: 0.4,
  fontFace: HEAD, fontSize: 20, bold: true, color: LIME, margin: 0, isTextBox: true,
});
s7.addText(
  "В вашей же презентации написано: комиссия должна иметь право сказать «нет» алгоритму. " +
  "Резюме решений пришлём в тот же день.",
  {
    x: 1.25, y: 6.12, w: 10.9, h: 0.5,
    fontFace: BODY, fontSize: 14, color: "AFAFA9", margin: 0, isTextBox: true,
  },
);
s7.addNotes(
  "Why this slide closes the deck: a call where the client approves everything is a failed call. Their " +
  "own criteria say the committee must be able to disagree with the algorithm, so inviting disagreement " +
  "is both honest and on-message.\n\n" +
  "The ownership question matters more than it sounds. If this person is relaying to Talent Craft, " +
  "questions 3, 4 and 5 will not get answered today, and they block work in the first week of Stage 2.\n\n" +
  "Send a one-page written summary of what was decided the same day and ask them to correct anything " +
  "recorded wrong. Decisions made on a call and never written down get re-litigated in November."
);

pres.writeFile({ fileName: "docs/inVisionU_call_questions.pptx" }).then((f) => {
  console.log("wrote", f);
});
