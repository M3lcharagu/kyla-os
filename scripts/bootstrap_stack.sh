#!/usr/bin/env bash
# Lazy stack for 8GB / 2012 MacBook Pro Catalina.
# Default: light markdown + pip CLIs only. NO Docker. NO GPU models.
# Heavy clones only if KYLA_CLONE_HEAVY=1 (do not set this on Catalina).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${KYLA_STACK_DIR:-}" ]]; then
  if [[ -d /workspace ]]; then
    export KYLA_STACK_DIR=/workspace/kyla-stack
  else
    export KYLA_STACK_DIR="$HOME/kyla-stack"
  fi
fi
mkdir -p "$KYLA_STACK_DIR"
echo "==> KYLA lazy stack -> $KYLA_STACK_DIR"
echo "    Catalina/8GB: no Docker, no heavy clones (KYLA_CLONE_HEAVY=${KYLA_CLONE_HEAVY:-0})"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

export KYLA_CLONE_HEAVY="${KYLA_CLONE_HEAVY:-0}"
"$PYTHON" - <<'PY'
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from integrations.catalog import items
from integrations.stack import ensure, ensure_stack_dir

ensure_stack_dir()
core = [
    "gitingest", "agency-agents", "awesome-design-md", "prompts",
    "marketingskills", "build-your-own-x", "freedomain", "context7",
    "clip", "ollama", "public-apis", "agent-reach",
    "awesome-harness-engineering", "anthropic-cybersecurity-skills",
]
heavy = {
    "openhands", "openmontage", "voicebox", "personalive",
    "mumuainovel", "cli-anything", "graft", "codebase-memory", "remotion",
    "awesome-llm-apps", "openviking",
}
lookup = {i["id"]: i for i in items()}
for tid in core:
    item = lookup.get(tid)
    if not item:
        continue
    print(f"\n==> ensure {tid}")
    try:
        print(f"    {ensure(item)}")
    except Exception as exc:
        print(f"    WARN {tid}: {exc}")

if os.environ.get("KYLA_CLONE_HEAVY") == "1":
    for tid in heavy:
        item = lookup.get(tid)
        if not item:
            continue
        print(f"\n==> HEAVY ensure {tid}")
        try:
            print(f"    {ensure(item)}")
        except Exception as exc:
            print(f"    WARN {tid}: {exc}")
else:
    print("\n[LAZY] skipped heavy:", ", ".join(sorted(heavy)))
    print("  Daily video = clip_agent. Daily chat = Ollama. No Docker.")
print("\nStack dir:", os.environ.get("KYLA_STACK_DIR"))
PY


# --- ALWAYS-ON Ruflo (not optional) ---
echo ""
echo "==> Ruflo always-on orchestrator (npx ruflo@latest)"
if command -v npx >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1 || echo 0)"
  if [[ "${NODE_MAJOR}" -lt 20 ]]; then
    echo "    WARN: Node ${NODE_MAJOR} < 20. Ruflo prefers Node 20+."
    echo "    Catalina: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
    echo "             nvm install 20 && nvm use 20"
  fi
  mkdir -p "$KYLA_STACK_DIR/ruflo"
  (
    cd "$KYLA_STACK_DIR/ruflo"
    # Non-interactive init when possible; wizard documented in docs/RUFLO.md
    CI=1 npm_config_yes=true npx --yes ruflo@latest --version || true
    if [[ ! -f .kyla_ruflo_inited ]]; then
      echo "    init (non-interactive)…"
      CI=1 npm_config_yes=true npx --yes ruflo@latest init || {
        echo "    init returned non-zero — try wizard on Mac: npx ruflo@latest init wizard"
      }
      echo "ok" > .kyla_ruflo_inited
    else
      echo "    already inited (.kyla_ruflo_inited)"
    fi
  )
  echo "    OK — KYLA default_agent=ruflo (see config.yaml / docs/RUFLO.md)"
else
  echo "    WARN: node/npx missing — Ruflo cannot run until Node 20+ is installed."
  echo "    KYLA will fall through to stack_agent/ollama. Config still says ruflo is intended."
fi

# --- Agent-Reach (ALWAYS available research web, lazy pip) ---
echo ""
echo "==> Agent-Reach (research/web always-available)"
if [[ -x "$ROOT/.venv/bin/pip" ]]; then
  "$ROOT/.venv/bin/pip" install -q agent-reach || echo "    WARN: pip agent-reach failed"
  AR=""
  if command -v agent-reach >/dev/null 2>&1; then AR="$(command -v agent-reach)"; fi
  [[ -z "$AR" && -x "$ROOT/.venv/bin/agent-reach" ]] && AR="$ROOT/.venv/bin/agent-reach"
  if [[ -n "$AR" ]]; then
    mkdir -p "$KYLA_STACK_DIR/agent-reach"
    if [[ ! -f "$KYLA_STACK_DIR/agent-reach/.kyla_inited" ]]; then
      echo "    agent-reach install --env=auto --safe"
      "$AR" install --env=auto --safe || echo "    WARN: agent-reach install non-zero (ok to retry later)"
      echo ok > "$KYLA_STACK_DIR/agent-reach/.kyla_inited"
    else
      echo "    already inited"
    fi
  fi
else
  echo "    WARN: no venv pip — run setup_local.sh first"
fi

# --- Anthropic Cybersecurity Skills (npx, alongside Ruflo) ---
echo ""
echo "==> Anthropic Cybersecurity Skills (R13)"
if command -v npx >/dev/null 2>&1; then
  mkdir -p "$KYLA_STACK_DIR/anthropic-cybersecurity-skills"
  if [[ ! -f "$KYLA_STACK_DIR/anthropic-cybersecurity-skills/.kyla_skills_added" ]]; then
    (cd "$KYLA_STACK_DIR/anthropic-cybersecurity-skills" && npx --yes skills add mukul975/Anthropic-Cybersecurity-Skills) \
      || echo "    WARN: skills add failed — retry: npx skills add mukul975/Anthropic-Cybersecurity-Skills"
    echo ok > "$KYLA_STACK_DIR/anthropic-cybersecurity-skills/.kyla_skills_added"
  else
    echo "    already added"
  fi
else
  echo "    WARN: npx missing — cyber skills deferred (Node 20+ via nvm on Catalina)"
fi

echo ""
echo "Done (lazy). Next:"
echo "  export KYLA_STACK_DIR=$KYLA_STACK_DIR"
echo "  python tools/integrations_cli.py list"
echo "  python main.py --dry-run \"clip a youtube short in gula\""
