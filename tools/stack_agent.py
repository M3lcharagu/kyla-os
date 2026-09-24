#!/usr/bin/env python3
"""Room suite operator. KYLA appends the user prompt as the last argv.

Runs the suite's first-class tools (lazy bootstrap) then Ollama when needed.
Never calls paid cloud LLM APIs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.catalog import find, load_stack, match_prompt, suite_for_room, tools_for_suite  # noqa: E402
from integrations.runtime import run_item  # noqa: E402
from integrations.stack import ensure_suite  # noqa: E402


def operate(suite: str, prompt: str) -> int:
    tools = tools_for_suite(suite)
    print(f"[SUITE] {suite} tools={tools}")
    ensure_suite(tools)
    matched = match_prompt(prompt)
    if matched and matched.get("id") in tools:
        return run_item(matched, [prompt])
    defaults = {
        "video": "clip",
        "code": "gitingest",
        "write": "prompts",
        "design": "awesome-design-md",
        "study": "build-your-own-x",
        "business": "marketingskills",
        "research": "context7",
        "command": "agency-agents",
        "memory": "prompts",
        "live": "personalive",
    }
    primary = defaults.get(suite) or (tools[0] if tools else "ollama")
    if suite == "video" and ("http://" in prompt or "https://" in prompt or "clip" in prompt.lower()):
        primary = "clip"
    if suite == "code" and any(w in prompt.lower() for w in ("openhands", "implement", "refactor")):
        primary = "openhands"
    if suite == "video" and "remotion" in prompt.lower():
        primary = "remotion"
    if suite == "video" and "voice" in prompt.lower():
        primary = "voicebox"
    if suite == "video" and "openmontage" in prompt.lower():
        primary = "openmontage"
    if suite == "design" or "design-md" in prompt.lower() or "design.md" in prompt.lower():
        if "awesome-design-md" in tools:
            primary = "awesome-design-md"
    return run_item(primary, [prompt])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="")
    parser.add_argument("--room", default="")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    prompt = " ".join(args.prompt).strip()
    suite = args.suite or suite_for_room(args.room.upper()) if args.room else ""
    if not suite:
        suite = "command"
    if not prompt:
        print("Usage: python tools/stack_agent.py --suite video|code|write|... <prompt>")
        return 2
    return operate(suite, prompt)


if __name__ == "__main__":
    raise SystemExit(main())
