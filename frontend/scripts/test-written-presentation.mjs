import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const words = await readFile("src/lib/words.ts", "utf8");
const form = await readFile("src/app/page.tsx", "utf8");
const types = await readFile("src/lib/types.ts", "utf8");
const api = await readFile("src/lib/api.ts", "utf8");
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

// The form no longer asks for it; the server still bounds-checks one if sent.
assert.doesNotMatch(form, /writtenPresentation|written_presentation/);
assert.match(types, /written_presentation: string;/);

// Video: graded by the committee, never analysed by the dashboard.
assert.doesNotMatch(types, /is_mock|VideoAnalysis/);
assert.doesNotMatch(detail, /VideoPanel|onAnalyzeVideo/);
assert.doesNotMatch(api, /video-analysis/);

// An older application's presentation is shown as submitted; no notice when absent.
assert.match(written, /if \(!c\.written_presentation\) return null;/);
assert.doesNotMatch(written, /#[0-9a-fA-F]{3,6}\b/, "WrittenPresentation uses a hex colour");

console.log("INP-01 frontend written-presentation contract passed (retired from the form)");
