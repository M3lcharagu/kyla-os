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
        aliases = [str(item.get("name", "")).lower()]
        aliases.extend(a.lower() for a in item.get("aliases") or [])
        if needle in aliases:
            return item
    return None


def match_prompt(text: str, path: str | None = None) -> dict[str, Any] | None:
    normalized = (text or "").lower()
    best: tuple[int, dict[str, Any]] | None = None
    for item in items(path):
        aliases = [str(item.get("id", "")), str(item.get("name", ""))]
        aliases.extend(str(a) for a in item.get("aliases") or [])
        for alias in aliases:
            alias = alias.strip()
            if not alias:
                continue
            if re.search(rf"(?i)(?<!\w){re.escape(alias)}(?!\w)", normalized):
                score = len(alias)
                if best is None or score > best[0]:
                    best = (score, item)
    return best[1] if best else None


def suite_for_room(room_id: str) -> str | None:
    mapping = (load_stack().get("room_defaults") or {})
    return mapping.get(room_id)


def tools_for_suite(suite: str) -> list[str]:
    suites = load_stack().get("suites") or {}
    row = suites.get(suite) or {}
    return list(row.get("tools") or [])


def format_hint(item: dict[str, Any]) -> str:
    rooms = ",".join(item.get("rooms") or [])
    return (
        f"[STACK] {item.get('id')} · {item.get('name')} "
        f"({item.get('status')}, {item.get('credit_impact')}, {rooms})\n"
        f"  {item.get('repo_url')}\n"
        f"  python tools/integrations_cli.py run {item.get('id')}"
    )
