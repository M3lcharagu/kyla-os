"""Ensure first-class stack tools exist (lazy clone / pip). No paid APIs."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from integrations.catalog import items, repo_path, stack_dir


def which(name: str) -> str | None:
    return shutil.which(name)


def ensure_stack_dir() -> Path:
    dest = stack_dir()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / ".kyla-stack").write_text("kyla-stack\n", encoding="utf-8")
    return dest


def ensure_repo(item: dict[str, Any], timeout: int = 180) -> Path | None:
    """Shallow-clone the repo into the stack dir if missing. Returns path or None."""
    dest = repo_path(item)
    if dest.is_dir() and any(p.name != ".git" for p in dest.iterdir()):
        return dest
    url = item.get("repo_url")
    if not url:
        return None
    heavy = bool(item.get("heavy"))
    if heavy and os.environ.get("KYLA_CLONE_HEAVY", "0") != "1":
        print(f"[STACK] skip heavy clone {item.get('id')} (set KYLA_CLONE_HEAVY=1)")
        return None
    ensure_stack_dir()
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    print(f"[STACK] clone --depth 1 {url} -> {dest}")
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout)
        return None
    return dest


def ensure_pip(pkg: str) -> bool:
    if not pkg:
        return False
    print(f"[STACK] pip install {pkg}")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", pkg],
        check=False,
    )
    return proc.returncode == 0


def ensure_bin(item: dict[str, Any]) -> str | None:
    for name in item.get("detect_bins") or []:
        found = which(name)
        if found:
            return found
    ident = item.get("id")
    if ident == "gitingest":
        if ensure_pip("gitingest"):
            return which("gitingest") or "gitingest"
    return None


def ensure(item: dict[str, Any]) -> Path | str | None:
    """Bootstrap whatever this tool needs so KYLA can operate."""
    ident = item.get("id")
    if ident == "clip":
        return Path(__file__).resolve().parents[1] / "tools" / "clip_agent.py"
    if ident == "ollama":
        return which("ollama") or "ollama"
    if ident == "agent-reach":
        dest = repo_path(item)
        dest.mkdir(parents=True, exist_ok=True)
        ensure_pip("agent-reach")
        exe = which("agent-reach")
        if exe and not (dest / ".kyla_inited").is_file():
            subprocess.run([exe, "install", "--env=auto", "--safe"], check=False)
            (dest / ".kyla_inited").write_text("ok\n", encoding="utf-8")
        (dest / "KYLA_POINTER.md").write_text(
            "# Agent-Reach\n\nhttps://github.com/Panniantong/Agent-Reach\n\n"
            "pip install agent-reach && agent-reach install --env=auto --safe\n"
            "python tools/agent_reach_cli.py <query>\n",
            encoding="utf-8",
        )
        return exe or dest
    if ident == "anthropic-cybersecurity-skills":
        dest = repo_path(item)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "KYLA_POINTER.md").write_text(
            "# Anthropic Cybersecurity Skills\n\n"
            "https://github.com/mukul975/Anthropic-Cybersecurity-Skills\n\n"
            "npx skills add mukul975/Anthropic-Cybersecurity-Skills\n",
            encoding="utf-8",
        )
        if which("npx"):
            marker = dest / ".kyla_skills_added"
            if not marker.is_file():
                subprocess.run(
                    ["npx", "--yes", "skills", "add", "mukul975/Anthropic-Cybersecurity-Skills"],
                    check=False,
                    cwd=str(dest),
                )
                marker.write_text("ok\n", encoding="utf-8")
        return dest
    if ident == "ruflo":
        dest = repo_path(item)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "KYLA_POINTER.md").write_text(
            "# Ruflo\n\nhttps://github.com/ruvnet/ruflo\n\n"
            "Always-on KYLA orchestrator. Run: npx ruflo@latest init\n"
            "Or: python tools/ruflo_agent.py <prompt>\n",
            encoding="utf-8",
        )
        return dest
    kind = item.get("install_kind") or "clone"
    if ident == "gitingest" or kind == "pip":
        ensure_bin(item)
    if kind in {"clone", "docs"} and item.get("repo_url"):
        return ensure_repo(item)
    if kind in {"npx", "scaffold", "docker"}:
        dest = repo_path(item)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "KYLA_POINTER.md").write_text(
            f"# {item.get('name')}\n\n{item.get('repo_url')}\n\n{item.get('run_hint')}\n",
            encoding="utf-8",
        )
        return dest
    return repo_path(item) if repo_path(item).is_dir() else None


def ensure_suite(tool_ids: list[str]) -> list[str]:
    ready = []
    lookup = {i.get("id"): i for i in items()}
    for tid in tool_ids:
        item = lookup.get(tid)
        if not item:
            continue
        try:
            ensure(item)
            ready.append(tid)
        except Exception as exc:  # noqa: BLE001
            print(f"[STACK] ensure {tid} failed: {exc}")
    return ready
