#!/usr/bin/env python3
"""KYLA -> Supabase sink (server side only). Stdlib only, no pip installs.

Writes agent_runs / news_briefs through the Supabase REST API (PostgREST) using
SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (legacy service_role JWT *or* the new
sb_secret_... key; SUPABASE_SECRET_KEY is accepted as an alias).

Graceful by design: when the env vars are missing, or Supabase is down/paused,
every call is a quiet no-op that returns False. It never raises and never exits
non-zero, so cron jobs and the bridge keep working before the project exists.

CLI (used by GitHub Actions):
  python3 tools/supabase_sink.py status
  python3 tools/supabase_sink.py ping
  python3 tools/supabase_sink.py brief --date 2026-09-25 --file kyla/briefs/2026-09-25.md
  python3 tools/supabase_sink.py run --agent kyla-daily --status ok --input "daily brief" --output-file out.md

NEVER ship the service/secret key to web code. The browser uses the anon /
publishable key via web/supabase.js instead.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT = 20000
TIMEOUT = float(os.environ.get("SUPABASE_TIMEOUT", "8"))
_ENV_LOADED = False


def _load_dotenv() -> None:
    """Read SUPABASE_* from ROOT/.env (if present) without overriding the real environment."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    path = ROOT / ".env"
    if not path.is_file():
        return
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            val = val.strip().strip('"').strip("'")
            if key.startswith("SUPABASE_") and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


def _creds() -> tuple[str, str]:
    _load_dotenv()
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SECRET_KEY") or "").strip()
    return url, key


def configured() -> bool:
    url, key = _creds()
    return bool(key) and url.startswith(("https://", "http://"))


def _headers(key: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    h = {"apikey": key, "Content-Type": "application/json", "Accept": "application/json"}
    # Legacy service_role keys are JWTs and go in Authorization too.
    # New sb_secret_ keys are opaque and must ONLY be sent as apikey.
    if key.startswith("eyJ"):
        h["Authorization"] = f"Bearer {key}"
    if extra:
        h.update(extra)
    return h


def _request(method: str, path: str, body: Any = None, prefer: str | None = None) -> tuple[bool, Any]:
    url, key = _creds()
    if not (url and key):
        return False, "not configured"
    data = json.dumps(body, ensure_ascii=False, default=str).encode() if body is not None else None
    extra = {"Prefer": prefer} if prefer else None
    req = urllib.request.Request(f"{url}/rest/v1/{path}", data=data, method=method, headers=_headers(key, extra))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return True, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        return False, f"HTTP {exc.code}: {detail}"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _clip(text: Any) -> str | None:
    if text is None:
        return None
    s = str(text)
    return s if len(s) <= MAX_TEXT else s[:MAX_TEXT] + "\n…[truncated]"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def insert(table: str, rows: dict | list, on_conflict: str | None = None) -> bool:
    """Insert (or upsert when on_conflict is given). Returns True on success, False otherwise."""
    if not configured():
        return False
    path = table + (f"?on_conflict={on_conflict}" if on_conflict else "")
    prefer = "return=minimal" + (",resolution=merge-duplicates" if on_conflict else "")
    ok, info = _request("POST", path, rows, prefer=prefer)
    if not ok:
        print(f"[supabase] {table} write skipped: {info}", file=sys.stderr)
    return ok


def log_run(agent: str, status: str = "ok", input: str | None = None, output: str | None = None,
            room: str | None = None, source: str = "bridge", started_at: str | None = None,
            finished_at: str | None = None, meta: dict | None = None) -> bool:
    status = status if status in {"queued", "running", "ok", "error", "skipped"} else "error"
    return insert("agent_runs", {
        "agent": agent or "unknown", "room": room, "status": status,
        "input": _clip(input), "output": _clip(output), "source": source,
        "started_at": started_at or _now(), "finished_at": finished_at or _now(),
        "meta": meta or {}, "user_id": None,
    })


def log_run_async(**kwargs: Any) -> None:
    """Fire-and-forget log_run so the bridge reply is never delayed."""
    if configured():
        threading.Thread(target=log_run, kwargs=kwargs, daemon=True).start()


def log_brief(brief_date: str, body_md: str, title: str | None = None, kind: str = "daily",
              source: str = "actions") -> bool:
    return insert("news_briefs", {
        "brief_date": brief_date, "kind": kind, "title": title,
        "body_md": _clip(body_md) or "", "source": source, "user_id": None,
    }, on_conflict="brief_date,kind")


def ping() -> bool:
    """Cheap REST select (keeps free projects from pausing)."""
    if not configured():
        return False
    ok, info = _request("GET", "news_briefs?select=id&limit=1")
    if not ok:
        print(f"[supabase] ping failed: {info}", file=sys.stderr)
    return ok


def status() -> dict[str, Any]:
    url, key = _creds()
    kind = "missing"
    if key.startswith("sb_secret_"):
        kind = "secret (sb_secret_)"
    elif key.startswith("eyJ"):
        kind = "legacy service_role JWT"
    elif key:
        kind = "unknown format"
    return {"configured": configured(), "url": url or None, "key": kind}


def _read(path: str | None) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="KYLA Supabase sink (no-op without SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("ping")
    b = sub.add_parser("brief")
    b.add_argument("--date", default=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d"))
    b.add_argument("--file", required=True)
    b.add_argument("--kind", default="daily")
    b.add_argument("--title", default=None)
    b.add_argument("--source", default="actions")
    r = sub.add_parser("run")
    r.add_argument("--agent", required=True)
    r.add_argument("--status", default="ok")
    r.add_argument("--room", default=None)
    r.add_argument("--input", default=None)
    r.add_argument("--output", default=None)
    r.add_argument("--output-file", default=None)
    r.add_argument("--source", default="actions")
    r.add_argument("--started-at", default=None)
    args = p.parse_args(argv)

    if args.cmd == "status":
        print(json.dumps(status()))
        return 0
    if not configured():
        print("[supabase] not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing) — skipping, no-op.")
        return 0
    if args.cmd == "ping":
        print("[supabase] ping ok" if ping() else "[supabase] ping failed (non-fatal)")
    elif args.cmd == "brief":
        body = _read(args.file)
        if not body.strip():
            print(f"[supabase] brief file empty/missing: {args.file} — skipping")
            return 0
        title = args.title or next((ln.lstrip("# ").strip() for ln in body.splitlines() if ln.strip()), None)
        ok = log_brief(args.date, body, title=title, kind=args.kind, source=args.source)
        print("[supabase] brief saved" if ok else "[supabase] brief not saved (non-fatal)")
    elif args.cmd == "run":
        output = args.output if args.output is not None else _read(args.output_file)
        ok = log_run(args.agent, status=args.status, input=args.input, output=output, room=args.room,
                     source=args.source, started_at=args.started_at)
        print("[supabase] run logged" if ok else "[supabase] run not logged (non-fatal)")
    return 0  # always soft


if __name__ == "__main__":
    raise SystemExit(main())
