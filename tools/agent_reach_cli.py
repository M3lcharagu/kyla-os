#!/usr/bin/env python3
"""KYLA Agent-Reach wrapper — ALWAYS available for research/web (lazy pip).

Upstream: https://github.com/Panniantong/Agent-Reach
  pip install agent-reach
  agent-reach install --env=auto --safe   # Catalina / 8GB safe

No paid APIs. Falls back to a clear install hint if pip/CLI missing.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _which(name: str) -> str | None:
    return shutil.which(name)


def ensure_agent_reach(safe: bool = True) -> str | None:
    """Ensure agent-reach CLI; lazy pip + optional install --env=auto --safe."""
    exe = _which("agent-reach")
    if exe:
        return exe
    print("[KYLA/agent-reach] pip install agent-reach (lazy)…")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "agent-reach"],
        check=False,
    )
    if proc.returncode != 0:
        print("[ERROR] pip install agent-reach failed", file=sys.stderr)
        return None
    exe = _which("agent-reach")
    if not exe:
        candidate = Path(sys.executable).parent / "agent-reach"
        if candidate.is_file():
            exe = str(candidate)
    if not exe:
        print("[ERROR] agent-reach not on PATH after pip install", file=sys.stderr)
        return None
    marker = Path(os.environ.get("KYLA_STACK_DIR", str(Path.home() / "kyla-stack"))) / "agent-reach" / ".kyla_inited"
    marker.parent.mkdir(parents=True, exist_ok=True)
    if not marker.is_file():
        cmd = [exe, "install", "--env=auto"]
        if safe:
            cmd.append("--safe")
        print(f"[KYLA/agent-reach] {' '.join(cmd)}")
        subprocess.run(cmd, check=False)
        marker.write_text("ok\n", encoding="utf-8")
    return exe


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="KYLA Agent-Reach (always-on research web)")
    p.add_argument("prompt", nargs="*", help="Query / URL / topic")
    p.add_argument("--ensure-only", action="store_true", help="Only bootstrap, do not run")
    p.add_argument("--no-safe", action="store_true", help="Skip --safe on install (not for 8GB Mac)")
    args = p.parse_args(argv)

    exe = ensure_agent_reach(safe=not args.no_safe)
    if not exe:
        print(
            "Install manually:\n"
            "  pip install agent-reach\n"
            "  agent-reach install --env=auto --safe\n"
            "Docs: https://github.com/Panniantong/Agent-Reach",
            file=sys.stderr,
        )
        return 1
    if args.ensure_only:
        print(f"[OK] agent-reach -> {exe}")
        return 0

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        return subprocess.run([exe, "--help"], check=False).returncode

    for trial in (
        [exe, "search", prompt],
        [exe, "run", prompt],
        [exe, prompt],
    ):
        print(f"[KYLA/agent-reach] {' '.join(trial)}")
        proc = subprocess.run(trial, check=False)
        if proc.returncode == 0:
            return 0
        if proc.returncode in (2, 127):
            continue
        return proc.returncode
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
