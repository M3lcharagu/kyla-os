# KYLA operating stack

Integrations are **first-class**. Rooms invoke a suite. Missing repos **auto-clone** into `$KYLA_STACK_DIR` (default `~/kyla-stack`). LLM stays **Ollama** — no paid APIs. **No Docker** on Catalina.

## What next on your terminal (2012 MBP / Catalina)

```bash
cd ~/kyla-os
git fetch origin && git checkout feat/integrations-catalog
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

## Suites

| Suite | Rooms | Tools |
|---|---|---|
| command | R1 | agency-agents, ollama |
| memory | R2 | prompts, codebase-memory, ollama |
| code | R4 | agency-agents, gitingest, context7, graft, CLI-Anything, openhands, ollama |
| write | R5 | prompts, mumuainovel, awesome-design-md, ollama |
| video | R6/R7 | clip, openmontage, remotion, voicebox |
| design | R8/R5/R4 | VoltAgent/awesome-design-md |
| study | R10 | build-your-own-x |
| business | R11 | marketingskills, freedomain |
| research | R12 | context7, gitingest |

Heavy Docker/GPU tools stay lazy. Daily video = `clip_agent --model tiny`.
