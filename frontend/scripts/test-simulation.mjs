import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const labels = await readFile("src/components/simulation/SimulationLabels.tsx", "utf8");
const panel = await readFile("src/components/candidate/ScenarioPanel.tsx", "utf8");
const page = await readFile("src/app/scenarios/page.tsx", "utf8");
const card = await readFile("src/components/dashboard/CandidateCard.tsx", "utf8");
const api = await readFile("src/lib/api.ts", "utf8");
const types = await readFile("src/lib/types.ts", "utf8");

// The committee sees every scenario result labelled, with weight zero.
assert.match(labels, /Observed in simulation/);
assert.match(labels, /Weight 0: not part of any score or ranking/);
assert.match(labels, /Demo mode · scripted partner/);
assert.match(panel, /<SimulationLabel/);
assert.match(types, /weight: 0;/);

// The applicant chooses a language and never sees a level or the competency.
assert.match(page, /LANGUAGE_NAMES/);
assert.match(page, /"kk"|kk:/);
assert.doesNotMatch(page, /LevelChip|competency\]/);
assert.match(api, /\/api\/scenarios\/result\//);

// No child persona is left anywhere on either side.
for (const source of [labels, panel, page]) assert.doesNotMatch(source, /Arman|10-year-old|10 y\.o\./);

// The backend never shifted weight to other sections: the card must not say it did.
assert.doesNotMatch(card, /Weight shifted/);
assert.match(card, /Not submitted:/);

console.log("INP-04 frontend scenario contract passed");
