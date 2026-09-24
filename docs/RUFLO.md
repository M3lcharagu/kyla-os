# Ruflo — KYLA always-on orchestrator

**Policy:** Ruflo is the **intended always-on** agent orchestration path for KYLA.
It is **not optional**. Config sets `runtime.default_agent: ruflo` and R1/R4 suites
default to `ruflo`. Video (R6) stays on `clip` / openmontage.

Upstream: [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (ex Claude-Flow). Melvin may say “ruflow” — same thing. Aliases: `ruflo`, `ruflow`, `claude-flow`, `swarm`, `hive`.

## What Ruflo is

Agent **meta-harness**: swarms, hive-mind, memory, MCP. CLI:

```bash
npx ruflo@latest init                 # non-interactive project init
npx ruflo@latest init wizard          # interactive wizard (Mac-friendly)
npx ruflo@latest --version
npx ruflo@latest hive-mind spawn "…"  # KYLA default path
npx ruflo@latest swarm init --topology hierarchical --max-agents 4
npx ruflo@latest agent spawn -t coder --name kyla-coder
npx ruflo@latest mcp start
```

Requires **Node 20+** (preferred).

## Credits (honest)

| Layer | Cost |
|---|---|
| Ruflo harness (`npx ruflo@latest`) | Free / MIT — no KYLA paid call |
| Claude Code / Anthropic / Codex backends | **Paid** if those CLIs/keys exist and Ruflo routes to them |
| Local Ollama / ruflo-ruvllm bridge | **$0** when configured |

KYLA never injects paid API keys. Prefer local/Ollama when Ruflo supports the provider bridge (`ruflo-ruvllm`). Until then, harness still installs; LLM work can fall through to `stack_agent` → Ollama.

## How KYLA always invokes Ruflo

1. `config.yaml` → `runtime.default_agent: ruflo` (also R1 + R4).
2. `python main.py "…"` routes to agent `ruflo` → `python tools/ruflo_agent.py`.
3. Wrapper **auto-bootstraps** via `npx --yes ruflo@latest` (init once under `$KYLA_STACK_DIR/ruflo`).
4. Default mode: `npx ruflo@latest hive-mind spawn "<prompt>"`.
5. **Only if Node/npx completely missing:** clear error + fall through to `stack_agent` / Ollama.
6. `scripts/bootstrap_stack.sh` always attempts Ruflo init.

```bash
python main.py --dry-run "plan my week"                  # shows AGENT ruflo
python main.py --agent ruflo --execute "plan my week"
python main.py --agent hive --execute "…"                # alias
python main.py --agent swarm --execute "…"               # swarm mode
python main.py --room R6 --execute "clip https://…"      # still clip
```

## Catalina / 2012 MBP notes

Apple’s old system Node (if any) is often **&lt; 20**. Ruflo prefers Node 20+.

```bash
# Install nvm (user-space — works on Catalina)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# restart shell or: source ~/.nvm/nvm.sh
nvm install 20
nvm use 20
node -v   # expect v20.x
```

Then:

```bash
cd ~/kyla-os
git pull origin main
bash scripts/setup_local.sh
export KYLA_STACK_DIR="$HOME/kyla-stack"
export KYLA_CLONE_HEAVY=0
bash scripts/bootstrap_stack.sh
npx ruflo@latest --version
# If init needs a wizard:
npx ruflo@latest init wizard
python main.py --dry-run "swarm a study plan"
```

8GB RAM: do **not** set `KYLA_CLONE_HEAVY=1`. Ruflo via `npx` is fine; skip heavy GPU clones.

## Health Action

`.github/workflows/ruflo-health.yml` runs `npx ruflo@latest --version` on a schedule (no paid keys).

## See also

- `docs/INTEGRATIONS.md` — suite catalog
- `docs/LOCAL_LOW_CREDIT.md` — Ollama / clip $0 path
- `tools/ruflo_agent.py` — wrapper source
