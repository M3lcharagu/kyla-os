# KYLA local helpers (Linux/mac/Mint; on Windows use the .ps1 scripts)
ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
MODEL ?= qwen2.5:3b
UI_PORT ?= 8080
UI_DIR ?= web
PYTHON ?= .venv/bin/python

.PHONY: setup run ui clip ollama-up dry-run ruflo-version online-bridge online-tunnel online supabase-status help

help:
	@echo "Targets: setup run ui clip ollama-up dry-run online-bridge online-tunnel"
	@echo "  make setup       Install local deps (no cloud keys)"
	@echo "  make ollama-up   Ensure Ollama model $(MODEL)"
	@echo "  make run         Interactive KYLA"
	@echo "  make ui          Serve static UI on :$(UI_PORT)"
	@echo "  make clip        clip_agent --help"
	@echo "  make dry-run     Sample dry-run routing (expects ruflo default)"
	@echo "  make ruflo-version  npx ruflo@latest --version"
	@echo "  make online-bridge  Start interactive API on :8787"
	@echo "  make online-tunnel  cloudflared tunnel to :8787"
	@echo "  make supabase-status  Supabase backend status + ping (no-op without keys)"

setup:
	bash scripts/setup_local.sh

ollama-up:
	@command -v ollama >/dev/null || (echo "Install Ollama from https://ollama.com"; exit 1)
	@curl -sf http://127.0.0.1:11434/api/tags >/dev/null || (echo "Start: ollama serve"; exit 1)
	ollama pull $(MODEL)
	@echo "OK — export OLLAMA_MODEL=$(MODEL) if needed"

run:
	$(PYTHON) main.py

ui:
	python3 -m http.server $(UI_PORT) --directory $(UI_DIR)

clip:
	$(PYTHON) tools/clip_agent.py --help

dry-run:
	$(PYTHON) main.py --dry-run "plan my week"
	$(PYTHON) main.py --dry-run "clip a youtube short in gula"
	$(PYTHON) main.py --dry-run "summarize my study plan"

ruflo-version:
	npx --yes ruflo@latest --version

online-bridge:
	$(PYTHON) tools/online_bridge.py

online-tunnel:
	@command -v cloudflared >/dev/null || { echo "Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"; exit 1; }
	cloudflared tunnel --url http://127.0.0.1:8787

online:
	@sed -n '1,40p' docs/ONLINE.md

supabase-status:
	python3 tools/supabase_sink.py status
	python3 tools/supabase_sink.py ping
