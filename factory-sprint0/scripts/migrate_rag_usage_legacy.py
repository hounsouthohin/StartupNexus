"""
Migrate legacy rag_usage.jsonl entries to the current schema.

- Legacy format had "docs": [{rank, category, source, tech, snippet, ...}]
- Current format expects: doc_ids, scores, snippet

This script preserves legacy docs in "legacy_docs" and normalizes fields.
It writes a new file: logs/metrics/rag_usage.migrated.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path


def _normalize_event(evt: dict) -> dict:
    if "doc_ids" not in evt:
        evt["doc_ids"] = []
    if "scores" not in evt:
        evt["scores"] = []
    if "snippet" not in evt:
        evt["snippet"] = ""

    if "docs" in evt and "legacy_docs" not in evt:
        legacy_docs = evt.pop("docs")
        evt["legacy_docs"] = legacy_docs
        if not evt["snippet"] and isinstance(legacy_docs, list) and legacy_docs:
            first = legacy_docs[0]
            if isinstance(first, dict):
                evt["snippet"] = str(first.get("snippet", ""))[:180]
        evt["migrated_from_legacy"] = True

    return evt


def main() -> int:
    src = Path("logs/metrics/rag_usage.jsonl")
    if not src.exists():
        print("Source file not found:", src)
        return 1

    dst = Path("logs/metrics/rag_usage.migrated.jsonl")
    migrated = 0
    total = 0

    lines = src.read_text(encoding="utf-8").splitlines()
    with dst.open("w", encoding="utf-8") as f:
        for line in lines:
            if not line.strip():
                continue
            total += 1
            try:
                evt = json.loads(line)
            except Exception:
                continue
            evt = _normalize_event(evt)
            if evt.get("migrated_from_legacy"):
                migrated += 1
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    print(f"Migrated {migrated}/{total} events to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
