#!/usr/bin/env bash
# Ensure one first-class stack tool (auto-clone / pip).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ID="${1:-}"
if [[ -z "$ID" ]]; then
  echo "Usage: bash scripts/install_integration.sh <id>"
  python3 tools/integrations_cli.py list
  exit 1
fi
export KYLA_STACK_DIR="${KYLA_STACK_DIR:-${HOME}/kyla-stack}"
if [[ -d /workspace/kyla-stack ]]; then
  export KYLA_STACK_DIR="${KYLA_STACK_DIR:-/workspace/kyla-stack}"
fi
python3 tools/integrations_cli.py ensure "$ID"
