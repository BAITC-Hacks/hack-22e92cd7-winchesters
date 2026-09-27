import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

// LED-12: every demo view says where its figures came from, and a view with
// nothing behind it says "unavailable — nothing was scored" instead of zeros.
const read = (path) => readFile(path, "utf8");

const ledgerLib = await read("src/lib/ledger.ts");
const backendProvenance = await read("../backend/ledger/provenance.py");
const provenance = await read("src/components/ledger/Provenance.tsx");
const quote = await read("src/components/ledger/EvidenceQuote.tsx");
const detail = await read("src/components/candidate/CandidateDetail.tsx");
const brief = await read("src/components/views/InterviewerBrief.tsx");
const audit = await read("src/components/views/FairnessAudit.tsx");
const dashboard = await read("src/app/dashboard/page.tsx");
const memo = await read("src/app/decision-memo/page.tsx");
const probe = await read("src/components/candidate/CounterfactualProbe.tsx");
const harness = await read("src/components/fairness/EvaluationHarness.tsx");
const unavailable = await read("src/components/ui/Unavailable.tsx");
const types = await read("src/lib/types.ts");
const api = await read("src/lib/api.ts");

// The frontend recognises the hand-authored example by the same marker and
// with the same words as the backend.
const marker = backendProvenance.match(/^HAND_AUTHORED = "([^"]+)"/m)?.[1];
assert.ok(marker, "backend/ledger/provenance.py must define HAND_AUTHORED");
assert.match(ledgerLib, new RegExp(`HAND_AUTHORED = "${marker}"`));
for (const label of ["Illustrative worked example — not from this applicant", "Cached ledger — built offline, not scored live"]) {
  assert.ok(backendProvenance.includes(label), `backend label missing: ${label}`);
  assert.ok(ledgerLib.includes(label), `frontend label missing: ${label}`);
}
assert.match(ledgerLib, /Illustrative, not from this applicant/);

// Every ledger view carries the banner, and every quote in an illustrative
// ledger is tagged, including the pre-brief strengths and the memo.
assert.match(provenance, /ILLUSTRATIVE_LABEL/);
assert.match(provenance, /CACHED_LEDGER_LABEL/);
assert.match(quote, /useIllustrative\(\)/);
assert.match(quote, /<IllustrativeTag \/>/);
assert.match(detail, /<LedgerProvenanceProvider ledger=\{ledger\}>/);
assert.match(detail, /<LedgerSourceBanner ledger=\{ledger\} \/>/);
assert.match(brief, /ledger_provenance\?\.illustrative/);
assert.match(memo, /memo\.ledger_provenance/);
assert.match(memo, /<IllustrativeTag \/>/);
assert.match(memo, /Example levels \(not AI\)/);
assert.match(types, /ledger_provenance: LedgerProvenance;/);

// No figures without a source: the example is not cohort data.
assert.match(audit, /filter\(\(l\) => !isIllustrative\(l\)\)/);
assert.doesNotMatch(audit, /Until\s+LED-11 this is the LED-03 fixture/);

// Baseline stand-ins are named as such wherever they replace a model result.
assert.match(probe, /deterministic baseline, no model call/);
assert.match(harness, /deterministic baseline, no model call/);

// Neutral empty states, never a red error or a 404 asked for on purpose.
assert.match(unavailable, /Unavailable — nothing was scored/);
assert.match(detail, /Unavailable — nothing was scored/);
assert.doesNotMatch(dashboard, /api\.ledger\s*\.get\(/);
assert.match(api, /\/api\/fairness\/historical\/status/);
assert.match(api, /\/api\/fairness\/heldout\/status/);
for (const [page, status] of [
  ["src/app/model-card/page.tsx", "historicalStatus"],
  ["src/app/funder-memo/page.tsx", "heldoutStatus"],
  ["src/app/reproducibility/page.tsx", "heldoutStatus"],
]) {
  const source = await read(page);
  assert.match(source, new RegExp(`api\\.fairness\\s*\\.${status}\\(\\)`), `${page} must ask for status first`);
  assert.match(source, /<Unavailable /, `${page} must show the neutral state`);
}

console.log("LED-12 frontend demo-offline contract passed");
