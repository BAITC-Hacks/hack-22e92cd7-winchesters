# What most competing teams will build (and why that is not enough)

Predictable Stage-2 build from 15 of the 20 finalists: (a) an LLM that reads the essay/video transcript and emits a 0-100 "leadership score" with a paragraph of justification; (b) a ranked dashboard with weight sliders; (c) a "bias" section that either is a disclaimer or a group-average table; (d) a generic "areas to improve" paragraph for the candidate. Some will add facial/voice "emotion" analysis, which the client will reject (see exclusions). Our own Stage-1 product is, honestly, a polished version of exactly this template, plus one memorable gimmick (Feynman).

Why that loses in Stage 2:
- It scores on the team's own invented dimensions, not the client's 9 competencies, ATOLA structure or BARS levels. The client's deck says "a solution with high AUC that cannot explain a single one of its scores, we cannot put into admissions". A paragraph of LLM prose is not an explanation tied to "a concrete behavioral indicator"; a BARS anchor plus a quote is.
- It produces one output (a score) for one audience (committee). The client named three insertion points (before / inside / after) and six people. The interviewer and the rejected candidate get nothing.
- It treats "bias" as a promise. The client says "verifiable on data". Research on LLM hiring judgments shows models look unbiased in simple tests and then develop 6-9% demographic bias when realistic context is added, with prompt-level anti-bias instructions proving fragile and chain-of-thought rationalizations masking the bias [source: https://arxiv.org/html/2506.10922]. A committee-runnable test beats a paragraph.
- Hackathon judges explicitly say the winners "depart the most from the template" while still nailing the primary objective, and that visual clarity of the demo matters enormously [source: https://info.devpost.com/blog/hackathon-judging-tips].

The winning posture: "We did not build a scorer. We built the evidence layer of your existing methodology, with one view for each of the three moments and each of the people in the room." Every idea below is a view onto one shared object: an Evidence Ledger of (competency, BARS level, indicator, verbatim quote, source, confidence) tuples.

# Verdict on the Feynman Teaching Challenge: TRANSFORM (keep the mechanic, kill the framing)

What it did well: it is the only thing in the Stage-1 product that produces observable behavior instead of self-description, it is memorable ("watch them teach"), and it got the team to 4th place. Do not throw away a proven demo hook.

Why it cannot stay as-is:
1. Teaching "why it rains" to a 10-year-old maps to none of the 9 competencies. The closest is Intellect (7: "understand the complex and apply it"), and even that is a stretch. Clarity/Patience/Empathy/Adaptability are the team's dimensions, not the client's. A methodology owner will ask "which behavioral indicator does this feed?" and there is no answer.
2. It rewards verbal fluency and typing speed in a chat UI, which is precisely the "polished city candidate" advantage the client wants to neutralize.
3. The quiz-transfer metric measures Claude's ability to learn from a transcript as much as the candidate's teaching.

The transformation: "Leadership Scenario Lab" (idea I6). Keep the core mechanic (candidate interacts with an AI-played persona over 6-10 turns, behavior is observed, a transparent scoring pass runs afterwards) but re-author the scenario so each fork is a live, open-response version of the client's own competencies. Example scenario: the candidate is co-leading a school/community project; an AI teammate ("Aigerim") argues with another AI teammate ("Daniyar") over the plan (Teamwork, the exact situation of the disclosed ipsative item "When an argument starts in the group, I..."); a shortcut is offered that would inflate the result (Values); a deadline slips and someone has to own it (Leadership abilities: takes responsibility for consequences); a teammate says something wounding (Wounded leadership: does the candidate go harsh, controlling or into a victim position). One optional final turn keeps the Feynman DNA: "a new teammate joins; explain the project so she can act tomorrow" (Intellect / communication of complexity).

Why a committee could accept it: it is an open-response situational judgment exercise, a format used in professional-school admissions (Casper) where the vendor reports 25-50% smaller demographic differences than academic assessments while retaining validity [source: https://acuityinsights.com/resources/research/casper-uses-a-unique-open-response-format/]; it is aligned with the client's principle "observable behavior, not self-description"; and, critically, it is positioned as supplementary evidence for the ledger and as probe material for the interviewer, never as a standalone score. Guardrails that make it defensible: scenarios authored/approved by Talent Craft (we provide the engine and a scenario editor); available in Kazakh/Russian/English with voice input allowed; scored only against BARS anchors with verbatim quotes; a "not observed" outcome is allowed and is not a penalty; the committee can toggle its weight to zero.

Known weakness to state out loud: LLM role-play agents diverge from real human conflict behavior and there is no consensus on what validates an LLM simulation as behavioral evidence [unverified: based on search snippets of Hullman "Validating LLM simulations as behavioral evidence" and an EMNLP 2025 paper on behavioral alignment in conflict dialogue; pages not opened]. Therefore we do not claim the AI teammate is realistic; we claim the candidate's own words in response are real evidence, which the interviewer can probe.

# Ideas

## I1. The Evidence Ledger (one object, three views)
- Insertion point: cross-cutting (foundation for everything else)
- What: Replace the 5-dimension scorer with a structured extraction step that turns every source (video transcript, ipsative profile, scenario lab transcript, interviewer notes) into atomic evidence tuples: competency (1-9), BARS level anchor text matched (weak/normal/high), indicator, verbatim quote in original language, source, timestamp, and a confidence. Aggregation to a level per competency is a transparent rule (e.g., highest level with at least two independent quotes, else "insufficient evidence"), not an LLM opinion. "No evidence" is a first-class state distinct from "weak". Use Claude with structured outputs (JSON schema) and one call per competency to avoid halo effects. The same ledger renders as the committee dossier, the interviewer pre-brief and the candidate growth map.
- Why / criteria served: Explainability (every score literally is a quote plus a BARS anchor), Transparency, Scoring for the committee (single scale = client's own scale), Human-in-the-loop (committee edits tuples, not scores).
- Differentiation: Other teams will score first and explain after. We never produce a number that does not decompose into quotes. This also makes the Stage-2 historical data usable: we can compute agreement per competency instead of one AUC.
- Demo moment: Click "High" on Leadership abilities; the exact 12-second segment of the video transcript highlights, with the BARS anchor text ("launches projects, unites people") shown next to it. Click "Wounded leadership: insufficient evidence"; nothing highlights, and the UI says "not observed remotely; interviewer probe suggested".
- Effort: M ; when: skeleton before Oct 3 (mapping to 9 competencies from open sample BARS), full BARS in Stage 2.
- Risks / mitigations: LLM rubric alignment with humans is only moderate (r about 0.5-0.65 in a 2025 essay-grading study, and few-shot calibration did not uniformly help) [source: https://pmc.ncbi.nlm.nih.gov/articles/PMC13520715/]; so the ledger must be presented as "AI-drafted, human-confirmed" and validated on the historical data (see I18). Kazakh quotes depend on transcript quality; keep the original audio segment linked so a human can listen.
- Confidence: high
- Sources: [source: https://pmc.ncbi.nlm.nih.gov/articles/PMC13520715/] [source: https://www.metaview.ai/resources/blog/create-effective-interview-scorecards]

## I2. Triangulation Map: ipsative profile vs observed behavior
- Insertion point: before
- What: Ingest the ipsative test result (Stage 2 gives scoring) as a 9-competency profile in the client's bands (+60..+90 very high, etc.). Overlay it with the ledger's video/scenario evidence. Where they agree, the dossier shows a confirmed signal. Where they diverge (test says teamwork very high, video shows only "I" stories), the dossier does not lower the score; it emits a named discrepancy and a suggested ATOLA probe for the interviewer. Also compute test-internal validity flags (response-time anomalies, straight-lining patterns) if the API exposes them.
- Why / criteria served: Directly implements the client's "hints to the interviewer which competencies to dig deeper"; addresses socially desirable answers by cross-source consistency instead of a single-source lie detector. Forced-choice formats are already fairly faking-resistant (meta-analysis of 82 samples, N=106k) [source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8511514/], so the test is the anchor and the video is the behavioral check.
- Differentiation: Most teams will ignore the ipsative test because the bank is closed now; we design the ingestion contract today and show it on a mocked profile.
- Demo moment: Two radar charts slide over each other; three spokes light up amber with the label "dig here: Teamwork - test very high, remote evidence none".
- Effort: S before Oct 3 (mock profile), M in Stage 2 (real scoring, IRT bands).
- Risks: A committee might read divergence as dishonesty. Mitigation: UI vocabulary is "unconfirmed", never "inconsistent"; divergence never changes a level.
- Confidence: high
- Sources: [source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8511514/]

## I3. Triage with the right to abstain (no black-box ranking)
- Insertion point: before
- What: Pre-interview prioritization as three transparent queues rather than a global score rank. Queue C "clearly irrelevant" (the only thing the client allows to be screened out) is decided by published rules only: no video / video not about the candidate / no test / test invalid / application for a non-existent major. Queue A "strong remote evidence": at least k competencies at normal-or-high with two or more quotes. Queue B "interview needed to resolve": everything else, sorted by information need (how many competencies are undetermined), not by score. Every queue assignment shows the rule that fired. The model is explicitly allowed to abstain ("insufficient evidence") and the abstention rate is displayed as a health metric.
- Why / criteria served: Problem (1) manual labor scales, without pretending remote data can rank humans; Transparency; Human-in-the-loop; Bias exclusion (a rule-based gate cannot learn a demographic proxy).
- Differentiation: Everyone else ranks 1..N. Judges who have sat on committees will recognize that "sort by uncertainty" is how experienced committees actually spend their time.
- Demo moment: Toggle "show why" on queue C: a candidate with an empty video appears with "Rule C2: video shorter than 20s". Toggle queue B: "3 of 9 competencies undetermined - 25-min interview will resolve".
- Effort: S ; when: before Oct 3
- Risks: Organizers might expect a score. Mitigation: the score still exists inside the dossier (I1) but is not the sort key before interview; explain anchoring risk.
- Confidence: high
- Sources: [source: https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/] (HireVue's audit found minority candidates gave shorter answers the system could not score, so they were disproportionately routed to human review; our design makes "route to human" the default rather than an error path)

## I4. Hidden Gems, done defensibly: context as a flag, never a multiplier
- Insertion point: before / committee
- What: Delete the school-type "starting advantage" table (private 75, village 25) from the score. Replace with (a) a "scope relative to opportunity" descriptor extracted from the candidate's own narrative ("organized 30 people with no budget in a school of 200" vs "led a funded club of 5 in a lyceum") shown as text next to the Leadership level; (b) a contextual flag (rural school, Foundation eligibility, first-generation, care/adversity self-declared) displayed as a badge for the committee, exactly as UK contextual admissions do it: flags for human attention, not automatic score changes; school performance data "contextualizes" but "does not generate flags" [source: https://www.bath.ac.uk/legal-information/contextual-data-used-for-2022-undergraduate-admissions/]. The Hidden Gem filter becomes "candidates whose observed-behavior levels exceed what their formal markers predict", computed from the ledger, and the committee decides what to do with it.
- Why / criteria served: Problem (5) unequal starting conditions; Bias exclusion (background must not lower the score; a demographic multiplier can also be attacked as raising it unfairly); Scoring for the committee (defensible).
- Differentiation: Teams will either ignore context or hard-code a bonus. Flag-not-multiplier is the practice a real admissions officer will recognize.
- Demo moment: Same candidate, two panels: "Stage 1 model: village = 25 starting points" crossed out; "Stage 2: Leadership High - 'organized 30 volunteers, no budget, school of 200' - context badge: rural / Foundation eligible". Score identical to an Almaty candidate with the same behavior.
- Effort: S ; when: before Oct 3
- Risks: Some committee members want the model to "boost" village candidates. Answer: the mission is to see potential, not to compensate; compensation is a human policy decision (Foundation year), and we make it visible, not automatic.
- Confidence: high
- Sources: [source: https://www.bath.ac.uk/legal-information/contextual-data-used-for-2022-undergraduate-admissions/]

## I5. Manner-of-speech firewall (polish-invariant scoring)
- Insertion point: before / integrity
- What: Before any scoring, the transcript passes through a normalization step that rewrites each utterance into neutral-register propositions in one working language (what was done, by whom, with what result), preserving specifics (numbers, names of activities, timelines) and dropping fluency markers, dialect, code-switching, grammar and filler. Scoring (I1) runs only on the normalized layer; the committee can see both layers side by side. A test harness feeds paired transcripts (same content, one in rural Kazakh with code-switching, one in polished Russian) and asserts identical ledgers.
- Why / criteria served: Bias exclusion on "manner of speech" and "language", verifiable on data; Problem (5). HireVue's own conclusion after dropping visual analysis was that answer content, not delivery, carried the predictive value [source: https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/].
- Differentiation: Most teams will feed raw transcripts to the LLM and hope the prompt says "ignore grammar". Research shows prompt-level debiasing is fragile in realistic contexts [source: https://arxiv.org/html/2506.10922]; an architectural firewall is a different class of answer.
- Demo moment: Left: raw Kazakh transcript with fillers and Russian loanwords. Right: normalized propositions. Below: two identical competency bars for the polished and unpolished versions of the same story.
- Effort: M ; when: prototype before Oct 3 (one example), harness in Stage 2.
- Risks: Normalization may erase legitimately weak content (vagueness is a real signal for "water"). Mitigation: the water meter (I15) runs on specificity of propositions, which normalization preserves. Translation errors for Kazakh: keep originals linked.
- Confidence: medium
- Sources: [source: https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/] [source: https://arxiv.org/html/2506.10922]

## I6. Leadership Scenario Lab (the transformed Feynman challenge)
- Insertion point: before
- What: See verdict above. 6-10 turn open-response scenario with AI teammates, forks authored per competency (Teamwork, Values, Leadership abilities, Wounded leadership, optional Intellect teach-back), voice or text in KZ/RU/EN, scored post-hoc into the ledger with quotes against BARS anchors. A scenario editor lets methodology owners write new forks and retire leaked ones, so the "bank" of scenarios can rotate like the test bank. The result is labeled "observed in simulation" and feeds interviewer probes ("in the scenario she chose the shortcut; ask about a real time she faced that").
- Why / criteria served: Client principle "observable behavior, not self-description"; Problem (3) socially desirable answers (you cannot recite a prepared story when the situation moves); Recommendations to the candidate (their own choices become the feedback material); Creativity.
- Differentiation: Nobody else will have an interactive behavioral exercise; and ours is tied to the client's competencies rather than to a cute science topic.
- Demo moment: Live on stage: a judge plays the candidate for 90 seconds; two AI teammates start arguing; the judge intervenes; the ledger populates in real time with "Teamwork - High - 'let's hear Daniyar's version first, then decide' - anchor: helps participants hear each other".
- Effort: M (re-skin of existing Feynman engine) before Oct 3 for one scenario; L in Stage 2 for editor, voice, validation on historical outcomes.
- Risks: Validity of LLM role-play is unproven [unverified]; a candidate with slow typing or no quiet room is disadvantaged (mitigate with voice, generous time, and treating absence as "not observed"); coaching schools will publish scenario walkthroughs (mitigate with rotation and by weighting scenario evidence below interview evidence). A committee will accept it only if Talent Craft co-authors the forks; say so.
- Confidence: medium
- Sources: [source: https://acuityinsights.com/resources/research/casper-uses-a-unique-open-response-format/]

## I7. Interviewer Pre-Brief: one page, no score
- Insertion point: inside (before the 25 minutes start)
- What: A phone-sized card generated from the ledger: nine rows, each with an evidence state (strong / some / none / conflicting) and no number; the top three probes, written in ATOLA form and targeting the competencies with the least evidence ("Application: ask where she applied the lesson from the volunteer camp elsewhere"); discrepancy alerts from I2; water hotspots (two quotes the water meter flagged, with the missing ATOLA element named); two verbatim strengths so the interviewer can open warmly. Deliberately withholds the preliminary score to reduce anchoring. Printable.
- Why / criteria served: The client explicitly permits "hints to the interviewer"; Problem (1) time (interviewer skips what is already evidenced remotely and spends the 25 minutes where the information is); Problem (2) calibration (everyone probes with the same ATOLA grammar); Human-in-the-loop.
- Differentiation: Interviewer-facing output is the most under-built surface in this competition; our Stage-1 product had none. Interview-intelligence vendors have converged on "AI routes evidence to competency, human adds the judgment line" [source: https://www.metaview.ai/resources/blog/create-effective-interview-scorecards], but none of them target a structured admissions interview with BARS.
- Demo moment: A real printed card held up to the camera; then the same card on a phone, with "Wounded leadership: no remote evidence - suggested opener: ..." circled.
- Effort: S ; when: before Oct 3
- Risks: Interviewers reading a screen instead of the human; mitigated by the one-page, no-live-updates design. Pre-brief could bias the interviewer toward confirming remote evidence; mitigated by showing states, not levels, and by rotating which probes appear.
- Confidence: high
- Sources: [source: https://www.metaview.ai/resources/blog/create-effective-interview-scorecards] [source: https://brighthire.com/ai-interview-notes/]

## I8. Post-interview Note-to-BARS structurer (offline, not live)
- Insertion point: inside (immediately after)
- What: The interviewer's own messy notes (typed, photographed handwriting, or a 3-minute voice memo dictated right after) are mapped by Claude into ledger tuples: each fragment is attached to a competency and a BARS level anchor, with the interviewer confirming or moving each with one tap. The tool lists competencies with no notes ("you did not record anything on Purpose-driven leadership"). If the university has a consented recording, the same flow runs on a post-hoc transcript; for Kazakh, the transcript is treated as a navigation aid to the audio, not as a scoring source, because Kazakh ASR error rates on spontaneous speech remain high (reported ranges roughly 18-40% WER for the best regional systems and far worse for stock Whisper) [unverified: MDPI Information 16(10):879 abstract seen via search results; page returned 403]. A lightweight in-interview companion exists but does nothing clever: nine competency chips the interviewer taps as covered, and a "5 minutes left, 2 blocks uncovered" nudge.
- Why / criteria served: Problem (2) calibration alignment on a single scale (the client's words); Explainability (interview ratings become quotes plus anchors, like remote ratings); Human-in-the-loop; realistic given Kazakh ASR.
- Differentiation: Teams that promise live transcription with real-time hints will either demo in English or fail on stage. Offline dictation is the honest, working alternative.
- Demo moment: The presenter dictates a 20-second messy note in Russian ("she talked about the school radio, organized six people, teacher was against it, they still did it, no clear result though"); tuples appear: Leadership abilities - Normal/High boundary - "organized six people despite opposition"; Outcome element missing - suggested rating note.
- Effort: M ; when: notes version before Oct 3; recording/transcript version in Stage 2 with the client's technical team.
- Risks: Recording minors requires consent and data-law review; default to notes and dictation. Interviewers may over-trust the auto-mapping; require one-tap confirmation per tuple and log changes.
- Confidence: high (notes) / medium (recording)
- Sources: [source: https://www.metaview.ai/resources/blog/create-effective-interview-scorecards] [source: https://brighthire.com/ai-interview-notes/]

## I9. Leadership Growth Map (candidate-facing feedback)
- Insertion point: after
- What: Every applicant, admitted or not, receives a mobile-first page (and a shareable PDF) with: (1) "What we saw" - two or three strengths, each quoting the candidate's own words back to them; (2) "What we could not see yet" - competencies with no or weak evidence, phrased as opportunity ("we did not hear about a time you helped a group in disagreement reach a decision"), never as a score; (3) one concrete, zero-budget next step per competency that is doable in a village school (start a study group and keep a results log; volunteer at the akimat youth center; run a one-day event and write down what went wrong); (4) links to free Kazakh/Russian resources; (5) the re-application pathway, including Foundation year eligibility. Tone follows the UK SPA good-practice principles: a clear reason, personal, plain language, never third-person system text, never referring to criteria that were not published [source: https://www.ucas.com/media/125531/download]. Optional Kazakh voice narration for low-literacy contexts [unverified that current Kazakh TTS quality is adequate].
- Why / criteria served: Recommendations to the candidate is a scored criterion the Stage-1 product completely lacks; mission ("talent is evenly distributed, opportunity is not"); reputation of a 100%-grant university with thousands of rejected 17-year-olds.
- Differentiation: Others will paste the committee explanation into an email. Ours is a product for the rejected candidate, designed around the fact that feedback delivered at a rejection point tends to be received negatively [unverified: search snippet citing a Southampton study, page not opened], so strengths come first and the ending is a door, not a verdict.
- Demo moment: Phone mock-up in Kazakh: three green cards with quotes, two grey cards "not seen yet" with a next step, a button "Apply again in 2027 - what will have changed".
- Effort: M ; when: before Oct 3 (template), Stage 2 (real BARS wording, resource curation, translation QA).
- Risks: Leaking the test (see I10). Feedback about Wounded leadership can hurt a minor; rule: never generate feedback on competency 9 without committee review, and never quote hard-experience content back. Legal: minors and personal data; feedback must be requested/consented by the applicant.
- Confidence: high
- Sources: [source: https://www.ucas.com/media/125531/download]

## I10. Test-bank leak guard for all outward text
- Insertion point: after / integrity
- What: A deterministic filter that every candidate-facing sentence (I9) and every interviewer probe (I7) passes through: embedding and n-gram similarity against the 95 forced-choice items and their options (available in Stage 2), plus a rule set banning phrases that describe answer patterns ("choose the option where you..."). Anything similar is rewritten or dropped and the drop is logged for the methodology owners. Also blocks numeric test scores from appearing in feedback.
- Why / criteria served: The client's stated reason for keeping the bank closed ("future cohorts prep for the test and validity dies"); Recommendations without gaming. This is a "we understand psychometrics" signal that judges from Talent Craft will notice.
- Differentiation: No other team will think about item leakage in feedback.
- Demo moment: Type a feedback sentence that paraphrases the disclosed teamwork item; it turns red with "similar to item T-04, rewritten as: ...".
- Effort: S ; when: before Oct 3 with the one public item, Stage 2 with the bank.
- Risks: False positives make feedback bland; tune threshold with methodology owners.
- Confidence: high
- Sources: none needed; grounded in the brief.

## I11. "Explain my result to me" - candidate-controlled dialogue with a right to object
- Insertion point: after
- What: From the Growth Map, the candidate can ask up to three questions to an assistant that is grounded only in their own feedback document and the public methodology description (not the ledger, not the test). Answers are logged. A button "this does not reflect me" lets the candidate write a short objection that is attached to their record and shown to the committee as a note; for borderline cases this can trigger a human re-read. Parent/guardian consent flow for under-18s.
- Why / criteria served: Human-in-the-loop extended to the person whose fate is decided; Transparency; Problem (6) "can't just trust a model". It also produces a feedback-quality signal for the methodology owners (which competencies generate the most objections).
- Differentiation: Every team builds explainability for the committee; almost none build it for the applicant.
- Demo moment: Candidate asks in Kazakh "Why does it say you did not see teamwork?"; the assistant answers with the two moments in the video where a "we" story could have gone deeper, and offers the objection button.
- Effort: M ; when: Stage 2
- Risks: Legal exposure (appeals), minors, workload if objections flood. Mitigations: objections are notes, not appeals; rate limits; committee decides policy; grounding excludes the ledger so the assistant cannot leak anything the Growth Map does not already say.
- Confidence: medium

## I12. Side-by-side Evidence Compare
- Insertion point: committee
- What: Select 2-4 candidates; a 9-row grid shows, per competency, the level and the single best quote per candidate, with the BARS anchor text in the row header so the committee compares like with like. Sort by any competency; "show only where they differ"; Foundation context badges (I4) visible but separate from the grid.
- Why / criteria served: Scoring for the committee ("candidates comparable to each other"); Problem (2) comparability; Explainability.
- Differentiation: Dashboards rank; almost none let a committee read two people's evidence for the same indicator on one screen.
- Demo moment: Two candidates with identical overall levels; the grid shows one has High on Leadership from a single big story and the other has High from three small ones; the committee sees why they are not the same.
- Effort: S ; when: before Oct 3
- Risks: Cognitive overload; limit to 4 candidates and one quote per cell with expand-on-click.
- Confidence: high

## I13. Disagreement Radar and interviewer calibration analytics
- Insertion point: committee
- What: For each candidate, a small chart of where AI-drafted levels and interviewer levels diverge, ranked by size. Across the cohort (Stage 2, historical data), per-interviewer severity/leniency per competency relative to peers rating the same BARS anchors, plus agreement statistics (Cohen's kappa) between AI and each interviewer and between interviewers. Overrides are logged with a reason code (evidence in interview / AI misread language / methodology disagreement) and the reason codes feed a monthly calibration session agenda. "AI as the Nth rater": the model is one more rater whose agreement is measured, not the judge.
- Why / criteria served: Problem (2) different interviewers calibrate differently; Human-in-the-loop with an audit trail; Transparency about the model's own limits (we will be able to say "AI agrees with the committee on Leadership abilities at kappa 0.6 but only 0.3 on Wounded leadership, so it abstains there"). Structured interviews are the strongest single predictor in the revised selection meta-analysis (operational validity about .42) but with high variability depending on how well they are run [source: https://www.siop.org/tip-article/is-cognitive-ability-the-best-predictor-of-job-performance-new-research-says-its-time-to-think-again/]; calibration analytics are how you reduce that variability.
- Differentiation: Turns the "human disagrees with AI" moment from an embarrassment into the product's main data asset.
- Demo moment: Heatmap of interviewers x competencies; one cell glows: "Interviewer 3 rates Values one level stricter than peers on the same anchors - 14 cases".
- Effort: M ; when: disagreement view before Oct 3 (synthetic), calibration analytics in Stage 2 with historical data.
- Risks: Interviewers may feel surveilled; frame as methodology QA owned by Talent Craft, aggregated, with a minimum-n rule.
- Confidence: high
- Sources: [source: https://www.siop.org/tip-article/is-cognitive-ability-the-best-predictor-of-job-performance-new-research-says-its-time-to-think-again/]

## I14. Contrastive explanations: "what would move this level"
- Insertion point: committee (also feeds I7 and I9)
- What: For each competency the system states the minimal missing evidence to reach the next BARS level, in the anchor's own words ("Normal to High requires: a concrete example of distributing tasks or resolving conflict; and evidence of finishing under difficulty"). The same statement becomes an interviewer probe before the interview and a next step in the candidate's Growth Map after it. One engine, three audiences.
- Why / criteria served: Explainability (the score is explained by what is present and what is absent); Recommendations; hints to the interviewer; makes the distinction between "weak" and "not yet evidenced" concrete.
- Differentiation: Most explanations are post-hoc justifications of a number; contrastive explanations are actionable and are what committees actually argue about.
- Demo moment: Hover a "Normal" chip: a tooltip lists two missing anchor elements; click "send to interviewer" and "send to candidate feedback" - the same text appears in both.
- Effort: S ; when: before Oct 3
- Risks: Could read as a checklist candidates can game; the anchors are already public in structure, and the engine never mentions test items (I10).
- Confidence: high

## I15. Water Meter: ATOLA-completeness instead of vibes
- Insertion point: before / inside / integrity
- What: Segment the transcript into stories; for each story, check which ATOLA elements are present (Action specifics, Thinking, Outcome with measure, Learning, Application elsewhere) and how specific each is (named people, numbers, dates, consequences). "Water" is defined as a story with generic claims and missing A/O elements; socially desirable phrasing is flagged as "value claim without an Action" ("I always put the team first" with no instance). Output is a per-story checklist with quotes, not a deception score. Flags route to the interviewer probe list, never subtract points.
- Why / criteria served: The client explicitly lists "detection of water and socially desirable phrasing" as permitted; Explainability (a checklist is self-explanatory); Problem (3).
- Differentiation: Teams will ask the LLM "is this answer sincere?" and get an unexplainable number. ATOLA completeness is the client's own grammar turned into a detector.
- Demo moment: A paragraph lights up in five colors; two of the five ATOLA letters are grey; the probe appears: "Outcome missing - ask: how did you know it worked?"
- Effort: S ; when: before Oct 3
- Risks: Short or shy speakers produce fewer elements; mitigation: flags are probes, not penalties, and short answers route to human by design (see I3).
- Confidence: high

## I16. Committee-runnable Bias Probe ("swap and rescore")
- Insertion point: committee / integrity
- What: A button on any candidate: the system creates counterfactual twins of the materials (swap name, region, school type, language of the transcript via translation, urban/rural markers, gender-marked forms) and re-runs the ledger. The committee sees the level per competency for each twin; the acceptance criterion is zero level flips and a bounded change in evidence counts. At cohort level: impact ratios of "recommended" rates by region, school type, language and gender against the four-fifths rule used in the NYC automated-employment-decision-tool audits, including intersections [source: https://rules.cityofnewyork.us/rule/automated-employment-decision-tools-2/]. Also a "Cohort Lens" (informational, not a quota) showing the composition of the currently shortlisted set versus the applicant pool.
- Why / criteria served: Bias exclusion "verifiable on data" is the client's phrase; this is the literal implementation. Research shows instance-level counterfactual testing is needed because group averages can look fine while individual scores flip on a name or a school [source: https://arxiv.org/html/2506.10922]. Replaces the Stage-1 "Fairness Audit" which grouped by recommendation category and tested nothing.
- Differentiation: Every team will claim fairness; ours lets a skeptical committee member press a button during the meeting.
- Demo moment: Press "swap": Almaty lyceum -> Kyzylorda village school, Russian -> Kazakh. The nine bars do not move; a green "0 flips" badge. Then the presenter deliberately re-runs with the old Stage-1 model: bars move, red badge. "This is why we deleted our own feature."
- Effort: M ; when: single-candidate swap before Oct 3; cohort impact ratios in Stage 2 with historical data.
- Risks: Translation-based swaps introduce noise; report evidence-count deltas honestly. A perfect swap test does not prove the absence of bias; say so on screen ("necessary, not sufficient").
- Confidence: high
- Sources: [source: https://rules.cityofnewyork.us/rule/automated-employment-decision-tools-2/] [source: https://arxiv.org/html/2506.10922]

## I17. Decision Memo export (defensibility as a document)
- Insertion point: committee
- What: One click produces a per-candidate memo: nine competency levels with quotes and anchors, test bands, interviewer ratings and notes, every override with its reason code and author, the bias-probe result, the model version and prompt hash, and the final committee decision with names. Also a cohort memo for the funder (inDrive) with impact ratios and calibration statistics. PDF, Kazakh/Russian.
- Why / criteria served: "Decision defensible" (client); responsibility for rejection stays with humans, and the memo records that; personal-data law readiness (what was processed, by which model, retained how long).
- Differentiation: Boring, and exactly what a university general counsel and a funder ask for first.
- Demo moment: Click; a two-page PDF opens with the committee chair's name on the signature line and "AI drafted 27 of 31 evidence items; committee changed 4".
- Effort: S ; when: before Oct 3
- Risks: None material.
- Confidence: high

## I18. Validation harness on the anonymized history: agreement, abstention, subgroup parity
- Insertion point: cross-cutting
- What: In Stage 2, replay the anonymized historical assessments through the ledger and report, per competency: agreement with committee levels (kappa, confusion matrices), abstention rate, and parity of agreement across region/school/language subgroups (the model must not be more accurate for city candidates). Publish a "model card" page inside the product. Explicitly report where the AI is weak, which by the client's own prediction will be Purpose-driven and Wounded leadership, and configure abstention there.
- Why / criteria served: "Reasonable and implementable" for judges; Transparency; the client's warning about high-AUC black boxes; turns Stage 2 data access into the team's strongest evidence.
- Differentiation: Most teams will show a demo; we will show a table of where we are wrong.
- Demo moment: Model card: "Leadership abilities kappa 0.62 (n=180); Wounded leadership kappa 0.28 -> AI abstains, interviewer probe only".
- Effort: M ; when: Stage 2 (needs data)
- Risks: Small n; the historical ratings were made by differently calibrated interviewers (so the ceiling on agreement is the human-human agreement, which we also report).
- Confidence: high
- Sources: [source: https://pmc.ncbi.nlm.nih.gov/articles/PMC13520715/]

## I19. Trajectory view: "then -> now" instead of a level
- Insertion point: before / committee (novel)
- What: From the candidate's own narrative, extract dated initiatives with their scope (people involved, duration, resources, result) and render a timeline; the committee sees the slope (from "joined a club at 14" to "ran a district event at 17"), not just the current altitude. No demographic input is used; only what the candidate said. Labeled as context, not a score. Replaces the Stage-1 "Growth Trajectory = current minus school-type baseline", which encoded a demographic proxy.
- Why / criteria served: Mission ("see potential, not background"); Problem (5); Explainability (each point on the timeline is a quote).
- Differentiation: Visual and mission-aligned; nobody else will draw a slope.
- Demo moment: Two candidates with the same current level: one flat line, one steep line; the committee's eyes go to the slope.
- Risks: Rewards candidates with longer résumés or better memory of dates; mitigation: slope is qualitative, displayed not scored; missing dates are fine.
- Effort: S ; when: before Oct 3
- Confidence: medium

## I20. Community evidence channel (novel, higher risk)
- Insertion point: before (novel)
- What: Optional: the candidate nominates one teacher, community member or peer who receives a 3-question structured form in Kazakh/Russian ("Describe one time you saw this person lead others. What exactly did they do? What happened?"), which is processed into the ledger as third-party evidence with a distinct source tag and a low, committee-adjustable weight. Absence of a nomination is never penalized (rural candidates may have no one who will fill in forms).
- Why / criteria served: Triangulation against self-report (Problem 3); mission (community leadership in villages is often invisible on paper). Selection research consistently finds job-specific, behavior-based information (structured interviews, biodata, work samples) among the top predictors [source: https://www.siop.org/tip-article/is-cognitive-ability-the-best-predictor-of-job-performance-new-research-says-its-time-to-think-again/].
- Differentiation: Adds a data source rather than another model on the same data.
- Demo moment: A teacher's Kazakh answer appears as a quote under Leadership abilities with a "third party" tag and its own anchor match.
- Effort: M ; when: Stage 2
- Risks: Forged or coached references, unequal access to referees, minors' privacy; a committee may refuse third-party data entirely. Tag as experimental; committee toggle; fraud checks (rate limiting, template-similarity detection).
- Confidence: low

# Ideas to explicitly exclude and why

- Facial expression / "emotion" analysis from video. HireVue, the largest vendor to ever ship it, dropped it after its own research found it added almost nothing to prediction and after public and regulatory pressure over discrimination against people with atypical affect; its data scientist said content of answers was what predicted [source: https://fortune.com/2021/01/19/hirevue-drops-facial-monitoring-amid-a-i-algorithm-audit/]. For 16-18-year-olds recording on phones in villages, it is also just noise.
- Voice-stress, prosody, "confidence" or "energy" scoring from audio. Directly penalizes manner of speech, which the client lists as a protected dimension. Excluded even as a "soft signal".
- Eye tracking, gaze, background/appearance inference. Same reasons; plus it measures internet quality and housing, i.e., income.
- Social-media scraping or web search on candidates. Illegal or borderline under personal-data law for minors, unverifiable, and rewards the digitally privileged.
- AI-written-text detectors as a penalty or "authenticity score" (our own Stage-1 feature). Detectors misclassify non-native English writing as AI-generated at very high rates and the authors caution against use in evaluative settings [source: https://arxiv.org/abs/2304.02819]. Our language-specific thresholds do not fix the underlying perplexity mechanism. Keep at most a neutral "prepared text detected - probe in interview" note, or drop it entirely in favor of I15 and I2.
- Demographic multipliers inside the score (our own school-type "starting advantage" table). Indefensible in both directions; replaced by flags (I4).
- Any admit/reject prediction model trained on past decisions without per-competency decomposition. The client pre-rejected this in one sentence ("high AUC that cannot explain a single score").
- Live real-time Kazakh transcription as a scoring input during the interview. Error rates are too high [unverified], the interviewer would watch a screen, and a failed live demo on stage is fatal. Offline dictation and notes instead (I8).
- Inferring family status or hardship for Foundation eligibility from text. Foundation eligibility is a declared, documented status assessed by humans; inferring it is both a privacy violation and an invitation to game.
- Quotas or automatic rebalancing of the shortlist by region. Visibility (Cohort Lens in I16) yes; automatic action no; it is a policy decision for humans and an attack surface for critics.

# Suggested 30-second and 3-minute demo narrative for Stage 2

30 seconds (the hook):
"Your methodology already has the answer: nine competencies, ATOLA, BARS. Nobody gave your people the tools to use it at scale. We built one evidence ledger and three views." Click a "High" chip: the video segment highlights with the BARS anchor. Press "swap": the candidate becomes a village Kazakh speaker; the nine bars do not move. Show the phone: the interviewer's one-page pre-brief. "The decision stays with you. The evidence is finally on one screen."

3 minutes (the story, in the client's own order):
1. Before (60s): a candidate's video and mocked ipsative profile flow into the Evidence Ledger. Show one High with quotes, one "insufficient evidence", one Triangulation discrepancy. Run the Scenario Lab for 30 seconds with a judge at the keyboard; the Teamwork tuple appears live. Show the triage queues and the rule that fired for one "clearly irrelevant" case.
2. Inside (40s): hold up the printed Pre-Brief. Dictate a messy Russian note; the Note-to-BARS structurer maps it; the interviewer confirms with two taps; one competency is flagged as uncovered.
3. Committee (40s): Side-by-side compare of two candidates on the same indicator. Disagreement radar. Contrastive tooltip "what would move this to High". Press the Bias Probe: zero flips. Then rerun with the Stage-1 model and show the bars move: "we deleted our own feature after this test." Export the Decision Memo.
4. After (30s): the Growth Map on a phone in Kazakh: three strengths in the candidate's words, two "not seen yet" with a village-feasible next step, the re-application door. A sentence turns red in the Leak Guard: "too close to a test item, rewritten."
5. Close (10s): the model card from the validation harness plan: "where we agree with your committee, where we abstain. Purpose-driven and Wounded leadership stay human."

Recommended priority for the Oct 1-3 demo (S/M items that carry the narrative): I1 skeleton, I3, I4, I7, I8 (notes version), I12, I14, I15, I16 (single-candidate swap), I17, I9 template, I6 re-skin of the existing engine. Stage 2 (Oct 5 - Nov 10, with data and methodology): I2 real ingestion, I5 harness, I6 editor and validation, I8 recording path, I10 against the bank, I11, I13 cohort analytics, I16 cohort ratios, I18, I19 polish, I20 pilot.
