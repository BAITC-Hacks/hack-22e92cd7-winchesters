"use client";

// Scenarios (INP-04): the applicant talks a real situation through with a
// conversation partner, in English, Russian or Kazakh. The applicant never
// sees which competency a scenario is about, nor a level afterwards.

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { SiteNav } from "@/components/site/SiteNav";
import { SiteFooter } from "@/components/site/SiteFooter";
import { ProvisionalChip } from "@/components/simulation/SimulationLabels";
import { api } from "@/lib/api";
import type { ScenarioCatalogue, ScenarioLanguage, ScenarioMessage } from "@/lib/types";
import { useAuth } from "@/lib/useAuth";

type Phase = "choose" | "talk" | "done";

const LANGUAGE_NAMES: Record<ScenarioLanguage, string> = { en: "English", ru: "Русский", kk: "Қазақша" };

const UI: Record<ScenarioLanguage, Record<string, string>> = {
  en: {
    title: "Scenarios",
    lead: "Real-Life",
    how: "How it works",
    intro:
      "Talk a real situation through with a conversation partner. There are no right answers: we want to hear what you would actually do, and about a time you did something similar.",
    step1: "Choose a language and a situation",
    step2: "Answer in 3 to 5 short replies",
    step3: "Finish: the committee reads your answers",
    language: "Language",
    choose: "Choose a situation",
    start: "Start",
    you: "You",
    placeholder: "Your answer…",
    send: "Send",
    finish: "Finish",
    finishHint: "You can finish after 3 replies.",
    doneTitle: "Thank you",
    doneText: "Your answers are saved. The committee reads them together with your application.",
    back: "Back to home",
    needApp: "Submit your application first: scenarios come after it.",
    demo: "Demo mode: the conversation partner follows a script.",
  },
  ru: {
    title: "Сценарии",
    lead: "Жизненные",
    how: "Как это устроено",
    intro:
      "Обсудите реальную ситуацию с собеседником. Правильных ответов нет: нам важно, как вы поступили бы на самом деле, и был ли у вас похожий опыт.",
    step1: "Выберите язык и ситуацию",
    step2: "Ответьте 3–5 короткими сообщениями",
    step3: "Завершите: комиссия прочитает ваши ответы",
    language: "Язык",
    choose: "Выберите ситуацию",
    start: "Начать",
    you: "Вы",
    placeholder: "Ваш ответ…",
    send: "Отправить",
    finish: "Завершить",
    finishHint: "Завершить можно после 3 ответов.",
    doneTitle: "Спасибо",
    doneText: "Ваши ответы сохранены. Комиссия прочитает их вместе с вашей заявкой.",
    back: "На главную",
    needApp: "Сначала отправьте заявку: сценарии идут после неё.",
    demo: "Демо-режим: собеседник следует сценарию.",
  },
  kk: {
    title: "Сценарийлер",
    lead: "Өмірлік",
    how: "Бұл қалай өтеді",
    intro:
      "Нақты жағдайды әңгімелесушімен бірге талқылаңыз. Дұрыс жауап жоқ: сіз шынымен не істейтініңізді және осыған ұқсас тәжірибеңіз болғанын білгіміз келеді.",
    step1: "Тіл мен жағдайды таңдаңыз",
    step2: "3–5 қысқа жауап беріңіз",
    step3: "Аяқтаңыз: комиссия жауаптарыңызды оқиды",
    language: "Тіл",
    choose: "Жағдайды таңдаңыз",
    start: "Бастау",
    you: "Сіз",
    placeholder: "Жауабыңыз…",
    send: "Жіберу",
    finish: "Аяқтау",
    finishHint: "3 жауаптан кейін аяқтауға болады.",
    doneTitle: "Рақмет",
    doneText: "Жауаптарыңыз сақталды. Комиссия оларды өтініміңізбен бірге оқиды.",
    back: "Басты бетке",
    needApp: "Алдымен өтініміңізді жіберіңіз: сценарийлер одан кейін.",
    demo: "Демо режим: әңгімелесуші сценарий бойынша жүреді.",
  },
};

