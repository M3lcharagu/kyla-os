# Local low-credit KYLA

Run KYLA on your laptop **without spending OpenAI / Anthropic / Gemini credits**.

## Default: free local path

| Piece | Role | Credits |
|---|---|---|
| `python main.py` room router | Keyword routing only | **None** |
| `--dry-run` | Show room/agent, no execution | **None** |
| `agents.ollama` → `tools/ollama_agent.py` | Local chat via Ollama HTTP | **None** |
| `agents.clip` → `tools/clip_agent.py` | yt-dlp + faster-whisper + ffmpeg | **None** |
| Cloud agents (`claude`, `codex`, …) | `command: null` | **None until you wire them** |

`runtime.dry_run` stays `true` in `config.yaml` until you opt in with `--execute`.

## One-time setup

**Linux / Linux Mint / macOS**

```bash
cd kyla-os
bash scripts/setup_local.sh
source .venv/bin/activate
# install Ollama from https://ollama.com then:
ollama pull qwen2.5:3b   # or: ollama pull phi4-mini
```

**Windows 11 (PowerShell)**

```powershell
cd kyla-os
.\scripts\setup_local.ps1
.\.venv\Scripts\Activate.ps1
ollama pull qwen2.5:3b
```

Models that fit **8 GB RAM** with headroom: `qwen2.5:3b`, `phi4-mini`, `llama3.2:3b`. Avoid 7B+ on 8 GB if you also run a browser + ffmpeg.

## Daily use (zero credits)

```bash
# Routing only — never calls a model
python main.py --dry-run "research laptop options"

# Local chat (Ollama must be running)
python main.py --agent ollama --execute "give me 3 study tips"
# or after runtime.default_agent: ollama
python main.py --execute "give me 3 study tips"

# CapCut-style shorts (local)
python tools/clip_agent.py --dry-run "https://www.youtube.com/watch?v=jNQXAC9IVRw"
python main.py --room R6 --execute "clip https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

Start the local stack (Ollama check + static UI):

```bash
bash scripts/start_local_stack.sh
# or: make ollama-up && make ui
```

## When cloud APIs are optional

Only wire a paid agent if you **explicitly** set `agents.<name>.command` and have a key in your environment. Leave them `null` for daily work. Prefer:

1. Room routing / shell / dry-run (no LLM)
2. Ollama local model
3. Optional LiteLLM cache (`litellm_config.yaml`) in front of Ollama — still free
4. Paid APIs last, for hard tasks you cannot do locally

## Tips to cut tokens further

- Keep prompts short; ask for bullets, not essays.
- Use `--dry-run` while exploring rooms.
- Route video work to R6/`clip` — **no LLM** for highlight scoring (heuristics only).
- Cache with LiteLLM disk cache for repeated prompts.
- Prefer `qwen2.5:3b` / `phi4-mini`; set `OLLAMA_NUM_PREDICT=256` for shorter replies.
- Do not enable WhatsApp / Docker / trading automations until reviewed.

## Env knobs

| Env | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Chat model |
| `OLLAMA_NUM_PREDICT` | `512` | Max generated tokens |
| `KYLA_WHISPER_MODEL` | `base` | faster-whisper size |
| `KYLA_TARGET_CLIPS` | `3` | Shorts per run |

## Makefile shortcuts

```text
make setup      # scripts/setup_local.sh
make run        # interactive KYLA
make ui         # python -m http.server on web/
make clip       # clip_agent --help
make ollama-up  # remind / pull local model
```
