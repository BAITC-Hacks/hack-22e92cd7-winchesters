"""Content hashes for the rubric and prompt versions a ledger is stamped with (LED-13).

A version string is only honest if it names fixed content. This module hashes
the content itself: the full rubric (every anchor, probe and flag) and the
prompt templates of both pipeline stages. `versions.lock.json` records the hash
of every released version, so a stored ledger can be traced back to what it was
built under, and `tests/test_led13_versions.py` fails when the rubric or a
prompt changes without a version bump.

When the extended methodology arrives, replacing the provisional scales is a
rubric change like any other: bump `RUBRIC_VERSION`, run

    python -m backend.ledger.versions --lock

and commit the new lock entry next to the rubric.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from backend.ledger import extract, pipeline, rate
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC, RUBRIC_VERSION

Kind = Literal["rubric", "prompt"]

LOCK_FILE = Path(__file__).resolve().parent / "versions.lock.json"


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    return value


def _sha256(body: Any) -> str:
    text = body if isinstance(body, str) else json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rubric_content_hash() -> str:
    """sha256 of every competency's scale, in the order the pipeline runs them."""
    return _sha256([_plain(RUBRIC[competency]) for competency in COMPETENCY_ORDER if competency in RUBRIC])


def prompt_content_hash() -> str:
    """sha256 of both stages' system prompts, output schemas and prompt builders."""
    builders = (extract._indicator_block, extract.build_prompt, rate._anchor_block, rate._evidence_block, rate.build_prompt)
    return _sha256({
        "extract": {"system": extract.EXTRACTION_SYSTEM, "schema": extract.EXTRACTION_SCHEMA},
        "rate": {"system": rate.RATING_SYSTEM, "schema": rate.RATING_SCHEMA},
        "builders": [inspect.getsource(builder) for builder in builders],
    })


def current() -> dict[Kind, tuple[str, str]]:
    return {"rubric": (RUBRIC_VERSION, rubric_content_hash()), "prompt": (pipeline.PROMPT_VERSION, prompt_content_hash())}


def read_lock(path: Path = LOCK_FILE) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"rubric": {}, "prompt": {}}


def known_hash(kind: Kind, version: str, path: Path = LOCK_FILE) -> str | None:
    """The locked content hash of a released version, or None if it was never released."""
    return read_lock(path).get(kind, {}).get(version)


def lock(path: Path = LOCK_FILE) -> dict[str, dict[str, str]]:
    """Record the current versions. Refuses to rewrite the hash of a released version."""
    data = read_lock(path)
    for kind, (version, digest) in current().items():
        locked = data.setdefault(kind, {}).get(version)
        if locked is not None and locked != digest:
            raise ValueError(f"{kind} {version} changed after release; bump the version instead of relocking it")
        data[kind][version] = digest
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps(lock(), indent=2))
    else:
        print(json.dumps({kind: {"version": version, "sha256": digest, "locked": known_hash(kind, version) == digest}
                          for kind, (version, digest) in current().items()}, indent=2))
