/**
 * Slot for the contrastive tooltip (LED-09 field, LED-06 design): what evidence
 * would move this competency to the next level, in the anchor's own words.
 * A native <details> for now, so it works on touch and in print without a
 * tooltip library; the designer's version replaces the markup, not the prop.
 */
export function ContrastiveHint({ text }: { text: string }) {
  if (!text) return null;
  return (
    <details data-slot="contrastive" className="text-xs text-ink-2">
      <summary className="cursor-pointer select-none text-ink-3 hover:text-ink">Next level?</summary>
      <p className="mt-1 max-w-prose">{text}</p>
    </details>
  );
}
