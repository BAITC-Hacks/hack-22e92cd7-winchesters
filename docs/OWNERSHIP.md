# Кто что делает

> Два разработчика, задачи из [STAGE2_TASK_BOARD.md](STAGE2_TASK_BOARD.md).
> **Алмас** (@m4rk1sov): платформа. **@raursq**: AI.
> Ревьюеры по файлам: [.github/CODEOWNERS](../.github/CODEOWNERS).
>
> Недели: **W0** = 20–26 сен · **W1** = 27 сен – 3 окт · **Demo Day 1–3 окт** · W2+ = с 5 окт.
> 🔴 = demo-critical.

## Правило

- **Алмас**: данные хранятся, доступ защищён, API отдаёт, UI показывает.
- **@raursq**: что модель извлекает, как оценивает и как доказать, что это честно.

Если задача про таблицы, auth, роутеры, фронт, Docker или CI, она у Алмаса. Если про промпты,
пайплайн, рубрику, eval или fairness-статистику, она у @raursq.

---

## День 1: вместе

| # | Задача | Результат |
|---|---|---|
| 0 | 🔴 **LED-03**: JSON-схема ledger'а + фикстура | `backend/ledger/schema.py` + `backend/ledger/fixtures/`. Все колонки ledger-таблиц Алмаса берутся отсюда. Дальше оба работают против фикстуры и никого не ждут. |

---

## Алмас

Делать сверху вниз.

### W0

| # | Задача | Что | Разблокирует |
|---|---|---|---|
| A1 | 🔴 **FND-04** (PR 1) | engine, `backend/db/`, Alembic, таблицы `applicants`, `artifacts`, `users` + импорт 16 записей. Убить `_candidates_cache`, `_users`. PK аппликанта — **UUID**, `c-001` → `legacy_ref`. | всё ниже |
| A2 | 🔴 **FND-04** (PR 2) | **Вся остальная схема** одной миграцией: `model_runs`, `rubric_versions`, `prompt_versions`, `evidence_items`, `ratings`, `competency_scores`, `committee_overrides`, `audit_log`, `protected_attributes`, `consents`. Колонки из LED-03. Append-only через триггеры. Предложить сигнатуру хука `llm.py → model_runs`. | **LED-04 у @raursq** |
| A3 | 🔴 **FND-05** | Auth: JWT + argon2, роли applicant/interviewer/committee/admin, guard на каждом роутере, CORS allowlist, демо-аккаунт только при `DEMO_MODE`. | A9, INP-03 |
| A4 | 🔴 **LED-05** | Разбить `dashboard/page.tsx` на Committee Card / Interviewer Brief / Growth Map / Fairness Audit, рендер из фикстуры. **Сделать до того, как кто-то ещё тронет дашборд.** | A13 |
| A5 | 🔴 **FND-04** (PR 3) | Старые кэши → `model_runs` (generic `output` JSON + `status`, `failed` вместо нуля). Убить `_score_cache`, `_baseline_cache`, `_video_cache`. **Только после того, как смержены LED-01/02 у @raursq**: не сохранять то, что он удаляет. | — |
| A6 | 🔴 **COM-01** | Override-ledger: append-only бэкенд + UI, обязательный reason code, AI-строка никогда не перезаписывается. | — |
| A7 | 🔴 **FAIR-02** | Убрать панель fairness-by-recommendation, поставить плейсхолдер. | — |
| A8 | 🔴 **FAIR-01** | Переключатель Blind/Informed + Context strip (UI). | — |

### W1

| # | Задача | Что | Ждёт |
|---|---|---|---|
| A9 | 🔴 **INP-03**, половина про хранение (PR 4) | Feynman-сессии в БД, привязка к пользователю, лимит попыток. Убить `_sessions` и `_score_cache` в `feynman.py`. | A3 |
| A10 | 🔴 **FND-07** | UUID везде наружу + PII-регексы (KZ-телефоны, ИИН, email, хэндлы) на все текстовые поля. | A1 |
| A11 | 🔴 **INP-01** | Written presentation как артефакт + поле формы; видео возвращает `status=no_transcript`, а не мок. | A1 |
| A12 | 🔴 **LED-11** | Подключить карточку комитета к реальному ledger API (`routers/ledger.py`). | LED-04 (@raursq), LED-06 (дизайнер) |
| A13 | 🔴 **COM-03** | Interviewer pre-brief из ledger'а, печать + телефон. | A12, COM-02 (дизайнер) |
| A14 | 🔴 **LED-12** | Сидинг демо-данных; каждый клик на демо читает из БД; ни одного live-вызова модели без fallback. | A12 |
| A15 | 🔴 **CAND-03** | Рендер Growth Map на 3 языках + кнопка «это не про меня». | CAND-02 (@raursq) |

