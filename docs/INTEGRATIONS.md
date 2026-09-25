# KYLA operating stack

Integrations are **first-class**. **Ruflo is the always-on orchestrator** (`runtime.default_agent: ruflo`). Rooms invoke a suite. Missing repos **auto-clone** into `$KYLA_STACK_DIR` (default `~/kyla-stack`). LLM preference stays **Ollama** for $0 — no paid APIs required. **No Docker** on Catalina.

See [`docs/RUFLO.md`](RUFLO.md).

## What next on your terminal (2012 MBP / Catalina)

```bash
cd ~/kyla-os
git fetch origin && git checkout main && git pull
bash scripts/setup_local.sh
source .venv/bin/activate
brew install python@3.11 ffmpeg git || true
export PATH="$(brew --prefix python@3.11 2>/dev/null)/bin:$PATH"
export KYLA_STACK_DIR="$HOME/kyla-stack"
export KYLA_CLONE_HEAVY=0
bash scripts/bootstrap_stack.sh
python tools/integrations_cli.py list
python main.py --dry-run "clip a youtube short in gula"
python tools/clip_agent.py --model tiny --dry-run "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

## Default backend: Supabase

`supabase` is registered in `integrations/REGISTRY.yaml` and `STACK.yaml` (`backend: supabase`,
suites command / memory / business). It is a hosted service — nothing is cloned or installed.
Status / ping: `python tools/integrations_cli.py run supabase ping`. Setup: [`supabase/README.md`](../supabase/README.md).

## Suites

| Suite | Rooms | Tools |
|---|---|---|
| command | R1 | **ruflo**, supabase, agency-agents, ollama |
| memory | R2 | ruflo, supabase, prompts, codebase-memory, ollama |
| code | R4 | **ruflo**, agency-agents, gitingest, context7, graft, CLI-Anything, openhands, ollama |
| write | R5 | prompts, mumuainovel, awesome-design-md, ollama |
| video | R6/R7 | clip, openmontage, remotion, voicebox |
| design | R8/R5/R4 | VoltAgent/awesome-design-md |
| study | R10 | build-your-own-x |
| business | R11 | supabase, marketingskills, freedomain |
| research | R12 | context7, gitingest |

Heavy Docker/GPU tools stay lazy. Daily video = `clip_agent --model tiny`.
