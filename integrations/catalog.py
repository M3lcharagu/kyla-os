"""Load REGISTRY.yaml + STACK.yaml and match prompts to first-class tools."""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path(__file__).resolve().parent / "REGISTRY.yaml"
STACK_PATH = Path(__file__).resolve().parent / "STACK.yaml"


@lru_cache(maxsize=1)
def load_registry(path: str | None = None) -> dict[str, Any]:
    target = Path(path) if path else REGISTRY_PATH
    with target.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    items = data.get("integrations") or []
    if not isinstance(items, list):
        raise ValueError("REGISTRY.yaml integrations must be a list")
    # Optional extras (TikTok stack etc.) merged by id without replacing primary
    extra_path = target.with_name("REGISTRY_EXTRA.yaml")
    if extra_path.is_file() and path is None:
        with extra_path.open("r", encoding="utf-8") as fh:
            extra = yaml.safe_load(fh) or {}
        seen = {i.get("id") for i in items if isinstance(i, dict)}
        for item in extra.get("integrations") or []:
            if isinstance(item, dict) and item.get("id") not in seen:
                items.append(item)
                seen.add(item.get("id"))
    data["integrations"] = items
    return data


@lru_cache(maxsize=1)
def load_stack() -> dict[str, Any]:
    if not STACK_PATH.is_file():
        return {}
    with STACK_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def items(path: str | None = None) -> list[dict[str, Any]]:
    return list(load_registry(path).get("integrations") or [])


def stack_dir() -> Path:
    env = os.environ.get("KYLA_STACK_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    for candidate in (
        Path("/workspace/kyla-stack"),
        Path.home() / "kyla-stack",
        ROOT / "kyla-stack",
    ):
        if candidate.is_dir():
            return candidate.resolve()
    default = load_stack().get("stack_dir_default") or "~/kyla-stack"
    return Path(default).expanduser().resolve()


def vendor_dir() -> Path:
    return stack_dir()


def repo_path(item_or_id: str | dict[str, Any]) -> Path:
    ident = item_or_id.get("id") if isinstance(item_or_id, dict) else item_or_id
    return stack_dir() / str(ident)


def find(id_or_alias: str, path: str | None = None) -> dict[str, Any] | None:
    needle = (id_or_alias or "").strip().lower()
    if not needle:
        return None
    for item in items(path):
        if str(item.get("id", "")).lower() == needle:
            return item
        aliases = [str(a).lower() for a in (item.get("aliases") or [])]
        if needle in aliases:
            return item
    return None


def match_prompt(prompt: str, path: str | None = None) -> dict[str, Any] | None:
    text = (prompt or "").strip().lower()
    if not text:
        return None
    # Prefer longer alias / id matches
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items(path):
        keys = [str(item.get("id", ""))] + [str(a) for a in (item.get("aliases") or [])]
        for key in keys:
            k = key.lower().strip()
            if k and k in text:
                ranked.append((len(k), item))
    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1]


def suite_for_room(room_id: str) -> str:
    """Room -> suite from STACK.yaml room_defaults (used by tools/stack_agent.py)."""
    return str((load_stack().get("room_defaults") or {}).get((room_id or "").strip().upper(), "") or "")


def tools_for_suite(suite: str) -> list[str]:
    """Suite -> tool ids from STACK.yaml suites (used by tools/stack_agent.py)."""
    entry = (load_stack().get("suites") or {}).get((suite or "").strip()) or {}
    return [str(t) for t in (entry.get("tools") or [])]


def format_hint(item: dict[str, Any]) -> str:
    rooms = ",".join(item.get("rooms") or [])
    return (
        f"[STACK] {item.get('id')} · {item.get('name')} "
        f"({item.get('status')}, {item.get('credit_impact')}, {rooms})\n"
        f"  {item.get('repo_url')}\n"
        f"  python tools/integrations_cli.py run {item.get('id')}"
    )