export default function ScenariosPage() {
  const { user, ready } = useAuth({ requireAuth: true, roles: ["applicant"] });
  const [catalogue, setCatalogue] = useState<ScenarioCatalogue | null>(null);
  const [live, setLive] = useState(true);
  const [language, setLanguage] = useState<ScenarioLanguage>("en");
  const [selected, setSelected] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("choose");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ScenarioMessage[]>([]);
  const [input, setInput] = useState("");
  const [replies, setReplies] = useState(0);
  const [canFinish, setCanFinish] = useState(false);
  const [mustFinish, setMustFinish] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const t = UI[language];

  useEffect(() => {
    if (!ready) return;
    api.scenarios.list().then(setCatalogue).catch((e) => setError(e instanceof Error ? e.message : String(e)));
    api.scenarios.mode().then((m) => setLive(m.live)).catch(() => {});
  }, [ready]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const scenario = catalogue?.scenarios.find((s) => s.id === selected) ?? null;
  const partner = catalogue?.partner_label[language] ?? "";

  async function start() {
    if (!selected) return;
    if (!user?.candidate_id) return setError(t.needApp);
    setError(null);
    setBusy(true);
    try {
      const res = await api.scenarios.start(user.candidate_id, selected, language);
      setSessionId(res.session_id);
      setMessages([{ role: "assistant", content: res.first_message }]);
      setReplies(0);
      setCanFinish(false);
      setMustFinish(false);
      setPhase("talk");
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || !sessionId || busy || mustFinish) return;
    setError(null);
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    try {
      const res = await api.scenarios.chat(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      setReplies(res.replies);
      setCanFinish(res.can_finish);
      setMustFinish(res.must_finish);
    } catch (e) {
      // Nothing was stored: take the message back so it can be resent.
      setMessages((prev) => prev.slice(0, -1));
      setInput(text);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    if (!sessionId) return;
    setError(null);
    setBusy(true);
    try {
      await api.scenarios.finish(sessionId);
      setPhase("done");
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const errorBox = error && (
    <div role="alert" className="mb-6 rounded-xl border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger">
      {error}
    </div>
  );

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <SiteNav />

      {phase === "choose" && (
        <>
          {/* Hero: sizes follow the Figma frame at 80%. */}
          <section className="relative overflow-hidden">
            <img src="/assets/hero/BG.png" alt="" className="pointer-events-none absolute inset-0 h-full w-full object-cover object-right" />
            <div className="relative mx-auto flex max-w-[1728px] items-end justify-between gap-8 px-4 md:px-[4.8vw] lg:min-h-[clamp(420px,24.57vw,472.5px)]">
              <div className="max-w-[39.33vw] py-10 max-lg:max-w-none lg:self-center lg:py-[clamp(40px,3.6vw,69.12px)]">
                <h1 className="text-[clamp(34px,2.85vw,54.72px)] font-bold leading-tight text-ink">
                  {t.lead} <span className="box-decoration-clone bg-accent px-[0.1em]">{t.title}</span>
                </h1>
                <p className="mt-[clamp(18px,1.31vw,25.2px)] max-w-[34em] text-[clamp(16px,1.12vw,21.6px)] text-ink">{t.intro}</p>
                <div className="mt-[clamp(18px,1.31vw,25.2px)] w-fit max-w-full rounded-[16px] border-2 border-line bg-white p-4">
                  <p className="text-[clamp(16px,1.12vw,21.6px)] text-ink">{t.how}</p>
                  <ol className="mt-3 flex flex-col gap-[5px] sm:flex-row">
                    {[t.step1, t.step2, t.step3].map((step, i) => (
                      <li key={step} className="flex flex-col gap-3 rounded-[8px] bg-ink px-4 py-5 sm:max-w-[16em]">
                        <span className="text-[clamp(28px,1.87vw,36px)] font-bold leading-none text-accent">{i + 1}</span>
                        <span className="text-[clamp(13px,0.75vw,14.4px)] leading-snug text-white">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
              <img src="/assets/scenarios/hero-girl.png" alt="" className="hidden w-[26.46vw] max-w-[508.5px] shrink-0 lg:block" />
            </div>
          </section>

          <main className="mx-auto w-full max-w-[1728px] flex-1 px-4 py-[clamp(24px,1.87vw,36px)] md:px-[4.2vw]">
            {errorBox}
            {/* Dark banner with the choice card over its lower part, as in the Figma "Choose a topic" block. */}
            <section className="relative overflow-hidden rounded-[28px] bg-ink">
              <img src="/assets/Dots.png" alt="" className="pointer-events-none absolute inset-x-0 top-0 h-[40%] w-full object-cover opacity-30" />
              <div className="relative flex flex-wrap items-center justify-between gap-4 px-[clamp(20px,2.29vw,43.92px)] pb-[clamp(20px,1.8vw,34.2px)] pt-[clamp(24px,2.56vw,49.32px)]">
                <h2 className="text-[clamp(30px,2.78vw,53.28px)] font-bold leading-none text-accent">{t.choose}</h2>
                <div className="flex flex-col items-end gap-2">
                  <div role="radiogroup" aria-label={t.language} className="flex gap-1 rounded-full bg-white/10 p-1">
                    {(Object.keys(LANGUAGE_NAMES) as ScenarioLanguage[]).map((code) => (
                      <button
                        key={code}
                        type="button"
                        role="radio"
                        aria-checked={language === code}
                        onClick={() => setLanguage(code)}
                        className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
                          language === code ? "bg-accent text-ink" : "text-white/70 hover:text-white"
                        }`}
                      >
                        {LANGUAGE_NAMES[code]}
                      </button>
                    ))}
                  </div>
                  {!live && <span className="text-xs text-white/60">{t.demo}</span>}
                </div>
              </div>

              <div className="relative rounded-[28px] border-2 border-line bg-white p-[clamp(14px,1.12vw,21.6px)]">
                <div className="grid gap-x-[clamp(12px,1.12vw,21.6px)] gap-y-[clamp(14px,1.73vw,33.12px)] lg:grid-cols-3">
                  {catalogue?.scenarios.map((s, i) => {
                    const on = s.id === selected;
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setSelected(s.id)}
                        aria-pressed={on}
                        className={`flex min-h-[clamp(110px,6.34vw,121.5px)] items-center gap-[clamp(12px,0.79vw,15.3px)] rounded-[16px] px-[clamp(18px,1.32vw,25.47px)] py-5 text-left text-ink transition-colors ${
                          on ? "bg-accent" : "bg-muted hover:bg-line"
                        }`}
                      >
                        <span className="text-[clamp(40px,3vw,57.6px)] font-bold leading-none">{i + 1}</span>
                        <span className="text-[clamp(15px,0.99vw,18.9px)] leading-snug">
                          <span className="block font-bold">{s.text[language].title}</span>
                          <span className="mt-1 block">{s.text[language].summary}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={start}
                  disabled={!selected || busy}
                  className="mt-[clamp(14px,1.73vw,33.12px)] h-[clamp(52px,3.19vw,61.2px)] w-full rounded-[16px] bg-ink text-[clamp(20px,1.5vw,28.8px)] font-bold text-accent transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {t.start}
                </button>
              </div>
            </section>
          </main>
        </>
      )}

      {phase !== "choose" && (
      <main className="mx-auto w-full max-w-[960px] flex-1 px-4 py-10 md:px-10 md:py-14">
        {errorBox}

        {phase === "talk" && scenario && (
          <>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h1 className="text-2xl font-bold text-ink">{scenario.text[language].title}</h1>
              <div className="flex items-center gap-2">
                <ProvisionalChip scenario={scenario} />
                {!live && <span className="rounded-full border border-line px-2.5 py-0.5 text-xs text-ink-3">{t.demo}</span>}
              </div>
            </div>

            <div className="rounded-2xl border border-line bg-white p-4 md:p-6">
              <div className="flex max-h-[60vh] flex-col gap-3 overflow-y-auto pr-1">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
                        m.role === "user" ? "bg-accent text-ink" : "border border-line bg-subtle text-ink"
                      }`}
                    >
                      <p className="mb-1 text-xs font-semibold text-ink-2">{m.role === "user" ? t.you : partner}</p>
                      {m.content}
                    </div>
                  </div>
                ))}
                {busy && <p className="animate-pulse text-sm text-ink-3">{partner}…</p>}
                <div ref={endRef} />
              </div>

              <div className="mt-4 flex flex-col gap-2 border-t border-line-soft pt-4 sm:flex-row">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  disabled={busy || mustFinish}
                  rows={2}
                  placeholder={t.placeholder}
                  className="min-h-[52px] flex-1 resize-y rounded-xl border border-line px-4 py-3 text-[15px] text-ink outline-none transition placeholder:text-ink-3 focus:border-ink focus:ring-4 focus:ring-accent/40 disabled:bg-subtle"
                />
                <button
                  type="button"
                  onClick={send}
                  disabled={busy || mustFinish || !input.trim()}
                  className="rounded-full bg-ink px-6 py-3 font-semibold text-accent transition-opacity hover:opacity-90 disabled:opacity-40"
                >
                  {t.send}
                </button>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
              <span className="text-xs text-ink-3">{canFinish ? `${replies} / 5` : t.finishHint}</span>
              <button
                type="button"
                onClick={finish}
                disabled={!canFinish || busy}
                className="rounded-full bg-accent px-6 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-40"
              >
                {t.finish}
              </button>
            </div>
          </>
        )}

        {phase === "done" && (
          <div className="mx-auto max-w-lg rounded-3xl border border-line bg-white p-8 text-center md:p-10">
            <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-accent">
              <svg className="size-7 text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <h1 className="mt-5 text-2xl font-bold text-ink">{t.doneTitle}</h1>
            <p className="mt-2 text-ink-2">{t.doneText}</p>
            <Link href="/" className="mt-6 inline-block rounded-full bg-ink px-6 py-3 font-semibold text-accent hover:opacity-90">
              {t.back}
            </Link>
          </div>
        )}
      </main>
      )}

      <SiteFooter />
    </div>
  );
}
