"""First-class wrappers: ensure (lazy) then RUN. LLM = Ollama only. No Docker."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from integrations.catalog import ROOT, find, repo_path
from integrations.stack import ensure, which

OUT = ROOT / "outputs" / "stack"


def print_header(item: dict[str, Any]) -> None:
    print(f"[KYLA/{item.get('id')}] {item.get('name')}  credits={item.get('credit_impact')}")
    print(f"  {item.get('repo_url')}")


def _text(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def run_ollama(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    prompt = " ".join(args).strip() or "Reply with KYLA_STACK_OK"
    return subprocess.run([sys.executable, str(ROOT / "tools" / "ollama_agent.py"), prompt], check=False).returncode


def run_clip(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    cmd = [sys.executable, str(ROOT / "tools" / "clip_agent.py"), *(args or ["--help"])]
    return subprocess.run(cmd, check=False).returncode


def run_gitingest(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    target = " ".join(args).strip() or str(ROOT)
    exe = which("gitingest")
    if not exe:
        code = "from gitingest import ingest; s,t,c=ingest(%r); print(s); print(t[:2000])" % target
        return subprocess.run([sys.executable, "-c", code], check=False).returncode
    OUT.mkdir(parents=True, exist_ok=True)
    return subprocess.run([exe, target, "-o", str(OUT / "digest.txt")], check=False).returncode


def run_context7(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    query = " ".join(args).strip() or "next.js"
    url = f"https://context7.com/?q={query}"
    print(f"[RUN] {url}")
    print("[RUN] MCP https://mcp.context7.com/mcp")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "context7.txt").write_text(f"{query}\n{url}\n", encoding="utf-8")
    ctx7 = which("ctx7")
    if ctx7:
        return subprocess.run([ctx7, "library", query], check=False).returncode
    return 0


def run_agency_agents(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    dest = ensure(item)
    dest = dest if isinstance(dest, Path) else repo_path(item)
    query = " ".join(args).strip().lower()
    if not dest or not dest.is_dir():
        print("[ERROR] agency-agents clone failed (network?)")
        return 1
    matches = [p for p in dest.rglob("*.md") if ".git" not in p.parts and p.name.lower() != "license.md"]
    if query:
        matches = [p for p in matches if query in str(p).lower()] or matches
    print(f"[RUN] {len(matches)} persona(s) in {dest}")
    for path in matches[:25]:
        print(f"  - {path.relative_to(dest)}")
    if not matches:
        return 0
    pick = matches[0]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "agency-persona.md").write_text(_text(pick, 8000), encoding="utf-8")
    task = query or "Give a 5-bullet plan for Mel's next task."
    prompt = f"You are this agent persona:\n{_text(pick, 2500)}\n\nTask: {task}\nBe concise."
    return subprocess.run([sys.executable, str(ROOT / "tools" / "ollama_agent.py"), prompt], check=False).returncode


def run_prompts(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    print("[DOCS] https://prompts.chat  (titles only; no prompt bodies vendored)")
    dest = repo_path(item)
    query = " ".join(args).strip().lower()
    if dest.is_dir():
        names = [str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file() and ".git" not in p.parts]
        shown = [n for n in names if not query or query in n.lower()]
        for name in shown[:40]:
            print(f"  - {name}")
    return 0


def run_design_md(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    dest = ensure(item)
    dest = dest if isinstance(dest, Path) else repo_path(item)
    query = " ".join(args).strip().lower() or "linear"
    if not dest or not dest.is_dir():
        print("[ERROR] awesome-design-md clone failed")
        return 1
    hits = [p for p in dest.rglob("DESIGN.md") if ".git" not in p.parts]
    if query:
        hits = [p for p in hits if query in str(p).lower()] or hits
    print(f"[RUN] {len(hits)} DESIGN.md")
    design_out = ROOT / "outputs" / "design"
    design_out.mkdir(parents=True, exist_ok=True)
    for path in hits[:8]:
        print(f"  - {path.relative_to(dest)}")
    if hits:
        (design_out / "DESIGN.md").write_text(hits[0].read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        print(f"[OK] copied -> {design_out / 'DESIGN.md'}")
    return 0


def run_openmontage(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    print("[VIDEO] Catalina default = clip_agent (no Docker / no Node studio yet)")
    text = " ".join(args)
    if "http://" in text or "https://" in text:
        return run_clip({"id": "clip", "name": "clip", "credit_impact": "local/$0", "repo_url": ""}, args)
    print("  python tools/clip_agent.py --model tiny URL")
    return 0


def run_remotion(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    print("[RUN] Scaffold only (do not clone remotion monorepo): npx create-video@latest")
    return 0


def run_openhands(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    print("[RUN] No Docker on Catalina. Code path = Ollama + agency-agents + gitingest + context7.")
    prompt = " ".join(args).strip() or "Outline implementation steps locally."
    return subprocess.run([sys.executable, str(ROOT / "tools" / "ollama_agent.py"), prompt], check=False).returncode


def run_voicebox(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    ensure(item)
    text = " ".join(args).strip() or "KYLA stack ready"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "voice.txt").write_text(text, encoding="utf-8")
    for cmd in (["espeak-ng", "-w", str(OUT / "voice.wav"), text], ["say", text]):
        if which(cmd[0]):
            return subprocess.run(cmd, check=False).returncode
    print(f"[RUN] saved text -> {OUT / 'voice.txt'} (no espeak/say)")
    return 0


def run_docs_operate(item: dict[str, Any], args: list[str]) -> int:
    print_header(item)
    dest = ensure(item)
    dest = dest if isinstance(dest, Path) else repo_path(item)
    query = " ".join(args).strip().lower()
    if dest and dest.is_dir():
        hits = [str(p.relative_to(dest)) for p in dest.rglob("*.md") if ".git" not in p.parts]
        if query:
            hits = [h for h in hits if query in h.lower()] or hits
        for rel in hits[:30]:
            print(f"  - {rel}")
        if hits:
            pick = dest / hits[0]
            prompt = f"Using local doc ({hits[0]}):\n{_text(pick, 2000)}\n\nUser: {query or item.get('id')}\nShort actionable answer."
            return subprocess.run([sys.executable, str(ROOT / "tools" / "ollama_agent.py"), prompt], check=False).returncode
    print(f"[DOCS] {item.get('repo_url')}")
    return 0


WRAPPERS = {
    "ollama": run_ollama,
    "clip": run_clip,
    "gitingest": run_gitingest,
    "context7": run_context7,
    "agency_agents": run_agency_agents,
    "prompts": run_prompts,
    "design_md": run_design_md,
    "openmontage": run_openmontage,
    "remotion": run_remotion,
    "openhands": run_openhands,
    "voicebox": run_voicebox,
    "generic": run_docs_operate,
    "docs_url": run_docs_operate,
    "skills_clone": run_docs_operate,
}


def run_item(item_or_id: str | dict[str, Any], args: list[str] | None = None) -> int:
    item = item_or_id if isinstance(item_or_id, dict) else find(str(item_or_id))
    if not item:
        print(f"[ERROR] Unknown integration: {item_or_id}", file=sys.stderr)
        return 1
    fn = WRAPPERS.get(str(item.get("wrapper") or "generic"), run_docs_operate)
    return fn(item, args or [])
