// Written presentation bounds (INP-01). Mirrors backend/models.py; the server
// enforces the same rule, this only lets the form say so before submitting.
// Form validation only: length is never a scoring input.
export const WRITTEN_PRESENTATION_MIN_WORDS = 150;
export const WRITTEN_PRESENTATION_MAX_WORDS = 300;

/** Whitespace-separated words in any script, so Kazakh, Russian and
 * code-switched text count the same way as English (no Latin-only regex). */
export function countWords(text: string): number {
  return text.split(/\s+/u).filter(Boolean).length;
}

/** Why a written presentation is out of bounds, or null when it is fine. */
export function writtenPresentationError(text: string): string | null {
  const words = countWords(text);
  if (words >= WRITTEN_PRESENTATION_MIN_WORDS && words <= WRITTEN_PRESENTATION_MAX_WORDS) return null;
  return `The written presentation must be ${WRITTEN_PRESENTATION_MIN_WORDS}–${WRITTEN_PRESENTATION_MAX_WORDS} words in any language; it has ${words}.`;
}
