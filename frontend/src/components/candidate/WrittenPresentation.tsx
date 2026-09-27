import type { Candidate } from "@/lib/types";
import { countWords } from "@/lib/words";
import { LevelChip } from "../ledger/LevelChip";
import { Section } from "../ui/Section";

/** Shown wherever the written presentation is missing (INP-01): no evidence
 * came from it, which is not the same as weak evidence. */
export function WrittenPresentationMissing() {
  return (
    <div
      data-slot="written-presentation-missing"
      className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-subtle px-5 py-4"
    >
      <LevelChip state="no_evidence" small />
      <p className="text-sm text-ink-2">
        No written presentation on file, so no evidence in this ledger comes from it. This is not a weak result.
      </p>
    </div>
  );
}

/** The canonical presentation input, as submitted. */
export function WrittenPresentationSection({ candidate: c }: { candidate: Candidate }) {
  return (
    <Section title="Written Presentation">
      {c.written_presentation ? (
        <>
          <p className="text-sm text-ink-3 mb-2">{countWords(c.written_presentation)} words</p>
          <div className="bg-muted rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
            {c.written_presentation}
          </div>
        </>
      ) : (
        <WrittenPresentationMissing />
      )}
    </Section>
  );
}
