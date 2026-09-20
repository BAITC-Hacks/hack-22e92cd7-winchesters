# AI Leader ID — Fairness, Explainability and Governance layer (research + proposals)

Scope note: written for the 1-dev + 1-designer team. "Client criteria" refers to the Stage-2 judging criteria: Transparency, Explainability, Bias exclusion ("verifiable on data"), Recommendations to the candidate, Scoring for the committee, Human-in-the-loop, plus Creativity. Every claim tagged [source: url] was opened in this session; [unverified] means I could not open a primary source. Where I could not confirm a statute article number I say "verify article number".

Two facts about the current product drive everything below: (1) the "Fairness Audit" groups by *recommendation category*, so it cannot detect bias by protected attribute; (2) the hand-coded school-type "starting advantage" table (private 75 … village 25) is a demographic proxy that feeds the score. Both must go or be re-purposed; the Ofqual 2020 failure (section 6) is essentially the same design.

---

# Findings

## 1. Fairness measurement the client can actually run (small n, no ground truth)

**1a. Adverse impact ratio (four-fifths rule).** The US Uniform Guidelines (29 CFR 1607.4D) say a selection rate for any group below 4/5 (80%) of the rate for the highest-rate group "will generally be regarded ... as evidence of adverse impact." Crucially for a cohort of hundreds, the same section says smaller differences may still be adverse impact "where they are significant in both statistical and practical terms," and that where numbers are "too small to be reliable," evidence over a longer period or from similar circumstances should be considered [source: https://www.uniformguidelines.com/uniform-guidelines.html]. Watson et al. argue computer scientists have over-abstracted the 4/5 rule; it is a screening heuristic, not the legal test, which also involves business necessity and a "less discriminatory alternative" [source: https://arxiv.org/abs/2202.09519]. Implication: present the 80% line as a *trigger for human review*, never as a pass/fail certificate.

**1b. How NYC operationalises it for scoring tools (directly reusable).** NYC Local Law 144 bias audits compute, for a tool that outputs a score, a "scoring rate" = share of each group scoring above the sample median, then an impact ratio = group rate / highest group rate; categories must include sex, race/ethnicity and intersections; groups under 2% of the data may be excluded from the ratio but their rates must still be reported; audits may use historical or test data (disclosed); the summary must be published and candidates notified at least 10 working days before use [source: https://www.nycbiasaudit.com/] [source: https://www.dlapiper.com/en-us/insights/publications/2026/01/critical-audit-of-nyc-ai-hiring-law-signals-increased-risk-for-employers]. The NY State Comptroller found LL144 enforcement "ineffective": regulators found 1 issue in 32 posted audits where the Comptroller found at least 17 [source: same DLA Piper]. Lesson: a self-published audit is only credible if the method is reproducible from data, which is exactly what "verifiable on data" asks for.

**1c. Which metrics are meaningful without ground truth (no label "became a leader").**
- *Demographic (statistical) parity difference/ratio*: selection rate or mean score independence from the protected attribute; Fairlearn notes it is appropriate "if the input data are known to contain biases" and that it ignores true labels; caveat: coarse [source: https://fairlearn.org/main/user_guide/assessment/common_fairness_metrics.html]. This is the primary Stage-2 metric because labels are absent.
- *Equalized odds / equal opportunity* need a label Y; usable only once the client's anonymised historical data supply committee outcomes (Stage 2), and even then the label encodes past human bias, which Fairlearn flags as the main caveat [source: same].
- *Calibration by group* (P(outcome | score, group) equal across groups) also needs a label; in Stage 2, use committee final ratings or interview BARS levels as a proxy label and check whether AI score s predicts the same human level for rural vs city candidates. [inference from the definitions above]
- *Rank-based exposure*: Singh & Joachims define fairness of exposure in rankings — the framework can express demographic parity, disparate treatment (exposure proportional to merit) and disparate impact constraints on ranked lists [source: https://arxiv.org/abs/1802.07281]. For pre-selection, the actionable version is "share of each group in the top-k / interview-invite list vs share in the applicant pool," reported at the client's actual cut-off k.
- *Small-sample handling*: Fairlearn warns granular groups have small n and trends "may be due to random chance," and points to confidence-interval estimation [source: same Fairlearn]. Use bootstrap CIs on every ratio and show them; a wide CI crossing 0.8 is "inconclusive," not "fair".
- *Differential item functioning (DIF) for the ipsative test*: forced-choice/ipsative data need Thurstonian IRT to yield inter-person comparable scores; DIF ("differential statement functioning") methods exist for multidimensional forced-choice items [source: https://www.sciencedirect.com/science/article/pii/S2405844024029153 (via search summary)] [source: https://journals.sagepub.com/doi/10.1177/0146621620965739 (abstract via search; page blocked)] — [partly unverified; article bodies not opened]. This belongs to the methodology owner (Talent Craft); the team can offer a per-block DIF screen by language/region as a Stage-2 service, not a demo item.

**1d. Presentation for a non-technical committee.** Use one visual language: for each protected attribute, a horizontal bar per group showing the impact ratio with a CI whisker and a single vertical 0.8 reference line, colour only as "review needed / OK / not enough data" (three states, with n printed). Show *mean-score gap in points* alongside ratios because committees think in points. The design should mirror NYC's published audit tables (selection/scoring rate, impact ratio, n) so it reads like a regulator's document rather than a dashboard widget. [design inference]

## 2. Counterfactual / perturbation bias testing for LLM scorers

State of the art is *matched-guise / counterfactual probing*: hold content fixed, vary a demographic marker, measure the change.
- Hofmann et al. (Nature 2024) used matched guise probing: LLMs judged AAE-dialect text as less employable and more criminal than semantically matched SAE text, with covert stereotypes "more negative than any human stereotypes ... ever experimentally recorded," and alignment/RLHF did not remove the dialect prejudice, only concealed overt bias [source: https://arxiv.org/abs/2403.00742]. Directly relevant to "manner of speech."
- A 2026 follow-up shows dialect bias is "significantly exacerbated" when items are compared *side by side* versus in isolation, and explicitly flags "contexts in which models are used to rank candidates" [source: https://arxiv.org/abs/2605.24384]. Design consequence: score candidates one at a time with an absolute rubric; never ask the LLM to rank or compare two candidates.
- Tamkin et al. (Anthropic) varied demographics across 70 decision scenarios and measured a discrimination score (logit difference vs a baseline); the most effective prompt mitigations were adding "it is illegal to discriminate" and instructions to "ignore demographics," which brought discrimination scores below 0.2 while keeping >0.9 correlation with original decisions [source: https://arxiv.org/abs/2312.03689] [source: https://www.alphaxiv.org/overview/2312.03689]. The dataset/prompts are public. Reusable: the exact mitigation strings and the "vary demographics, measure delta" protocol.
- Bloomberg ran GPT-3.5 resume ranking 1,000 times; names distinct to Black women were top-ranked for software engineering only 11% of the time, 36% less often than the best group, i.e. below the 4/5 benchmark; Asian-women names ranked top 17.2% vs Black men 7.6% [source: https://www.bloomberg.com/graphics/2024-openai-gpt-hiring-racial-discrimination/ (blocked on fetch; numbers from search summary — treat as [partly unverified]); reproduction materials at https://github.com/BloombergGraphics/2024-openai-gpt-hiring-racial-discrimination]. "Silicon Ceiling" (GPT-3.5, 32 names × 10 occupations × 3 tasks) found generated resumes for women had less experience and Asian/Hispanic names got "immigrant markers, such as non-native English" [source: https://arxiv.org/abs/2405.04412].
- LLM-judge bias taxonomies: MT-Bench identified position, verbosity and self-enhancement bias and proposed swapping positions, few-shot, CoT and reference-guided judging as mitigations [source: https://arxiv.org/abs/2306.05685]. CALM (ICLR 2025) formalises 12 biases — position, verbosity, compassion-fade, bandwagon, distraction, fallacy-oversight, authority, sentiment, diversity, chain-of-thought, self-enhancement, refinement-aware — measured as a *robustness rate* (does the judgement survive a principle-guided perturbation); ChatGPT's fallacy-oversight robustness was 0.566; case studies show judges hacked with fake citations and emotional framing [source: https://llm-judge-bias.github.io/] [source: https://arxiv.org/abs/2410.02736]. "Humans or LLMs as the Judge" perturbs answers (misinformation, gender, authority, beauty) and reports an attack success rate = share of cases where the perturbation flips the judgement [source: https://aclanthology.org/2024.emnlp-main.474.pdf].
- Manner of speech specifically: research on speech LLMs reports "fluency bias" — judges reward polish over substance and disfluent transcripts get lower quality ratings [source: https://arxiv.org/pdf/2603.16941 (search summary only) — [unverified]]. Combine with Liang et al.: seven GPT detectors misclassified more than half of 91 TOEFL essays by non-native writers as AI-generated (one detector ~98%) while classifying >90% of US 8th-grade essays correctly, because detectors reward low perplexity/simple vocabulary; prompting ChatGPT to enrich vocabulary flipped the labels [source: https://www.sciencedaily.com/releases/2023/07/230710113921.htm] [source: https://arxiv.org/abs/2304.02819]. This is a direct warning about the product's stylometry-based "authenticity score": low TTR/short sentences are what a rural Kazakh speaker writing in a second language produces.

**Reusable recipe (bias probe suite).** For each candidate artefact (essay, transcript, Feynman chat): generate K counterfactual variants that change only a protected marker — name (Kazakh/Russian/neutral), region tag (Almaty vs Kyzylorda oblast village), school type, language of the text (KZ↔RU↔EN translation), and "manner of speech" (inject disfluencies "ээ… ну…", grammar errors, code-switching, remove polish) — re-score with identical prompts, and report the delta per dimension. Metric = CALM-style robustness rate (share of variants whose 3-level BARS rating is unchanged) plus mean signed delta. The tolerance should be set from the model's own *re-scoring noise* (same text, same prompt, N runs): a counterfactual delta is a flag only if it exceeds the noise band.

## 3. Language fairness (Kazakh vs Russian vs English)

- Zhou et al. 2026 (Cambridge): across 23 languages, LLM judges and reward models assign systematically different scores to semantically identical content, ~0.4–0.5 points on a 1–5 scale; lower-resource languages get *higher* scores (reward-model Spearman ρ = −0.81 with resource level); >90% pairwise accuracy hides "up to 43%" differences in acceptance rate at a global threshold; per-language offset calibration cut the gap ~61%; language-ID-based calibration is vulnerable to code-switching (44% mis-ID) [source: https://arxiv.org/html/2607.14480]. Two consequences: (i) a single 70/50 threshold across KZ/RU/EN is indefensible; (ii) code-switched Kazakh-Russian text (common among applicants) breaks per-language normalisation unless language is a *declared* field, not detected.
- First-language bias in LLM essay scoring (Gemma-3-27B on TOEFL11, 12,100 essays): systematic offsets by L1, German +0.55, Japanese/Korean −0.34, stable across proficiency bands; the authors' recommendation is an "L1-disaggregated fairness audit rather than relying on overall agreement figures alone" [source: https://arxiv.org/html/2607.14605].
- KazMMLU: 23,000 questions; GPT-4o 76.9% on Kazakh, DeepSeek V3 81.8% on Russian; models "perform slightly better in Russian than in Kazakh"; open models ~55%; LLMs score higher when the *instruction* is in English even with Kazakh content [source: https://arxiv.org/html/2502.12829v1]. Implication: write rubric/system prompts in English, keep the candidate's text in its original language.
- Whisper WER on spontaneous Kazakh is 31–60% (from the shared brief; not re-verified here) — so any transcript-derived metric for Kazakh video must be either gated or labelled as low-confidence.

**Which mitigations are defensible.**
1. *Score in source language, English rubric, explicit "ignore grammar, spelling, dialect and fluency; assess only the behavioural indicator" instruction* — supported by Tamkin's "ignore demographics" result and KazMMLU's English-instruction finding. Effort S. Necessary but not sufficient (Hofmann shows instructions don't remove covert dialect bias).
2. *Per-language calibration* (language-specific offset or z-scoring within declared language) — supported by Zhou et al.; requires declared language; do not infer. Effort S–M. Needs the Stage-2 historical data for robust offsets; before Oct 3 show it on synthetic data.
3. *Translate-then-score with back-translation check* — no direct evidence found for rubric grading; risk: translation smooths dialect and "manner of speech" markers away (which is arguably what you want for fairness, but it also removes authentic voice). Use as one leg of an ensemble, not alone. [inference]
4. *Cross-lingual consistency check (ensemble)*: score original + machine translation into a pivot language (English) with the same rubric; report agreement; flag disagreement > 1 BARS level for human review. This is the most demo-able, innovative feature and is grounded in (i) Zhou et al. per-language bias and (ii) the MT-Bench recommendation of reference/ensemble judging [sources above]. Effort M.
5. *Per-language stylometry thresholds* (already partly in the product) — keep, but never let a stylometric "authenticity" flag lower a competency score (Liang et al.).

## 4. Explainability formats for high-stakes decisions

- NIST's four principles of explainable AI: Explanation (deliver evidence or reasons), Meaningful (understandable to the intended user), Explanation Accuracy (correctly reflects the process that produced the output), Knowledge Limits (operate only within designed conditions and sufficient confidence) [source: https://nvlpubs.nist.gov/nistpubs/ir/2021/nist.ir.8312.pdf (PDF opened; principle definitions taken from the NIST search summary)]. "Knowledge limits" is the standard's authority for showing uncertainty and for abstaining (e.g., Kazakh transcript too noisy → no Communication score).
- Counterfactual explanations (Wachter, Mittelstadt, Russell): "the smallest change to the world that can be made to obtain a desirable outcome"; three aims — understand, contest, alter future outcome — without disclosing model internals [source: https://arxiv.org/abs/1711.00399]. This is the theoretical basis for a candidate-facing "what would need to be different" sentence that does not reveal the item bank or weights.
- Miller's social-science review argues XAI should build on how humans explain (contrastive, selective, social) [source: https://arxiv.org/abs/1706.07269 — abstract confirms the argument; the specific properties are from the paper body, [partly unverified]].
- EU AI Act Article 86 gives an affected person the right to "clear and meaningful explanations of the role of the AI system in the decision-making procedure and the main elements of the decision taken" [source: https://artificialintelligenceact.eu/article/86/]. Article 14(4)(c) requires that overseers can "correctly interpret the high-risk AI system's output" and (b) remain aware of automation bias [source: https://artificialintelligenceact.eu/article/14/].
- Model Cards (Mitchell et al.) prescribe intended use, factors, metrics, evaluation data, quantitative analyses *disaggregated* by demographic/cultural groups and intersections, ethical considerations, caveats [source: https://arxiv.org/abs/1810.03993].

Formats that follow: (a) indicator-level rating with a verbatim quoted span as evidence (Explanation + Accuracy); (b) "not found" list — indicators the model looked for and did not observe, phrased as absence-of-evidence, not presence-of-weakness (Knowledge Limits; also anti-"water" transparency); (c) confidence tag per indicator driven by transcript quality, text length, language, and re-score variance; (d) contrastive sentence: "Rated Normal rather than High because no example of distributing tasks or resolving conflict was present" — this exposes the BARS anchor (already public) not the test bank; (e) committee override with reason, stored in the log (Article 14(4)(d) "disregard, override or reverse").

Candidate-facing safety: give BARS-anchored development advice per competency (the 9 competencies and 3-level logic are public per the brief) and never surface ipsative item text, item scores, weights or cut-offs (closed). Counterfactuals stated at the behaviour level ("show a concrete result you measured") reveal nothing about the bank.

## 5. Governance and law

**EU AI Act (voluntary alignment).** Annex III point 3(a) lists "AI systems intended to be used to determine access or admission or to assign natural persons to educational and vocational training institutions at all levels" as high-risk [source: https://artificialintelligenceact.eu/annex/3/]. Applicable obligations: Article 12 — automatic logging over the system lifetime to identify risk situations and support monitoring [source: https://artificialintelligenceact.eu/article/12/]; Article 14(4) — overseers must understand capacities/limits, remain aware of automation bias, interpret output, be able to "disregard, override or reverse," and stop the system [source: https://artificialintelligenceact.eu/article/14/]; Article 26 (deployer) — competent trained humans with authority, input data "relevant and sufficiently representative," keep logs at least six months, inform affected natural persons that they are subject to a high-risk AI system [source: https://artificialintelligenceact.eu/article/26/]; Article 27 — fundamental rights impact assessment with six elements: process description, period/frequency, affected groups, specific harm risks, human oversight measures, and measures if risks materialise including complaint mechanisms [source: https://artificialintelligenceact.eu/article/27/]; Article 86 — right to explanation [source above]. Timeline: the Digital Omnibus (Regulation (EU) 2026/1744) deferred Annex III high-risk obligations from 2 Aug 2026 to 2 Dec 2027 [source: search summary of https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/ and https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-high-risk-deadline-omnibus-20260/ — [partly unverified], pages not opened]. Pitch line: "We built to the EU's admissions high-risk standard before the EU itself requires it."

**Kazakhstan.**
- Law "On Artificial Intelligence" No. 230-VIII, signed 17 Nov 2025, in force 18 Jan 2026: risk tiers minimal/medium/high and separate autonomy levels; high-risk owners must manage risk continuously, ensure security/reliability, keep documentation, provide user agreements; individuals may receive explanations of AI decisions affecting them, request information on underlying data, object to automated processing, and decline AI interaction unless legally required; bans on manipulation, exploiting age/disability vulnerability, social scoring, emotion detection without consent, discriminatory biometric classification [source: https://www.levellers.ai/what-is/ai-regulation-kazakhstan] [source: https://www.ey.com/en_kz/technical/tax-alerts/2025/12/law-on-artificial-intelligence-kazakhstan]. Note the "emotion detection without consent" ban: do not build facial/voice emotion features. Article numbers for the rights provisions: verify article number (GRATA cites Art. 17.2/17.3 for autonomy classification and prohibitions [source: https://gratanet.com/publications/digital-compliance-2026-conflicts-among-the-digital-code-artificial-intelligence-and-personal-data-laws-in-kazakhstan?region=6]).
- Digital Code No. 255-VIII, enacted 9 Jan 2026, effective 11 Jul 2026: for "fully automated decisions" individuals have the right to be notified that algorithmic systems were applied, to an explanation of "key factors and criteria" (excluding algorithms and source code), to request human review where decisions have legal consequences, and to dispute resolution [source: https://www.kinstellar.com/news-and-insights/detail/4081/the-year-of-digitalisation-and-ai-in-kazakhstan-new-regulations]. Because AI Leader ID is *decision support*, not a fully automated decision, the cleanest compliance posture is to design so it can never become one (no auto-reject path; every screen-out is committee-confirmed).
- Law "On Personal Data and their Protection" No. 94-V (21 May 2013): consent must be written/electronic and specify operator, subject, validity period, third-party and cross-border transfer, and data categories; personal data databases must be stored in Kazakhstan; cross-border transfer requires adequate protection or consent; biometric data (physiological features enabling identification) is personal data, and use of technological means to collect biometrics/identify persons requires consent or a legal basis [source: https://www.dlapiperdataprotection.com/?t=law&c=KZ]. Consent is given by "the subject or his (her) legal representative" (Article 8 — verify article number; search summary of the law text). For 16–18-year-old applicants, obtain parental/legal-representative consent alongside the applicant's; I found no explicit statutory age threshold [unverified]. Video of a face is biometric-capable data: store video outside the model pipeline, transcribe, and delete or minimise; do not run face analysis. The brief's "Kazakhstan personal-data law" constraint plus data localisation means Anthropic API calls (data leaves KZ) need PII masking (already present) and explicit consent text covering cross-border processing — verify with the client's legal team.
- Standards: ISO/IEC TR 24027:2021 covers bias in AI-aided decision making across the lifecycle with measurement techniques [source: https://www.iso.org/standard/77607.html]; ISO/IEC 42001:2023 is the certifiable AI management system standard (risk management, AI impact assessment, lifecycle) [source: search summary https://www.iso.org/standard/42001 — [partly unverified]]; NIST AI RMF 1.0 (Jan 2023, voluntary) has Govern/Map/Measure/Manage functions [source: https://airc.nist.gov/airmf-resources/airmf/] [source: https://www.paloaltonetworks.com/cyberpedia/nist-ai-risk-management-framework]. Lightweight alignment = a one-page model card (Mitchell) + a one-page impact assessment structured on Article 27's six elements + a "Measure" table of the metrics in section 1.

## 6. Lessons from failures

- **HireVue (Jan 2021)** dropped facial-expression analysis; the CEO said it added ~0.25% to model accuracy and "wasn't worth the incremental value" given bias concerns; EPIC had filed an FTC complaint in 2019; the ORCAA audit flagged possible accent-related bias and disproportionate flagging of minority candidates who gave brief answers [source: https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/]. Rules: no non-verbal/appearance signals; short answers ≠ weak answers; accents must be tested explicitly.
- **Amazon (2014–2017)** trained on 10 years of mostly male résumés; penalised "women's" and all-women colleges; scrapped after failing to guarantee neutrality [source: https://www.technologyreview.com/2018/10/10/139858/amazon-ditched-ai-recruitment-software-because-it-was-biased-against-women/]. Rule: do not learn from past admit decisions as the target without a bias audit of the labels; keyword features are proxies.
- **Ofqual 2020**: grades set from a school's historical distribution; small cohorts (≤5 entirely, 6–14 partly teacher-assessed) were exempt and were more common in private schools; ~36% of A-level grades were one grade below teacher prediction, private schools gained more top grades, no individual appeal existed; reversed on 17 Aug 2020 [source: https://en.wikipedia.org/wiki/2020_United_Kingdom_school_exam_grading_controversy]. Rules: never let a school- or region-level prior move an individual's score; every individual must have an appeal; small groups need special handling, not silent exemption. The product's school-type "starting advantage" table is the Ofqual mechanism in miniature.
- **NYC LL144 enforcement gap** (above): a published audit nobody checks is theatre; make the audit reproducible (code + data hash) [source: DLA Piper above].
- **GPT detectors vs non-native writers** (Liang): stylometric AI-detection is a proxy for language background [source above]. Rule: authenticity flags inform interviewers; they never subtract points.

## 7. Creative but defensible fairness features (finding, not filtering)

Table stakes for any credible pitch: per-attribute impact ratios with CIs; counterfactual name/region swap test; committee override with logged reason; model card; no auto-reject. Uncommon but achievable: cross-lingual consistency check; "not found" evidence lists; re-score noise band as the tolerance; fairness gate in CI that blocks deploy; candidate contest flow. Genuinely novel for a hackathon: opportunity context shown to humans but provably not fed to the model (with a live "blind vs. informed" toggle showing identical AI scores); disparate-impact monitoring across the *funnel* (applied → AI pre-score → invited → admitted) with the AI stage isolated; red-team log with attack success rates on your own scorer; language-declared calibration with code-switch detection routed to human review.

---

# Proposals

## F1. Protected-attribute Fairness Audit (replace the current one)
- Category: metric
- What: Group by declared attributes — region (oblast; urban/rural), school type, essay/video language, Foundation-eligibility flag (income proxy), plus intersections (rural × Kazakh-language). For each: n, mean overall and per-competency score, "scoring rate" (share above cohort median, NYC method), impact ratio vs best group, 1,000-sample bootstrap 95% CI, share in top-k at the committee's cut-off. Three visual states: OK (ratio ≥ 0.8 and CI excludes lower), Review (ratio < 0.8 or CI crosses 0.8), Not enough data (n < 10 or < 2% of pool, rates still shown). One reference line at 0.8. Exportable as PDF "Bias audit summary" with method text, date, data hash.
- Why: "Bias exclusion — verifiable on data"; also Scoring for the committee. Mirrors a regulator's published audit format (LL144).
- Novelty: table stakes
- Effort: S–M; when: before Oct 3 (synthetic 16 → generate ~200 synthetic profiles to make CIs visible), rerun on real data in Stage 2
- Risks: with hundreds of applicants, CIs will be wide; say so on screen. Attribute data must be declared/consented, not inferred.
- Confidence: high
- Sources: uniformguidelines.com; nycbiasaudit.com; fairlearn.org; arxiv 2202.09519

## F2. Counterfactual Bias Probe button ("Re-score with swapped markers")
- Category: probe
- What: On a candidate's detail panel, a button generates K=6 variants of the essay/transcript with one marker changed (name → Kazakh/Russian/neutral; region mention → other oblast; school type phrase → other; language → machine translation; polish → inject 5–8 disfluencies/grammar slips; code-switch a few clauses), re-scores each with the identical prompt, and shows per-competency deltas as dots on a 3-level BARS strip plus a signed mean delta. Tolerance band = 2× SD of N=5 same-text re-scores (measured once per prompt version, cached). Anything outside band = red "probe failed", written to the red-team log (F9).
- Why: Bias exclusion; Transparency; Creativity. Directly reuses the matched-guise (Hofmann), CALM robustness-rate and Tamkin protocols.
- Novelty: uncommon (live, per-candidate, with noise-calibrated tolerance)
- Effort: M; when: before Oct 3 (essay only; transcript/Feynman in Stage 2)
- Risks: cost (K+1 calls per probe) — use Haiku 4.5 for variant generation and the production model for scoring; translation variants alter meaning; the probe tests the LLM scorer, not the ipsative test.
- Confidence: high
- Sources: arxiv 2403.00742; llm-judge-bias.github.io; arxiv 2312.03689; aclanthology 2024.emnlp-main.474

## F3. Cohort-level Bias Probe Suite (nightly / on-demand)
- Category: probe
- What: Run F2 across the whole cohort per prompt version; report per-marker "robustness rate" (share of candidates whose BARS level is unchanged) and mean signed delta per competency; a heat-map marker × competency. Store results with prompt hash and model ID so the committee can see the probe passed for *this* version.
- Why: Bias exclusion verifiable on data at scale; gates F10.
- Novelty: uncommon
- Effort: M; when: Stage 2 (a 20-candidate preview before Oct 3)
- Risks: API spend; mitigate by sampling 30–50 candidates per run.
- Confidence: high
- Sources: same as F2

## F4. Cross-lingual Consistency Check
- Category: language-fairness
- What: Score the original text (English rubric, source-language text) and an English machine translation with the same rubric; show both per competency; if they differ by ≥1 BARS level, mark "language-sensitive — human review" and show the two rationales side by side. Add explicit instruction block: "Assess only the behavioural indicators. Ignore grammar, spelling, dialect, fluency, vocabulary size and length." Language is a *declared* field; a code-switch detector (simple script-mix heuristic) routes mixed text to the check automatically.
- Why: Bias exclusion (language, manner of speech); Creativity. Grounded in Zhou et al. per-language bias, KazMMLU's English-instruction advantage, and the MT-Bench ensemble/reference guidance.
- Novelty: genuinely novel for a hackathon
- Effort: M; when: before Oct 3 (essay), Stage 2 (video transcripts, Feynman)
- Risks: translation erases dialect features, which may hide real disparities; treat agreement as one signal, not proof. Kazakh ASR error inflates disagreement; gate on transcript confidence.
- Confidence: medium-high
- Sources: arxiv 2607.14480; arxiv 2502.12829; arxiv 2306.05685

## F5. Per-language and per-cohort score calibration
- Category: language-fairness | metric
- What: Replace fixed 70/50 thresholds with within-language percentile bands (or offsets learned from Stage-2 historical data where human ratings exist); display raw and calibrated score with a tooltip "Calibrated within Kazakh-language applicants (n=…)". Show the pre/post impact ratio in F1 so the committee sees the effect.
- Why: Bias exclusion (language); Scoring for the committee (comparability).
- Novelty: uncommon
- Effort: S (percentile) / M (learned offsets); when: S before Oct 3, M in Stage 2
- Risks: small n per language; requires declared language; calibration is a policy choice the methodology owner must approve (document as committee-owned parameter).
- Confidence: medium
- Sources: arxiv 2607.14480; arxiv 2607.14605

## F6. Evidence-linked indicator rationale with "not found" list and confidence
- Category: explainability
- What: For each of the 9 competencies (Stage 2: their BARS anchors; now: our dimensions), the scorer returns structured JSON: level (weak/normal/high), 1–3 verbatim quoted spans with character offsets (front end highlights them in the source), the anchor matched, an "indicators looked for but not found" list, a contrastive sentence ("Normal rather than High because …"), and a confidence tag (high/medium/low) derived from text length, language, transcript WER class, and re-score agreement. Use structured outputs (not regex on free text).
- Why: Explainability ("tied to a concrete behavioural indicator"); Transparency; NIST Explanation Accuracy and Knowledge Limits; EU AI Act Art. 86 "main elements of the decision".
- Novelty: table stakes (quotes) / uncommon ("not found" + contrastive + confidence)
- Effort: M; when: before Oct 3
- Risks: quoted spans must be verified programmatically to exist in the text (hallucinated quotes destroy Explanation Accuracy) — reject and retry if not found.
- Confidence: high
- Sources: nvlpubs NIST IR 8312; arxiv 1711.00399; artificialintelligenceact.eu/article/86

## F7. Candidate-facing development feedback (bank-safe)
- Category: candidate-facing
- What: Auto-draft, committee-approved before release: per competency a strengths line, one development recommendation phrased at behaviour level from the public BARS ("show a measured result and your personal contribution"), and a counterfactual "what would strengthen this" sentence. Never shows ipsative items, item scores, weights, cut-offs or ranks. Includes a "Request a human review of my AI pre-score" link (F8).
- Why: Recommendations to the candidate; Human-in-the-loop; Kazakhstan Digital Code right to notification/explanation of key factors; EU AI Act Art. 26(11)/86.
- Novelty: table stakes (feedback) / uncommon (counterfactual + contest link)
- Effort: S–M; when: before Oct 3 (draft view), Stage 2 (release workflow)
- Risks: feedback leaks the rubric emphasis to future cohorts; mitigate by keeping wording at BARS-anchor level (already public) and rotating phrasing.
- Confidence: high
- Sources: arxiv 1711.00399; kinstellar.com Digital Code summary; artificialintelligenceact.eu/article/26

## F8. Right to see and contest the AI pre-score
- Category: candidate-facing | governance
- What: Candidate portal shows: "An AI system produced a preliminary score used by the committee" notice, the competency levels and rationales (F6/F7), and a "Contest" form (free text + optional attachment). Contests create a committee task; the committee must record an outcome. Status visible to the candidate.
- Why: Human-in-the-loop; Transparency; Digital Code rights to human review and dispute resolution; EU AI Act Art. 26(11), 27(f) "complaint mechanisms"; Ofqual lesson (no individual appeal).
- Novelty: uncommon
- Effort: M; when: Stage 2 (mock in demo before Oct 3)
- Risks: workload for committee; cap by routing only contests on screened-out candidates first.
- Confidence: high
- Sources: kinstellar.com; artificialintelligenceact.eu/article/27; wikipedia Ofqual controversy

## F9. Red-team log and attack-success dashboard
- Category: governance | probe
- What: A versioned log of every adversarial test run against the scorer: fake authority/citations, emotional framing, verbosity padding, "water" filler, socially desirable phrasing, name/region swaps, dialect injection — each with attack success rate (share of runs that changed the BARS level), model/prompt hash, date, and fix applied. Displayed as a table + trend.
- Why: Transparency; Bias exclusion; NIST AI RMF Measure/Manage; ISO 24027 lifecycle bias testing; also directly addresses the client's "socially desirable answers / water" problem as an adversarial robustness property.
- Novelty: genuinely novel for a hackathon
- Effort: S–M (log + 5 canned attacks); when: before Oct 3
- Risks: none material; keep it honest — show failures, not only passes.
- Confidence: high
- Sources: llm-judge-bias.github.io; aclanthology 2024.emnlp-main.474; airc.nist.gov

## F10. Fairness gate ("fairness budget") on prompt/model changes
- Category: governance
- What: A pytest-style check run on every prompt or model change against a frozen golden set (synthetic now, anonymised historical later): max |mean delta| per counterfactual marker, min robustness rate (e.g., ≥ 0.9), min impact ratio (≥ 0.8 with CI), max score drift. Failing the gate blocks the "Publish scorer version" action in the admin UI and shows which check failed. Model card (F12) auto-updates from the gate results.
- Why: Bias exclusion verifiable on data; Human-in-the-loop (nothing ships unchecked); Amazon lesson (they could not verify neutrality, so they stopped — here the stop is automatic).
- Novelty: uncommon (common in ML ops, rare in hackathons)
- Effort: M; when: before Oct 3 (minimal), Stage 2 (full)
- Risks: thresholds are policy; set them jointly with the methodology owner and record in the model card.
- Confidence: high
- Sources: technologyreview.com Amazon; airc.nist.gov; fairlearn.org

## F11. Opportunity context for humans, provably excluded from the score
- Category: explainability | governance
- What: Retire the school-type "starting advantage" as a score input. Instead, show the committee a context strip (school type, region, language, Foundation eligibility) alongside the AI score, with a "Blind / Informed" toggle: the AI score is computed only from masked content; toggling shows the same number, demonstrating the model never saw the attributes. Growth Trajectory is redefined as evidence of change described *by the candidate* (before/after within their own narrative), not a demographic delta.
- Why: Bias exclusion ("background must not lower the score"); Transparency; addresses the client's "unequal starting conditions" concern the defensible way — humans contextualise, the model does not adjust. Avoids Ofqual's school-prior mechanism.
- Novelty: genuinely novel for a hackathon (the live blind/informed proof)
- Effort: S; when: before Oct 3
- Risks: the committee may still weigh context inconsistently — log overrides with reasons and show override rates by group in F1.
- Confidence: high
- Sources: wikipedia Ofqual controversy; arxiv 2312.03689 (masking works)

## F12. One-page Model Card + Impact Assessment, auto-filled
- Category: governance
- What: A `/model-card` page and PDF generated from live data: model ID, prompt version hash, intended use ("decision support before interview; never final"), out-of-scope uses, factors (language, region, school type, income proxy), metrics with current values from F1/F3/F9/F10, evaluation data description, known limits (Kazakh ASR WER, small-n CIs), human oversight description, complaint path. Impact assessment section follows EU AI Act Art. 27(a)–(f).
- Why: Transparency; Human-in-the-loop; credibility signal via ISO 42001 / NIST RMF / EU AI Act alignment.
- Novelty: table stakes in industry, uncommon in hackathons
- Effort: S; when: before Oct 3
- Risks: must stay truthful — generate from data, not hand-typed claims.
- Confidence: high
- Sources: arxiv 1810.03993; artificialintelligenceact.eu/article/27; iso.org/standard/77607.html

## F13. Committee override log with automation-bias telemetry
- Category: governance | metric
- What: Every override stores dimension, from→to, reason, user, time. Dashboard shows override rate by protected group and by AI confidence, plus "agreement with AI" rate per committee member (calibration view) and a monthly reminder card about automation bias. Logs retained ≥ 6 months.
- Why: Human-in-the-loop; EU AI Act Art. 12 logging, Art. 14(4)(b) automation-bias awareness, Art. 26(6) log retention; Scoring for the committee (calibration alignment was a client problem).
- Novelty: table stakes (log) / uncommon (automation-bias telemetry)
- Effort: S–M; when: log before Oct 3, telemetry Stage 2
- Risks: storage currently in-memory; needs a real DB first.
- Confidence: high
- Sources: artificialintelligenceact.eu/article/12, /14, /26

## F14. Funnel disparate-impact monitor
- Category: metric
- What: Stage-by-stage counts by group: applied → complete application → AI pre-score above cut-off → invited to interview → admitted. Impact ratio per transition, isolating the AI stage from the human stages so the committee can see where disparity enters.
- Why: Bias exclusion verifiable on data; Uniform Guidelines 4C "bottom line" logic (evaluate components when the total process shows impact).
- Novelty: genuinely novel for a hackathon
- Effort: S (data model) / M (real data); when: Stage 2 (mock before Oct 3)
- Risks: needs the client's downstream outcomes; small n per transition.
- Confidence: medium
- Sources: uniformguidelines.com; nycbiasaudit.com

## F15. Single-candidate absolute scoring (no pairwise LLM comparison), transcript-quality gating
- Category: probe | language-fairness
- What: Architectural rule enforced in code: the scorer sees one candidate at a time with an absolute BARS rubric; ranking is computed from scores, never by asking the model to compare. For Kazakh video, compute an ASR confidence/WER class; below threshold, Communication-type indicators are marked "not assessed (audio quality)" instead of scored.
- Why: Bias exclusion (manner of speech, language) — side-by-side comparison amplifies dialect bias; NIST Knowledge Limits.
- Novelty: table stakes once known; uncommon to state explicitly
- Effort: S; when: before Oct 3
- Risks: gating reduces coverage for Kazakh speakers; make the gap visible in F1 and route to interviewer hints.
- Confidence: high
- Sources: arxiv 2605.24384; nvlpubs NIST IR 8312

---

# Design rules to cite in the pitch

1. "Test the scorer, not the applicant": every scorer version passes counterfactual name/region/school/dialect swaps before it touches a real application — matched-guise probing [arxiv 2403.00742; arxiv 2312.03689].
2. Never let the model compare two people; side-by-side comparison amplifies dialect bias [arxiv 2605.24384].
3. No school- or region-level prior ever moves an individual's score — the Ofqual 2020 mechanism downgraded state-school pupils and was reversed in four days [wikipedia Ofqual controversy].
4. No facial, voice-emotion or appearance signals — HireVue dropped facial analysis (≈0.25% accuracy contribution) under bias pressure; Kazakhstan's AI Law bans emotion detection without consent [fortune.com; levellers.ai].
5. Don't learn the target from past admits without auditing the labels — Amazon's model penalised "women's" [technologyreview.com].
6. Stylometry/AI-detection flags never subtract points; they penalise non-native writers (over half of TOEFL essays misflagged) [sciencedaily.com; arxiv 2304.02819].
7. Per-language calibration and an L1/language-disaggregated audit, not one global threshold — LLM judges shift 0.4–0.5 points across languages [arxiv 2607.14480; arxiv 2607.14605].
8. The 80% impact-ratio line is a review trigger with confidence intervals, not a certificate [uniformguidelines.com; arxiv 2202.09519; fairlearn.org].
9. Every rationale quotes the evidence and names what was *not* found; confidence shown; abstain when transcript quality is low — NIST Explanation Accuracy and Knowledge Limits [nvlpubs NIST IR 8312].
10. The committee can disregard, override or reverse any output, and overrides are logged ≥ 6 months — EU AI Act Art. 14(4)(d), Art. 26 [artificialintelligenceact.eu].
11. Every applicant is told an AI pre-score exists, gets the key factors, and can request human review — Kazakhstan Digital Code (in force 11 Jul 2026) and EU AI Act Art. 86 [kinstellar.com; artificialintelligenceact.eu/article/86].
12. A published audit is theatre unless it is reproducible — NYC found 17 issues where the regulator found 1 [dlapiper.com]; ship code + data hash with the audit.

---

# One-page Model Card and Impact Assessment outline

**Model Card — AI Leader ID pre-selection scorer** (auto-generated; structure per Mitchell et al.)
1. Model details: LLM ID(s), prompt version hash, scoring schema version, date, owner (team) and methodology owner (inVision U / Talent Craft).
2. Intended use: preliminary scoring and interviewer hints before the live interview; decision support only. Out of scope: final admission, auto-reject, ranking by LLM comparison, any use of face/voice-emotion.
3. Inputs: essay, video transcript (language, ASR confidence class), Feynman chat, ipsative test scores (Stage 2). Protected attributes are collected for audit only and masked from the model (list exactly which fields are masked).
4. Factors audited: language (KZ/RU/EN/code-switched), region (urban/rural, oblast), school type, Foundation eligibility (income proxy), gender; intersections.
5. Metrics and current values: scoring-rate impact ratios with 95% CI per factor; robustness rate per counterfactual marker; re-score noise SD; cross-lingual agreement rate; override rate by group; attack success rates (red-team).
6. Evaluation data: synthetic cohort (n, generator description) now; anonymised historical cohort (n, years) in Stage 2; data hash.
7. Known limits: Kazakh spontaneous-speech ASR WER (state numbers used), small-n CIs, prompt sensitivity, translation smoothing, no outcome labels for predictive validity.
8. Human oversight: who reviews, override mechanism, log retention, contest path, automation-bias reminder.
9. Ethical considerations / do-not-use: minors' data, consent basis, cross-border processing with PII masking, no video retention in the pipeline.
10. Changelog of fairness-gate results per version.

**Impact Assessment (structure per EU AI Act Art. 27(a)–(f), scaled down)**
- (a) Process: where the system sits in the AS-IS funnel (before interview; hints during; draft feedback after); what humans decide.
- (b) Period and frequency: admission cycle dates, cohort size, re-score cadence.
- (c) Affected groups: applicants aged 16–18, rural/Kazakh-speaking applicants, Foundation candidates, applicants with disfluent speech or low-quality video.
- (d) Specific risks: language-severity bias, dialect/manner-of-speech penalty, proxy learning from school/region, stylometry false flags, ASR failure for Kazakh, automation bias in committee, item-bank leakage via feedback, cross-border data transfer.
- (e) Oversight measures: F2/F3 probes, F10 gate, F13 override log, F15 gating, competency-trained reviewers.
- (f) If risks materialise: pause scorer version (gate), re-score affected cohort, notify committee, candidate contest path (F8), record in red-team log (F9); legal basis and consent text (Kazakhstan Law 94-V, consent by applicant and legal representative — verify article number; AI Law 230-VIII; Digital Code 255-VIII).
