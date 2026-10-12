#!/usr/bin/env python3
"""HeyClicky (helloclicky) interface bridge — front door for Jarvis.

Always-present UI layer stub: accepts a user utterance / context packet and
returns a structured response the real HeyClicky client can speak, point, or
type. Screen capture and computer-use are NOT implemented here; they require
explicit opt-in, allowlists, and R13.

KYLA appends the user prompt as the final argv entry.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY = ROOT / "memory"


def load_profile_snippet() -> dict:
    path = MEMORY / "profile.json"
    if not path.is_file():
        path = MEMORY / "profile.example.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def build_packet(prompt: str) -> dict:
    profile = load_profile_snippet()
    return {
        "layer": "interface",
        "component": "heyclicky",
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "actions": [
            {"type": "speak", "text": None},
            {"type": "annotate", "target": "active_window", "enabled": False},
            {"type": "spawn_agent", "candidates": ["kyla-health", "quant-mind", "jarvis"]},
        ],
        "context_hints": {
            "screen_aware": False,
            "note": "Screen OCR/portal hooks gated until R13 + opt-in",
        },
        "memory_touch": {
            "owner": profile.get("owner"),
            "goals": profile.get("goals", [])[:3],
        },
        "routing_suggestion": _suggest_route(prompt),
    }


def _suggest_route(prompt: str) -> str:
    p = prompt.lower()
    health = (
        "lab", "hba1c", "biomarker", "cgm", "longevity", "biological age",
        "wearable", "apple health", "glucose", "cholesterol", "vo2",
    )
    quant = (
        "forex", "eurusd", "signal", "backtest", "paper trade", "portfolio",
        "slippage", "risk unit", "london session",
    )
    if any(k in p for k in health):
        return "kyla-health"
    if any(k in p for k in quant):
        return "quant-mind"
    return "jarvis"


def format_human(packet: dict) -> str:
    route = packet["routing_suggestion"]
    lines = [
        "[HEYCLICKY] Interface layer active",
        f"[ROUTE→] {route}",
        f"[PROMPT] {packet['prompt']}",
        "[STATUS] Context packet ready (no screen capture; no external send).",
        "[NEXT] python main.py --agent " + route + " --execute \"<same prompt>\"",
        "[DOCS] docs/JARVIS_HEYCLICKY_KYLA.md",
    ]
    return "\n".join(lines)


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt or prompt in {"-h", "--help"}:
        print(__doc__)
        return 0 if prompt else 2
    packet = build_packet(prompt)
    # Human-readable primary output for KYLA CLI
    print(format_human(packet))
    # Machine-readable trailer for future HeyClicky client
    print("---json---")
    print(json.dumps(packet, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
