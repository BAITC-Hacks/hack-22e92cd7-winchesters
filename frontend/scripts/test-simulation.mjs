import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const labels = await readFile("src/components/simulation/SimulationLabels.tsx", "utf8");
const panel = await readFile("src/components/candidate/FeynmanPanel.tsx", "utf8");
const teach = await readFile("src/app/teach/page.tsx", "utf8");
const card = await readFile("src/components/dashboard/CandidateCard.tsx", "utf8");
const api = await readFile("src/lib/api.ts", "utf8");
const types = await readFile("src/lib/types.ts", "utf8");

// Every place a simulation result is shown carries the label.
assert.match(labels, /Observed in simulation/);
assert.match(labels, /Weight 0: not part of any score or ranking/);
assert.match(labels, /Cached demo transcript/);
assert.match(panel, /<SimulationLabel/);
assert.match(teach, /<SimulationLabel/);
assert.match(types, /weight: 0;/);

// The cached demo is its own endpoint and its own phase, never a live result.
assert.match(api, /\/api\/feynman\/demo/);
assert.match(api, /\/api\/feynman\/mode/);
assert.match(teach, /phase === "replay"/);
assert.match(teach, /<CachedDemoNotice/);

// The backend never shifted weight to other sections: the card must not say it did.
assert.doesNotMatch(card, /Weight shifted/);
assert.match(card, /Not submitted:/);

console.log("INP-03 frontend simulation contract passed");
