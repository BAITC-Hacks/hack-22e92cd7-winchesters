// Display text for ledger vocabulary. Ids come from backend/ledger/schema.py;
// labels are display only and can change without touching the contract.
// Indicator labels and BARS anchor wording live in backend/ledger/rubric.py and
// are not copied here: until the ledger API returns them (LED-11), a view shows
// the indicator id itself.

import type { CompetencyState, EvidenceState } from "@/lib/ledger";
import type { AtolaComponent, Competency, EvidenceStatus, Source } from "@/lib/types";

export const COMPETENCY_LABELS: Record<Competency, string> = {
  motivation_university: "Motivation for the university",
  motivation_major: "Motivation for the major",
  leadership_abilities: "Leadership abilities",
  teamwork: "Teamwork",
  values: "Values",
  prior_experience: "Prior experience",
  intellect: "Intellect",
  purpose_driven_leadership: "Purpose-driven leadership",
  wounded_leadership: "Wounded leadership",
};

export const STATE_LABELS: Record<CompetencyState, string> = {
  high: "High",
  normal: "Normal",
  weak: "Weak",
  no_evidence: "No evidence",
  reserved: "Rated live",
  not_in_ledger: "Not assessed",
};

export const EVIDENCE_STATE_LABELS: Record<EvidenceState, string> = {
  demonstrated: "Behaviour described",
  claimed_only: "Claimed, not shown",
  no_evidence: "Nothing found",
  live_only: "Ask live only",
  not_in_ledger: "Not assessed yet",
};

export const SOURCE_LABELS: Record<Source, string> = {
  essay: "Essay",
  written_presentation: "Written presentation",
  video_transcript: "Video transcript",
  scenario: "Scenario",
  interview_notes: "Interview notes",
  recommendation_letter: "Recommendation letter",
  ipsative_test: "Ipsative test",
};

export const ATOLA_LABELS: Record<AtolaComponent, string> = {
  action: "Action",
  thinking: "Thinking",
  outcome: "Outcome",
  learnings: "Learnings",
  application: "Application",
  none: "—",
};

export const EVIDENCE_STATUS_LABELS: Record<EvidenceStatus, string> = {
  present: "Shown",
  claimed_only: "Claimed only",
  contradicted: "Contradicted",
  not_assessable: "Not assessable",
};
