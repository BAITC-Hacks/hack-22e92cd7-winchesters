import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const api = await readFile("src/lib/api.ts", "utf8");
const types = await readFile("src/lib/types.ts", "utf8");
const view = await readFile("src/components/views/InterviewerBrief.tsx", "utf8");

assert.match(api, /preBrief: \(candidateId: string\)/);
assert.match(api, /\/api\/committee\/pre-brief/);
assert.match(types, /score_withheld: true/);
assert.match(types, /canonical: string/);
assert.match(view, /Canonical probe:/);
assert.match(view, /preBrief\.strengths\.map/);
assert.match(view, /discrepancy_alerts/);

console.log("COM-06 frontend pre-brief contract passed");