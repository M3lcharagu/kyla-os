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
    "clip", "ollama",
]
heavy = {
    "openhands", "openmontage", "voicebox", "personalive",
    "mumuainovel", "cli-anything", "graft", "codebase-memory", "remotion",
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

echo ""
echo "Done (lazy). Next:"
echo "  export KYLA_STACK_DIR=$KYLA_STACK_DIR"
echo "  python tools/integrations_cli.py list"
echo "  python main.py --dry-run \"clip a youtube short in gula\""
