import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const words = await readFile("src/lib/words.ts", "utf8");
const form = await readFile("src/app/page.tsx", "utf8");
const types = await readFile("src/lib/types.ts", "utf8");
const video = await readFile("src/components/candidate/VideoPanel.tsx", "utf8");
const written = await readFile("src/components/candidate/WrittenPresentation.tsx", "utf8");
const detail = await readFile("src/components/candidate/CandidateDetail.tsx", "utf8");
const models = await readFile("../backend/models.py", "utf8");

// The form and the server agree on the bounds.
const bound = (source, name) => Number(source.match(new RegExp(`${name}\\s*=\\s*(\\d+)`))[1]);
assert.equal(bound(words, "WRITTEN_PRESENTATION_MIN_WORDS"), 150);
assert.equal(bound(words, "WRITTEN_PRESENTATION_MAX_WORDS"), 300);
assert.equal(bound(models, "WRITTEN_PRESENTATION_MIN_WORDS"), bound(words, "WRITTEN_PRESENTATION_MIN_WORDS"));
assert.equal(bound(models, "WRITTEN_PRESENTATION_MAX_WORDS"), bound(words, "WRITTEN_PRESENTATION_MAX_WORDS"));

// Words are counted by whitespace, never by a Latin-only pattern.
assert.match(words, /split\(\/\\s\+\/u\)/);
assert.doesNotMatch(words, /\[a-zA-Z/);
assert.doesNotMatch(words, /\\w/);

// The counting rule itself, run on Kazakh and code-switched text. The body of
// countWords is lifted from words.ts so the check runs the real code.
const body = words.match(/export function countWords\(text: string\): number \{([\s\S]*?)\n\}/)[1];
const countWords = new Function("text", body);
const kazakh = "Мен ауылдағы балаларға математикадан тегін сабақ бердім және олардың қиындықтарын түсіндім".split(" ");
const text = (n) => Array.from({ length: n }, (_, i) => kazakh[i % kazakh.length]).join(" ");
assert.equal(countWords(text(149)), 149);
assert.equal(countWords(text(150)), 150);
assert.equal(countWords("Біз volunteers тобын құрдық,\nпотом мы   собрали"), 7);
assert.equal(countWords("   "), 0);

// The form validates before submitting, shows a counter and sends the field.
assert.match(form, /writtenPresentationError\(writtenPresentation\)/);
assert.match(form, /written_presentation: writtenPresentation/);
assert.match(form, /data-slot="presentation-word-count"/);
assert.match(types, /written_presentation: string;/);

// Video: no mock, no numbers without a transcript, neutral wording.
assert.doesNotMatch(types, /is_mock/);
assert.doesNotMatch(video, /is_mock|OPENAI|Whisper/);
assert.match(types, /"analyzed" \| "no_transcript" \| "unavailable"/);
assert.match(types, /motivation_score: number \| null;/);
assert.match(video, /No transcript — nothing was scored\./);
assert.match(video, /analysis\.status !== "analyzed"/);

// A missing written presentation reads as no evidence, through LevelChip only.
assert.match(written, /<LevelChip state="no_evidence"/);
assert.match(written, /This is not a weak result\./);
assert.match(detail, /<WrittenPresentationMissing \/>/);

// Design tokens, not hex codes, in the new and rewritten components.
for (const [name, source] of [["VideoPanel", video], ["WrittenPresentation", written]]) {
  assert.doesNotMatch(source, /#[0-9a-fA-F]{3,6}\b/, `${name} uses a hex colour`);
}

console.log("INP-01 frontend written-presentation contract passed");
