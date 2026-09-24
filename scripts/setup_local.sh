#!/usr/bin/env bash
# KYLA local low-credit setup (Linux / macOS / Linux Mint)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> KYLA local setup (no cloud API keys required)"

# Python venv
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> Checking system tools"
need_apt=()
command -v ffmpeg >/dev/null || need_apt+=(ffmpeg)
command -v ffprobe >/dev/null || need_apt+=(ffmpeg)
if [[ ${#need_apt[@]} -gt 0 ]]; then
  echo "    Missing: ${need_apt[*]}"
  if command -v apt-get >/dev/null && [[ "${KYLA_AUTO_APT:-0}" == "1" ]]; then
    sudo apt-get update && sudo apt-get install -y ffmpeg
  else
    echo "    Install ffmpeg (Debian/Mint: sudo apt install ffmpeg)"
  fi
else
  echo "    ffmpeg OK"
fi

# yt-dlp (pip copy is fine for local)
pip install -q "yt-dlp>=2024.1" || true
command -v yt-dlp >/dev/null && echo "    yt-dlp OK" || echo "    yt-dlp via: python -m yt_dlp"

# Optional clip stack (heavy — opt-in)
if [[ "${KYLA_INSTALL_CLIP:-1}" == "1" ]]; then
  echo "==> Installing optional clip deps (requirements-clip.txt)"
  pip install -r requirements-clip.txt || {
    echo "    WARN: clip deps failed — base KYLA still works. Retry later."
  }
  # auto-editor: silence trim helper (optional)
  pip install -q auto-editor || echo "    WARN: auto-editor optional install failed"
fi

# Ollama
echo "==> Ollama (local LLM — zero credits)"
MODEL="${KYLA_OLLAMA_MODEL:-qwen2.5:3b}"
if command -v ollama >/dev/null; then
  echo "    ollama binary found"
  if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "    ollama server up — pulling ${MODEL} (small, 8GB-friendly)"
    ollama pull "$MODEL" || echo "    WARN: pull failed; start with: ollama serve && ollama pull $MODEL"
  else
    echo "    Start server in another terminal: ollama serve"
    echo "    Then: ollama pull $MODEL"
  fi
else
  echo "    Install from https://ollama.com/download (Linux/mac/Windows)"
  echo "    Or: curl -fsSL https://ollama.com/install.sh | sh"
  echo "    Then: ollama pull $MODEL"
  echo "    Alt 8GB model: ollama pull phi4-mini"
fi

# Sibling kyla-clip (editable if present)
CLIP_DIR="$(dirname "$ROOT")/kyla-clip"
if [[ -d "$CLIP_DIR/src/kyla_clip" ]]; then
  echo "==> Linking sibling kyla-clip (editable)"
  pip install -e "$CLIP_DIR" || echo "    WARN: editable install skipped"
fi


# Ruflo (ALWAYS-ON orchestrator — Node 20+)
echo "==> Ruflo / Node (always-on agent harness)"
if command -v node >/dev/null && command -v npx >/dev/null; then
  echo "    node $(node -v) / npx OK"
  NODE_MAJOR="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1 || echo 0)"
  if [[ "${NODE_MAJOR}" -lt 20 ]]; then
    echo "    WARN: Node ${NODE_MAJOR} < 20 — Ruflo prefers 20+."
    echo "    macOS Catalina: install nvm then: nvm install 20 && nvm use 20"
  fi
  echo "    Init via: bash scripts/bootstrap_stack.sh  (runs npx ruflo@latest init)"
else
  echo "    Node/npx missing. Install Node 20+ then re-run bootstrap."
  echo "    Catalina nvm:"
  echo "      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
  echo "      nvm install 20 && nvm use 20"
fi

mkdir -p outputs/clips
echo ""
echo "Done. Next:"
echo "  source .venv/bin/activate"
echo "  make ollama-up   # or: ollama serve && ollama pull $MODEL"
echo "  python main.py --dry-run \"hello\""
echo "  python main.py --agent ruflo --dry-run \"plan my week\"   # ALWAYS-ON default"
echo "  python main.py --agent ollama --execute \"summarize my day in 3 bullets\""
echo "  python tools/clip_agent.py --help"
echo "See docs/RUFLO.md, docs/LOCAL_LOW_CREDIT.md, and /workspace/KYLA_LOCAL_HANDOFF.md"