### W2+

FND-08 (Batch API + стоимость в `model_runs`) → COM-07 (Compare + очереди) → COM-04 (Decision Memo PDF) →
COM-06 (pre-brief v2) → FND-09, часть про consents + retention job → FND-11 (нагрузочный тест на 500,
**можно на Go**) → FND-10 (Postgres в KZ, только если хостит inVision).

---

## @raursq

Делать сверху вниз.

### W0

| # | Задача | Что | Разблокирует |
|---|---|---|---|
| R1 | 🔴 **LED-01** | Удалить все демографические прокси из пути скоринга; school/region/language/Foundation → `protected_attributes`. | A5, LED-04 |
| R2 | 🔴 **LED-02** | Удалить AI-text authenticity score из API и UI. | A5 |
| R3 | 🔴 **LED-04** (L) | Двухстадийный пайплайн: extraction → проверка подстрокой → BARS-рейтинг → уровень → скор. Код в `backend/ledger/`. **Начать против фикстуры сразу**, в БД включить после A2. | **A12 у Алмаса** и почти весь W1 |

### W1

| # | Задача | Ждёт |
|---|---|---|
| R4 | 🔴 **LED-08** ATOLA mapper + water checklist | R3 |
| R5 | 🔴 **LED-09** contrastive-поле в схеме рейтинга | R3 |
| R6 | 🔴 **LED-10** компетенции 8 и 9 только как флаги | R3 |
| R7 | 🔴 **CAND-02** генерация Growth Map + release gate | R3 → **разблокирует A15** |
| R8 | 🔴 **INP-03**, половина про промпты: квиз читает `<lesson>`, один форк Teamwork/Values, кэш транскрипта | A9 |
| R9 | 🔴 **FAIR-05** eval harness v0 + страница результатов | R3, FAIR-04 (дизайнер) |
| R10 | 🔴 **FAIR-06** swap-and-rescore (эндпоинт в `routers/fairness.py` + кнопка) | R3 |
| R11 | 🔴 **FAIR-07** fairness-аудит по атрибутам + панель | R1 |
| R12 | CAND-04 leak guard (один публичный item) | R7 |
| R13 | INP-02 ipsative-профиль + матрица claimed-vs-demonstrated | R3 |
| R14 | INP-04 определение языка с учётом code-switching + манифест исключённых признаков | R1 |

### W2+

LED-13 (все 9 компетенций) → FAIR-08 (пре-регистрация, **до** открытия исторических данных) → FAIR-09 →
LED-14 → INP-05 → FND-09, часть про NER → FAIR-10 → LED-15 → FAIR-11 → INP-06 → INP-07 → CAND-08 →
COM-10 → FAIR-12 → FAIR-13.

> **Если @raursq не успевает:** FAIR-07 (бутстрап-статистика, без LLM) и FAIR-13 (пересчёт скоров из
> сохранённых рейтингов) переходят к Алмасу. Переносить сначала их.

---

## Кто кого ждёт

| Ждёт | Чего | Как не простаивать |
|---|---|---|
| @raursq (LED-04) | схему БД от Алмаса (A2) | работать против фикстуры LED-03; БД подключается одной строкой в конце |
| Алмас (A5, кэши) | LED-01/02 от @raursq | делать A3, A4 |
| Алмас (A12, карточка) | LED-04 от @raursq | UI уже рендерится из фикстуры после A4 |
| Алмас (A15) | CAND-02 от @raursq | — |
| Оба, `feynman.py` | один файл на двоих | сначала Алмас (A9, хранение), потом @raursq (R8, промпты) |
| Оба, `llm.py` | хук записи в `model_runs` | Алмас предлагает сигнатуру в A2, @raursq одобряет и сам вставляет вызов |

---

## Процесс

- Ветка = ID задачи: `fnd-04-core-tables`, `led-04-pipeline`. ID в заголовке PR.
- Файл чужой зоны (см. CODEOWNERS) правишь только через PR с ревью владельца.
- Смержил задачу: добавь ID в `done` в `docs/research/task_board_source.json` и перегенерируй через
  `build_board.py`. `STAGE2_TASK_BOARD.md` руками не править.
- 10 минут синка в день, только о контрактах: схема ledger'а, API, хук `llm.py`.
- Чтобы CODEOWNERS был обязательным, а не рекомендацией: владелец репо включает в branch protection
  для `main` опцию **Require review from Code Owners**.
