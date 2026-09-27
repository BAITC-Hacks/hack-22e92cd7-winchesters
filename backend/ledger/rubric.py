"""The nine competencies, their indicators and their BARS anchors.

Two of the nine are public: inVision U published the full behavioural scale for
Leadership abilities and for Wounded leadership, and those are reproduced here
close to their wording. The other seven are drafted from the one-line
descriptions in the same deck and are marked `provisional`. The real scales
arrive with the extended methodology on Oct 5 and replace them wholesale, which
is why `RUBRIC_VERSION` is stamped onto every ledger: a score is only comparable
to another score computed under the same version.

Weights, cut-offs and the item bank are not here and must not be added. They
belong to inVision U and Talent Craft, arrive as configuration, and are
displayed in the product as theirs.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.ledger.schema import Competency, Level

RUBRIC_VERSION = "provisional-0.1"


@dataclass(frozen=True)
class Indicator:
    """One behavioural thread, with what it looks like at each level."""

    id: str
    label: str
    weak: str
    normal: str
    high: str

    def anchor(self, level: Level) -> str:
        return {Level.WEAK: self.weak, Level.NORMAL: self.normal, Level.HIGH: self.high}.get(level, "")


@dataclass(frozen=True)
class CompetencyRubric:
    """One of the nine blocks."""

    competency: Competency
    label: str
    description: str
    indicators: tuple[Indicator, ...]
    question: str
    probes: tuple[str, ...]
    ai_may_rate: bool = True
    provisional: bool = True


# ── 3. Leadership abilities — full public scale ────────────────────

_LEADERSHIP = CompetencyRubric(
    competency=Competency.LEADERSHIP_ABILITIES,
    label="Лидерские способности / Leadership abilities",
    description=(
        "Already demonstrated leadership through real actions: where they took "
        "initiative, how they involved people, whether they saw it through, and "
        "whether they took responsibility for the consequences."
    ),
    indicators=(
        Indicator(
            id="lead.concrete_examples",
            label="Concreteness of the example",
            weak="Gives no concrete situations, speaks in general phrases.",
            normal="Has some leadership examples, but limited in scale.",
            high="Gives clear, concrete examples of leadership actions.",
        ),
        Indicator(
            id="lead.initiative",
            label="Initiative",
            weak="Shows no initiative; the role is rather passive.",
            normal="Takes responsibility, but more out of necessity than initiative.",
            high="Shows initiative: launches projects, brings people together.",
        ),
        Indicator(
            id="lead.organizing_others",
            label="Organising others",
            weak="Cannot organise others; avoids distributing tasks.",
            normal="Can organise a small process within a group.",
            high="Distributes tasks, supports others, resolves conflicts.",
        ),
        Indicator(
            id="lead.responsibility_under_difficulty",
            label="Responsibility under difficulty",
            weak="Difficulties cause confusion; avoids responsibility.",
            normal="Copes with difficulties, but without a systematic approach.",
            high=(
                "Takes responsibility for decisions and their consequences, corrects "
                "mistakes, stays resilient and finishes even in hard circumstances."
            ),
        ),
        Indicator(
            id="lead.result_and_contribution",
            label="Result and own contribution",
            weak="Finds it hard to describe a real result or their own contribution.",
            normal="Results exist, but their role in them is moderate or partial.",
            high="Describes the result and their personal contribution to it clearly.",
        ),
    ),
    question=(
        "Расскажите про самый крутой пример, где вы были лидером: какую цель вы "
        "поставили, кого вовлекли, что именно вы делали, и какой результат получился?"
    ),
    probes=(
        "Почему это было важно именно вам?",
        "Как вы измеряли результат?",
        "Что было вашим личным вкладом, а не команды?",
    ),
    provisional=False,
)


# ── 9. Wounded leadership — full public scale, humans rate it ──────

_WOUNDED = CompetencyRubric(
    competency=Competency.WOUNDED_LEADERSHIP,
    label="Wounded leadership",
    description=(
        "Leadership formed by lived hard experience. The point of the block is not "
        "the hardship: it is whether the past distorts the leadership style into "
        "harshness, control or a victim position."
    ),
    indicators=(
        Indicator(
            id="wound.awareness_of_influence",
            label="Awareness of the influence",
            weak="Unaware of the influence of hard experience, or avoids the topic.",
            normal="Aware of some elements, but not of the overall influence.",
            high="Clearly aware of the experience and how it drives wanting to help others.",
        ),
        Indicator(
            id="wound.empathy",
            label="Empathy toward others",
            weak="Examples of help or empathy are absent or formal.",
            normal="Empathy is present but unstable.",
            high="Deep empathy and sensitivity to other people's pain.",
        ),
        Indicator(
            id="wound.experience_as_resource",
            label="Experience used as a resource",
            weak="Does not use personal experience to support others.",
            normal="Sometimes uses personal experience to support others.",
            high="Uses the experience as a resource: supports, holds, acts sustainably.",
        ),
        Indicator(
            id="wound.absence_of_distortion",
            label="Absence of harshness or victimhood",
            weak="Shows harshness or a need to prove significance; slips into blame or a victim position.",
            normal="Leadership is broadly constructive, but the past sometimes affects behaviour.",
            high="Does not slide into harshness, control or victimhood.",
        ),
        Indicator(
            id="wound.positive_change_examples",
            label="Concrete examples of positive change",
            weak="Cannot point to change that came out of the experience.",
            normal="Conclusions exist but are applied selectively.",
            high="Gives concrete examples where the experience became a source of positive change.",
        ),
    ),
    question=(
        "Были ли у вас сложные ситуации или трудный опыт, который заметно повлиял на "
        "вас? Что вы из этого вынесли, и как это проявляется в ваших решениях и "
        "отношении к людям сейчас?"
    ),
    probes=(
        "Что конкретно изменилось в вашем поведении?",
        "Какие свои триггеры вы знаете?",
        "Как вы их отслеживаете и сдерживаете?",
    ),
    # The interviewer asks this live and rates it. The AI may only surface
    # indicator observations and attention flags for a human to verify, because
    # judging how a minor narrates hardship is a clinical-adjacent inference and
    # narrated growth is weak evidence of real growth.
    ai_may_rate=False,
    provisional=False,
)


def _provisional(
    competency: Competency,
    label: str,
    description: str,
    indicators: tuple[Indicator, ...],
    ai_may_rate: bool = True,
) -> CompetencyRubric:
    """Build a placeholder scale for a competency whose BARS is not public yet."""
    return CompetencyRubric(
        competency=competency,
        label=label,
        description=description,
        indicators=indicators,
        question="",
        probes=(),
        ai_may_rate=ai_may_rate,
        provisional=True,
    )


def _indicator(prefix: str, name: str, label: str, weak: str, normal: str, high: str) -> Indicator:
    return Indicator(id=f"{prefix}.{name}", label=label, weak=weak, normal=normal, high=high)


_PROVISIONAL = (
    _provisional(
        Competency.MOTIVATION_UNIVERSITY,
        "Мотивация на университет / Motivation for the university",
        "Why inVision U specifically, rather than a good university nearby.",
        (
            _indicator("motu", "specificity", "Specific to this university",
                       "Reasons would fit any university.",
                       "Names some things specific to inVision U.",
                       "Connects specific features of the programme to their own plans."),
            _indicator("motu", "informed", "Informed choice",
                       "No sign of having looked into it.",
                       "Knows the basics of the programme.",
                       "Refers to concrete details of the curriculum, mission or community."),
            _indicator("motu", "fit", "Fit with their own path",
                       "No link between the university and their own trajectory.",
                       "A general link is stated.",
                       "Explains what they would do here that they could not do elsewhere."),
        ),
    ),
    _provisional(
        Competency.MOTIVATION_MAJOR,
        "Мотивация на специальность / Motivation for the major",
        "Sees the link between themselves, the major and their plans.",
        (
            _indicator("motm", "understanding", "Understanding of the field",
                       "Describes the field in slogans.",
                       "Describes what the field involves in broad terms.",
                       "Describes concretely what people in this field actually do."),
            _indicator("motm", "evidence_of_interest", "Evidence of prior interest",
                       "No activity connected to the field.",
                       "Some exposure, mostly through school.",
                       "Self-directed work in the field before applying."),
            _indicator("motm", "forward_link", "Link to plans",
                       "No stated plan beyond admission.",
                       "General plans.",
                       "A concrete plan that requires this major."),
        ),
    ),
    _provisional(
        Competency.TEAMWORK,
        "Умение работать в команде / Teamwork",
        "A 'we' orientation while remaining personally accountable.",
        (
            _indicator("team", "we_orientation", "Orientation to the team",
                       "Speaks only of personal contribution, or only of the group with no own role.",
                       "Describes both, unevenly.",
                       "Describes their own contribution inside a shared result."),
            _indicator("team", "disagreement", "Handling disagreement",
                       "Avoids disagreement or defends their position at any cost.",
                       "Handles disagreement case by case.",
                       "Helps people hear each other and brings the group back to the task."),
            _indicator("team", "accountability", "Accountability to others",
                       "Does not mention obligations to teammates.",
                       "Mentions them in general terms.",
                       "Gives an example of carrying a commitment that others depended on."),
        ),
    ),
    _provisional(
        Competency.VALUES,
        "Ценности / Values",
        "Contribution and ethics, not only personal gain.",
        (
            _indicator("val", "beyond_self", "Beyond personal gain",
                       "Motivation framed entirely as personal benefit.",
                       "Mentions benefit to others in general terms.",
                       "Gives an instance of choosing a shared good over a personal one."),
            _indicator("val", "ethical_choice", "Ethical choice under pressure",
                       "No example; or describes taking the shortcut without reflection.",
                       "Describes an ethical question without resolving it.",
                       "Describes a concrete choice and what it cost them."),
            _indicator("val", "consistency", "Consistency across sources",
                       "Stated values contradict described behaviour.",
                       "Values and behaviour are broadly aligned.",
                       "Behaviour across several stories shows the same value."),
        ),
    ),
    _provisional(
        Competency.PRIOR_EXPERIENCE,
        "Предыдущий реальный опыт / Prior real experience",
        "Projects, work, volunteering, initiatives.",
        (
            _indicator("prio", "reality", "Reality of the experience",
                       "Roles named with nothing behind them.",
                       "Real activity, modest in scope or duration.",
                       "Sustained activity with describable outcomes."),
            _indicator("prio", "ownership", "Ownership",
                       "Participated in what others organised.",
                       "Took a defined role inside someone else's structure.",
                       "Started or substantially shaped the thing themselves."),
            _indicator("prio", "consequences", "Consequences they can describe",
                       "Cannot say what came of it.",
                       "Describes what happened in general terms.",
                       "Describes what changed, for whom, and how they know."),
        ),
    ),
    _provisional(
        Competency.INTELLECT,
        "Интеллект / Intellect",
        (
            "Understanding the complex and applying it. Explicitly not grades: "
            "the deck lists academic performance as something that does not measure "
            "this."
        ),
        (
            _indicator("int", "explains_complexity", "Explains something complex simply",
                       "Cannot unpack an idea beyond restating it.",
                       "Explains it, leaning on memorised phrasing.",
                       "Rebuilds the idea in their own terms for a listener who lacks the background."),
            _indicator("int", "transfer", "Transfer to a new situation",
                       "No example of applying an idea elsewhere.",
                       "Applies it within the same setting.",
                       "Applies a lesson in a genuinely different situation."),
            _indicator("int", "revises", "Revises on new information",
                       "Holds the position regardless of what they encounter.",
                       "Adjusts when told directly.",
                       "Describes changing their mind and what caused it."),
        ),
    ),
    _provisional(
        Competency.PURPOSE_DRIVEN_LEADERSHIP,
        "Purpose-driven leadership",
        "Leadership grounded in meaning and mission.",
        (
            _indicator("purp", "why_beyond_self", "A 'why' larger than themselves",
                       "Purpose is stated as ambition alone.",
                       "A larger purpose is named but not connected to action.",
                       "The purpose visibly drives specific choices they made."),
            _indicator("purp", "sustained_action", "Sustained action toward it",
                       "One-off or declared only.",
                       "Episodic action.",
                       "A pattern of action over time pointing the same way."),
            _indicator("purp", "cost", "Willingness to bear a cost",
                       "No cost described.",
                       "Minor cost described.",
                       "Describes giving something up for the purpose, concretely."),
        ),
        # The deck calls this one of the two hardest to automate and most
        # valuable to get right. Same treatment as wounded leadership until
        # agreement with committee ratings is measured on historical data.
        ai_may_rate=False,
    ),
)


RUBRIC: dict[Competency, CompetencyRubric] = {
    rubric.competency: rubric
    for rubric in (_LEADERSHIP, _WOUNDED, *_PROVISIONAL)
}

# The order the committee card and the interviewer brief render in: the deck's order.
COMPETENCY_ORDER: tuple[Competency, ...] = (
    Competency.MOTIVATION_UNIVERSITY,
    Competency.MOTIVATION_MAJOR,
    Competency.LEADERSHIP_ABILITIES,
    Competency.TEAMWORK,
    Competency.VALUES,
    Competency.PRIOR_EXPERIENCE,
    Competency.INTELLECT,
    Competency.PURPOSE_DRIVEN_LEADERSHIP,
    Competency.WOUNDED_LEADERSHIP,
)


def indicators_of(competency: Competency) -> tuple[Indicator, ...]:
    """Indicators for one competency, or an empty tuple if it is unknown."""
    rubric = RUBRIC.get(competency)
    return rubric.indicators if rubric else ()


def ai_may_rate(competency: Competency) -> bool:
    """Whether the AI is allowed to produce a level for this competency at all."""
    rubric = RUBRIC.get(competency)
    return bool(rubric and rubric.ai_may_rate)
