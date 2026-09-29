import type { Candidate } from "@/lib/types";
import { countWords } from "@/lib/words";
import { Section } from "../ui/Section";

/** A written presentation from an application sent before the form retired it.
 * New applications have none, and its absence is not shown as anything. */
export function WrittenPresentationSection({ candidate: c }: { candidate: Candidate }) {
  if (!c.written_presentation) return null;
  return (
    <Section title="Written Presentation">
      <p className="text-sm text-ink-3 mb-2">{countWords(c.written_presentation)} words</p>
      <div className="bg-muted rounded-2xl p-5 text-base whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
        {c.written_presentation}
      </div>
    </Section>
  );
}
