#!/usr/bin/env python3
"""Jarvis orchestrator — routes to HeyClicky / Kyla / Quant Mind specialists.

Implements the decision layer of the five-layer stack. Uses keyword routing
and optional subprocess calls to specialist tools when KYLA_JARVIS_DEEP=1.

KYLA appends the user prompt as the final argv entry.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

HEALTH_KEYS = (
    "lab", "hba1c", "biomarker", "cgm", "longevity", "biological age",
    "wearable", "apple health", "glucose", "cholesterol", "vo2", "health",
    "hemoglobin", "a1c",
)
QUANT_KEYS = (
    "forex", "eurusd", "gbpusd", "signal", "backtest", "paper trade",
    "portfolio", "slippage", "london", "nasdaq", "quant", "markets",
)
UI_KEYS = ("clicky", "heyclicky", "helloclicky", "point", "annotate", "screen")


def choose_specialist(prompt: str) -> str:
    p = prompt.lower()
    if any(k in p for k in HEALTH_KEYS):
        return "kyla-health"
    if any(k in p for k in QUANT_KEYS):
        return "quant-mind"
    if any(k in p for k in UI_KEYS):
        return "heyclicky"
    # Morning brief / multi-domain → still jarvis-local summary unless deep
    if "morning" in p or "brief" in p:
        return "multi"
    return "heyclicky"


def run_tool(script: str, prompt: str, timeout: int = 90) -> str:
    path = TOOLS / script
    if not path.is_file():
        return f"[ERROR] Missing {path}"
    try:
        r = subprocess.run(
            [sys.executable, str(path), prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"[ERROR] {script} timed out"
    out = (r.stdout or r.stderr or "").strip()
    return out or f"[INFO] {script} returned empty"


def orchestrate(prompt: str) -> str:
    specialist = choose_specialist(prompt)
    header = [
        "[JARVIS] Orchestrator",
        f"[SPECIALIST] {specialist}",
        f"[PROMPT] {prompt}",
        "[RULE] dry-run safe · health educational · quant paper-only",
        "",
    ]
    deep = os.environ.get("KYLA_JARVIS_DEEP", "1") == "1"

    if not deep:
        header.append(f"[PLAN] Would call specialist `{specialist}` (set KYLA_JARVIS_DEEP=1 to chain).")
        return "\n".join(header)

    if specialist == "multi":
        health = run_tool("kyla_health_agent.py", "morning health drift check educational only")
        quant = run_tool("quant_mind_agent.py", "paper portfolio pulse")
        body = "\n--- HEALTH ---\n" + health + "\n--- QUANT ---\n" + quant
        return "\n".join(header) + body

    script_map = {
        "kyla-health": "kyla_health_agent.py",
        "quant-mind": "quant_mind_agent.py",
        "heyclicky": "heyclicky_bridge.py",
    }
    body = run_tool(script_map[specialist], prompt)
    return "\n".join(header) + body


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt or prompt in {"-h", "--help"}:
        print(__doc__)
        return 0 if prompt else 2
    print(orchestrate(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
