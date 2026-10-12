#!/usr/bin/env python3
"""Quant Mind specialist bridge — paper research only.

Routes finance/market prompts toward kyla-quant style workflows without any
live order path. Safe default: structured paper checklist + memory note.

KYLA appends the user prompt as the final argv entry.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "memory"
QUANT_SIBLING = ROOT.parent / "kyla-quant"

BOUNDARY = (
    "Paper / research only. Not financial advice. No live execution in this scaffold."
)


def load_quant_prefs() -> dict:
    for name in ("profile.json", "profile.example.json"):
        path = MEMORY / name
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("quant_prefs") or {}
            except (OSError, json.JSONDecodeError):
                continue
    return {"mode": "paper_only"}


def respond(prompt: str) -> str:
    prefs = load_quant_prefs()
    sibling = QUANT_SIBLING.is_dir()
    lines = [
        "[QUANT-MIND] Specialist response",
        f"[TS] {datetime.now(timezone.utc).isoformat()}",
        f"[BOUNDARY] {BOUNDARY}",
        f"[MODE] {prefs.get('mode', 'paper_only')}",
        f"[PROMPT] {prompt}",
        "",
        "Paper workflow checklist:",
        "  1. Define setup + invalidation (no vague 'feels good')",
        "  2. Data quality: source, timestamp, timezone",
        "  3. Risk unit and max daily loss (paper)",
        "  4. Journal entry after decision",
        "  5. R13 before any automation that touches external brokers",
        "",
        f"[SIBLING kyla-quant] {'found at ' + str(QUANT_SIBLING) if sibling else 'not cloned beside kyla-os'}",
    ]
    if sibling:
        lines.append(
            "  Hint: cd ../kyla-quant && python3 -m http.server 8080 --directory dashboard"
        )
    focus = prefs.get("focus") or []
    if focus:
        lines.append(f"[FOCUS] {', '.join(focus)}")
    lines.extend(
        [
            "",
            "[DOCS] Sibling kyla-quant docs/LOOPHOLES.md + docs/JARVIS_BLUEPRINT.md",
            "[LOCAL] docs/JARVIS_HEYCLICKY_KYLA.md",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt or prompt in {"-h", "--help"}:
        print(__doc__)
        return 0 if prompt else 2
    print(respond(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
