#!/usr/bin/env python3
"""Local Ollama agent — zero cloud credits.

KYLA appends the user prompt as the final argv entry.
Talks to the Ollama HTTP API (default http://127.0.0.1:11434).

Env:
  OLLAMA_HOST   base URL (default http://127.0.0.1:11434)
  OLLAMA_MODEL  model tag (default qwen2.5:3b — fits 8GB RAM)
  OLLAMA_TIMEOUT seconds (default 120)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
SYSTEM = (
    "You are KYLA, Mel's local personal AI assistant. "
    "Be concise, practical, and helpful. Prefer short answers to save tokens."
)


def chat(prompt: str) -> str:
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)
    timeout = float(os.environ.get("OLLAMA_TIMEOUT", "120"))

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "options": {
            # Cap generation to keep latency/tokens low on 8GB machines.
            "num_predict": int(os.environ.get("OLLAMA_NUM_PREDICT", "512")),
            "temperature": float(os.environ.get("OLLAMA_TEMPERATURE", "0.4")),
        },
    }

    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return (
            "[ERROR] Ollama is not reachable.\n"
            f"  Tried: {host}/api/chat\n"
            f"  Detail: {exc}\n"
            "  Fix: install Ollama, run `ollama serve`, then "
            f"`ollama pull {model}`.\n"
            "  See docs/LOCAL_LOW_CREDIT.md"
        )
    except TimeoutError:
        return f"[ERROR] Ollama timed out after {timeout}s (model={model})."

    message = body.get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        return f"[ERROR] Empty Ollama response: {json.dumps(body)[:400]}"
    return content


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        print("Usage: python tools/ollama_agent.py \"your question\"", file=sys.stderr)
        return 2
    if prompt in {"--help", "-h"}:
        print(__doc__)
        return 0
    print(chat(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
