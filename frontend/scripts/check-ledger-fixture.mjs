// Fails when the frontend copy of the LED-03 fixture drifts from the backend one.
//
// The frontend renders its views from frontend/src/lib/fixtures/ledger_example.json
// until LED-11 wires the real ledger API. The source of truth is
// backend/ledger/fixtures/ledger_example.json, which is generated from
// backend/ledger/schema.py and owned by both reviewers. Runs as part of
// `npm run lint`, which CI already calls.
//
// To resync after the backend fixture changes:
//   cp backend/ledger/fixtures/ledger_example.json frontend/src/lib/fixtures/

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { isDeepStrictEqual } from "node:util";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const backendPath = resolve(here, "../../backend/ledger/fixtures/ledger_example.json");
const frontendPath = resolve(here, "../src/lib/fixtures/ledger_example.json");

const read = (path) => JSON.parse(readFileSync(path, "utf8"));
const backend = read(backendPath);
const frontend = read(frontendPath);

if (!isDeepStrictEqual(backend, frontend)) {
  console.error(
    "Ledger fixture out of sync.\n" +
      `  source of truth: ${backendPath}\n` +
      `  frontend copy:   ${frontendPath}\n` +
      "Copy the backend file over the frontend one, then check the views still render.",
  );
  process.exit(1);
}
console.log(`Ledger fixture in sync (schema_version ${backend.schema_version}).`);
