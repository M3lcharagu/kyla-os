#!/usr/bin/env python3
"""Kyla health / longevity specialist (research framing only).

Domain expert backend for biomarkers, trends, and protocol *ideas*.
Does NOT diagnose, prescribe, or replace a clinician.

Optionally reads local memory/profile.json. Never uploads health data.
KYLA appends the user prompt as the final argv entry.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "memory"

DISCLAIMER = (
    "Educational / research framing only. Not medical advice, diagnosis, or "
    "treatment. Confirm any action with a qualified clinician."
)


def load_profile() -> dict:
    for name in ("profile.json", "profile.example.json"):
        path = MEMORY / name
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return {}


def analyze(prompt: str) -> str:
    profile = load_profile()
    topics = (profile.get("health_flags") or {}).get("topics_of_interest") or []
    jobs = (profile.get("health_flags") or {}).get("recurring_jobs") or []

    lines = [
        "[KYLA-HEALTH] Specialist response",
        f"[TS] {datetime.now(timezone.utc).isoformat()}",
        f"[DISCLAIMER] {DISCLAIMER}",
        f"[PROMPT] {prompt}",
        "",
        "Structured outline (fill with clinician-validated data only):",
        "  1. What was observed (source + date — attach if local lab note exists)",
        "  2. Trend direction vs prior points (if any in memory/health/)",
        "  3. Research-context risk factors (population studies, not your diagnosis)",
        "  4. Questions to ask your clinician",
        "  5. Lifestyle protocol *ideas* to discuss (sleep, activity, nutrition) — not orders",
        "",
    ]
    if topics:
        lines.append(f"[PROFILE TOPICS] {', '.join(topics)}")
    enabled_jobs = [j for j in jobs if j.get("enabled")]
    if enabled_jobs:
        lines.append(f"[ACTIVE KYLA-CLICKY JOBS] {len(enabled_jobs)}")
    else:
        lines.append(
            "[KYLA-CLICKY] No enabled recurring jobs. "
            "Enable in memory/profile.json → health_flags.recurring_jobs."
        )

    # Optional local LLM enrichment if Ollama is up
    if os.environ.get("KYLA_HEALTH_USE_OLLAMA", "0") == "1":
        try:
            from tools.ollama_agent import chat  # type: ignore
        except Exception:
            try:
                sys.path.insert(0, str(ROOT / "tools"))
                from ollama_agent import chat  # type: ignore
            except Exception:
                chat = None  # type: ignore
        if chat:
            sys_msg = (
                "You are Kyla, a health research assistant. "
                + DISCLAIMER
                + " Be concise. Prefer questions for a clinician over directives."
            )
            try:
                # reuse ollama via env; inject disclaimer in user turn
                body = chat(f"{sys_msg}\n\nUser: {prompt}")
                lines.extend(["", "[LOCAL MODEL NOTES]", body])
            except Exception as exc:
                lines.append(f"[OLLAMA SKIP] {exc}")

    lines.extend(
        [
            "",
            "[MEMORY] Local only under memory/ — do not commit PHI.",
            "[DOCS] docs/JARVIS_HEYCLICKY_KYLA.md",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt or prompt in {"-h", "--help"}:
        print(__doc__)
        return 0 if prompt else 2
    print(analyze(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
