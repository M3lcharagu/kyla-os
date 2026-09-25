"""Extra KYLA wrappers: ruflo, agent-reach, cyber_skills, supabase."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from integrations.catalog import ROOT
from integrations.stack import ensure, which


def run_agent_reach(item: dict[str, Any], args: list[str], print_header) -> int:
    print_header(item)
    ensure(item)
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "agent_reach_cli.py"), *(args or [])],
        check=False,
    ).returncode


def run_cyber_skills(item: dict[str, Any], args: list[str], print_header) -> int:
    print_header(item)
    dest = ensure(item)
    print("[SKILLS] npx skills add mukul975/Anthropic-Cybersecurity-Skills")
    print(f"  pointer: {dest}")
    if which("npx"):
        return subprocess.run(
            ["npx", "--yes", "skills", "add", "mukul975/Anthropic-Cybersecurity-Skills"],
            check=False,
        ).returncode
    print("[WARN] npx missing — install Node 20+ (nvm on Catalina)")
    return 0


def run_ruflo(item: dict[str, Any], args: list[str], print_header) -> int:
    print_header(item)
    ensure(item)
    prompt_args = args or ["KYLA_RUFLO_OK"]
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "ruflo_agent.py"), *prompt_args],
        check=False,
    ).returncode


def run_supabase(item: dict[str, Any], args: list[str], print_header) -> int:
    """Status / ping for the default Supabase backend. Always exits 0 (soft)."""
    print_header(item)
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import supabase_sink as sb
    except Exception as exc:  # noqa: BLE001
        print(f"[supabase] helper unavailable: {exc}")
        return 0
    info = sb.status()
    print(f"[supabase] configured={info['configured']} url={info['url']} key={info['key']}")
    if not info["configured"]:
        print("[supabase] not configured — KYLA runs in local mode. Setup: supabase/README.md")
        return 0
    print("[supabase] ping ok" if sb.ping() else "[supabase] ping failed (paused project? see supabase/README.md)")
    return 0


def install(wrappers: dict, print_header) -> None:
    wrappers["ruflo"] = lambda item, args: run_ruflo(item, args, print_header)
    wrappers["agent_reach"] = lambda item, args: run_agent_reach(item, args, print_header)
    wrappers["cyber_skills"] = lambda item, args: run_cyber_skills(item, args, print_header)
    wrappers["supabase"] = lambda item, args: run_supabase(item, args, print_header)
