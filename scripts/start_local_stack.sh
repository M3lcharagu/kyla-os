#!/usr/bin/env bash
# Start the free local stack: Ollama (if needed) + optional UI http.server
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODEL="${KYLA_OLLAMA_MODEL:-qwen2.5:3b}"
PORT="${KYLA_UI_PORT:-8080}"
UI_DIR="${KYLA_UI_DIR:-web}"

echo "==> Local stack (zero cloud credits)"

if command -v ollama >/dev/null; then
  if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Starting ollama serve in background..."
    nohup ollama serve >/tmp/kyla-ollama.log 2>&1 &
    sleep 2
  fi
  echo "Ensuring model $MODEL is present..."
  ollama pull "$MODEL" || true
else
  echo "WARN: ollama not installed — chat agent will fail until you install it."
fi

# Optional LiteLLM cache proxy (only if litellm is installed)
if python3 -c "import litellm" 2>/dev/null || { [[ -f .venv/bin/python ]] && .venv/bin/python -c "import litellm" 2>/dev/null; }; then
  echo "Optional: litellm --config litellm_config.yaml --port 4000"
fi

echo "Static UI: python -m http.server $PORT --directory $UI_DIR"
echo "  Open http://127.0.0.1:$PORT/"
echo "Optional Caddy one-liner (if installed):"
echo "  caddy file-server --listen :8080 --root $UI_DIR"
echo ""
echo "KYLA CLI tips:"
echo "  source .venv/bin/activate"
echo "  python main.py --agent ollama --execute \"short question\""
echo "  python tools/clip_agent.py --dry-run \"https://youtube.com/watch?v=...\""

if [[ "${KYLA_START_UI:-1}" == "1" ]]; then
  echo "Serving $UI_DIR on :$PORT (Ctrl+C to stop)"
  exec python3 -m http.server "$PORT" --directory "$UI_DIR"
fi
