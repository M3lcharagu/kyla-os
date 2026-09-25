#!/usr/bin/env python3
"""KYLA stack CLI — list / show / run / dispatch / bootstrap."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.catalog import find, format_hint, items, match_prompt, stack_dir  # noqa: E402
from integrations.runtime import run_item  # noqa: E402
from integrations.stack import ensure, repo_path  # noqa: E402


def _present(item) -> str:
    if item.get("id") == "supabase":
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            import supabase_sink
            return "yes" if supabase_sink.configured() else "no"
        except Exception:  # noqa: BLE001
            return "no"
    dest = repo_path(item)
    if dest.is_dir() and any(dest.iterdir()):
        return "yes"
    if item.get("id") in {"clip", "ollama"}:
        return "yes"
    return "no"


def cmd_list(_args: argparse.Namespace) -> int:
    rows = items()
    print(f"KYLA stack ({len(rows)})  dir={stack_dir()}\n")
    print(f"{'ID':<22} {'STATUS':<8} {'ON':<4} {'ROOMS':<16} {'CREDITS':<22} REPO")
    print("-" * 110)
    for item in rows:
        print(
            f"{item.get('id',''):<22} {item.get('status',''):<8} {_present(item):<4} "
            f"{','.join(item.get('rooms') or []):<16} {item.get('credit_impact',''):<22} "
            f"{item.get('repo_url','')}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    item = find(args.name)
    if not item:
        print(f"[ERROR] unknown: {args.name}", file=sys.stderr)
        return 1
    print(format_hint(item))
    print(f"  path: {repo_path(item)}")
    print(f"  install: {item.get('install_hint')}")
    print(f"  run: {item.get('run_hint')}")
    print(f"  note: {item.get('note')}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    return run_item(args.name, args.rest)


def cmd_dispatch(args: argparse.Namespace) -> int:
    prompt = " ".join([args.name, *args.rest]).strip()
    item = match_prompt(prompt) or find(args.name)
    if not item:
        print(f"[ERROR] no match: {prompt!r}", file=sys.stderr)
        return 1
    extra = prompt
    for alias in [item.get("id"), *(item.get("aliases") or [])]:
        extra = extra.replace(str(alias), " ")
    return run_item(item, [t for t in extra.split() if t])


def cmd_ensure(args: argparse.Namespace) -> int:
    item = find(args.name)
    if not item:
        print(f"[ERROR] unknown: {args.name}", file=sys.stderr)
        return 1
    dest = ensure(item)
    print(f"[OK] {item['id']} -> {dest}")
    return 0 if dest else 1


def main() -> int:
    p = argparse.ArgumentParser(description="KYLA first-class integrations")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(func=cmd_list)
    s = sub.add_parser("show"); s.add_argument("name"); s.set_defaults(func=cmd_show)
    r = sub.add_parser("run"); r.add_argument("name"); r.add_argument("rest", nargs="*"); r.set_defaults(func=cmd_run)
    d = sub.add_parser("dispatch"); d.add_argument("name", nargs="?", default=""); d.add_argument("rest", nargs="*"); d.set_defaults(func=cmd_dispatch)
    e = sub.add_parser("ensure"); e.add_argument("name"); e.set_defaults(func=cmd_ensure)
    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
